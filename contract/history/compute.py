#!/usr/bin/env python3
"""contract/history — §2.7 이력 계약의 기대값 계산기 (G0).

    python3 contract/history/compute.py            # expected.json 재생성
    python3 contract/history/compute.py --check    # CI

**합성 리포가 필요한 계약**이다(§2.9): 이력 자체가 입력이다. 트리는 커밋되고 git 이력은
이 스크립트가 **결정적으로** 만든다 — 커미터 이름·메일·시각을 고정하므로 커밋 SHA가
언제나 같다. `.git`은 커밋하지 않는다.

**git에 판정을 위임하지 않는다.** 창 걸기·머지 제외·나이·rename tie-break는 §2.7의
규칙을 여기서 직접 구현한다. git의 rename 휴리스틱을 그대로 쓰면 JGit과 다른 숫자가
나올 수 있고(§4.5·D17이 네이티브 백엔드를 옵트인으로 둔 이유가 그것이다), 그러면
픽스처가 계약이 아니라 특정 구현을 고정하게 된다. git에서 읽는 것은 **사실**뿐이다:
커밋 SHA·부모·커미터 시각·변경 경로·추가/삭제 라인.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CASE_DIR.parent / "tools"))
import exact  # noqa: E402

GENERATED_BY = "contract/history/compute.py"
SECONDS_PER_DAY = 86400
K_THRESHOLD = 3  # §2.7·D161 — 팀 집계의 k 하한. 3인 미만 팀은 `other`로 접힌다.

# D162 — off 모드가 내는 저자 유래 필드의 **닫힌 목록**. 이 밖의 저자 유래 필드가 off
# 산출물에 있으면 위반이다. 저자 사실(`author`·`authors`·`author_id`)은 어느 모드에서도
# report에 오지 않는다(D126·D161).
OFF_ALLOWED_AUTHOR_FIELDS = ("distinct_authors_90d", "ownership_max_share", "minor_contributor_share")
TEAM_ONLY_FIELDS = ("team_count", "teams_folded")
NEVER_IN_REPORT = ("author", "authors", "author_id", "teams")


# --------------------------------------------------------------------------
# 합성 리포 — 결정적으로 만든다
# --------------------------------------------------------------------------

def expand_commits(commits: list[dict]) -> list[dict]:
    """`repeat: n`을 n개 커밋으로 편다. 21커밋을 손으로 나열하지 않기 위한 압축 표기.

    id는 `<id>-01..n`, 시각은 `at_seconds + (k-1) * step_seconds`, 내용에는 회차를
    섞어 매번 실제 변경이 되게 한다(같은 내용이면 커밋이 비어 측정이 0이 된다).
    """
    out: list[dict] = []
    for commit in commits:
        n = int(commit.get("repeat", 1))
        step = int(commit.get("step_seconds", 3600))
        for k in range(1, n + 1):
            copy = {key: value for key, value in commit.items()
                    if key not in ("repeat", "step_seconds")}
            # id는 repeat이 1이어도 편다 — 내용 치환이 id를 쓰므로 일관돼야 한다.
            copy["id"] = commit["id"] if n == 1 else f"{commit['id']}-{k:02d}"
            copy["at_seconds"] = int(commit["at_seconds"]) + step * (k - 1)
            copy["message"] = commit["message"] if n == 1 else f"{commit['message']} #{k}"
            # **치환은 repeat과 무관하게 항상 한다.** repeat: 1에서 건너뛰면 서로 다른
            # 명세 항목이 같은 내용을 써서 빈 커밋이 되고, 그 커밋은 파일을 만지지 않은
            # 것으로 세어진다 — chg_commits가 조용히 줄고 저자 하나가 사라진다.
            copy["write"] = {
                path: content.replace("{k}", str(k)).replace("{id}", copy["id"])
                for path, content in commit.get("write", {}).items()}
            out.append(copy)
    return out


def author_of(spec: dict, commit: dict) -> dict:
    """커밋의 저자. 명세가 `authors` 표와 커밋별 `author` id를 준다.

    **고정 가짜 값이다**(`a@example.invalid` 류). 이 값은 `expected.json`에 들어가지
    않는다 — 익명 집계만 기록된다(D135). 픽스처 자신이 D48을 지켜야 한다: 합성
    리포의 저자라도 정체를 산출물에 남기면 그 픽스처는 자기가 검사하는 규칙을 어긴다.
    """
    key = commit.get("author")
    if key is None:
        return spec["committer"]
    return spec["authors"][key]


def build_repo(spec: dict, workdir: Path) -> Path:
    workdir.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "TZ": "UTC",
    }

    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", str(workdir), *args], env=env, check=True,
                              capture_output=True, text=True).stdout.strip()

    git("init", "-q", "-b", "main")
    base = datetime.fromisoformat(spec["base_time"])
    branches: dict[str, str] = {}

    for commit in expand_commits(spec["commits"]):
        when = (base + timedelta(seconds=int(commit["at_seconds"]))).isoformat()
        who = author_of(spec, commit)
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
        env["GIT_AUTHOR_NAME"] = who["name"]
        env["GIT_AUTHOR_EMAIL"] = who["email"]
        env["GIT_COMMITTER_NAME"] = who["name"]
        env["GIT_COMMITTER_EMAIL"] = who["email"]

        if "merge_of" in commit:
            git("checkout", "-q", branches[commit["merge_of"][0]])
            git("merge", "-q", "--no-ff", "-m", commit["message"],
                branches[commit["merge_of"][1]])
        else:
            # 부모를 **명시**한다. 앞 커밋에 이어 붙는다고 가정하면 브랜치를 판 뒤
            # 다음 커밋이 그 브랜치에 쌓여 이력이 조용히 선형이 된다.
            if commit.get("on"):
                git("checkout", "-q", branches[commit["on"]])
            for path, content in commit.get("write", {}).items():
                target = workdir / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                git("add", "--", path)
            for path in commit.get("delete", []):
                git("rm", "-q", "--", path)
            git("commit", "-q", "--allow-empty", "-m", commit["message"])
        branches[commit["id"]] = git("rev-parse", "HEAD")
    return workdir


def shallow_boundary(workdir: Path) -> set[str]:
    """`.git/shallow`에 적힌 graft 경계 커밋. 그 커밋의 diff는 부모가 없어
    **트리 전체가 추가된 것처럼** 보인다 — 거기서 읽은 '마지막 변경'은 사실이 아니다."""
    marker = workdir / ".git" / "shallow"
    if not marker.exists():
        return set()
    return {line.strip() for line in marker.read_text(encoding="utf-8").splitlines()
            if line.strip()}


def read_history(workdir: Path) -> list[dict]:
    """git에서 **사실만** 읽는다. 판정은 하지 않는다."""
    env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null",
           "GIT_CONFIG_SYSTEM": "/dev/null", "TZ": "UTC"}

    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", str(workdir), *args], env=env, check=True,
                              capture_output=True, text=True).stdout

    # §2.7의 창은 "비머지 커밋"이지 first-parent 한정이 아니다. 브랜치에서 만든
    # 커밋도 머지되어 도달 가능하면 세고, 머지 커밋 자체만 뺀다.
    # `%cI`가 아니라 `%ct`(unix 초)를 읽는다. git 버전에 따라 `%cI`가 UTC를
    # `Z`로도 `+00:00`으로도 쓰고, 그러면 "두 머신 바이트 동일"(§2.9)이 깨진다 —
    # CI가 실제로 이것을 잡았다. 커밋 SHA는 플랫폼 사이에 같았고 문자열 포맷만
    # 갈렸다. 여기서 UTC로 정규화한다: §2.1의 `chg_days`도 UTC 날짜 기준이다.
    raw = git("log", "--format=%H%x00%P%x00%ct%x00%s%x00%ae")
    commits = []
    for line in raw.strip().splitlines():
        sha, parents, epoch, subject, author_email = line.split("\x00")
        when = datetime.fromtimestamp(int(epoch), timezone.utc).isoformat()
        parent_list = parents.split() if parents else []
        # 머지 커밋은 어차피 창에서 빠지므로 numstat을 읽지 않는다.
        stat = "" if len(parent_list) >= 2 else git("show", "--numstat", "--format=", sha)
        paths, added, deleted = [], 0, 0
        for row in stat.strip().splitlines():
            parts = row.split("\t")
            if len(parts) != 3:
                continue
            a, d, path = parts
            paths.append(path)
            added += 0 if a == "-" else int(a)
            deleted += 0 if d == "-" else int(d)
        commits.append({
            # §2.7 — 저자는 **읽되 정체는 프로세스 밖으로 내지 않는다.** 여기서만
            # 쓰이고 expected.json에 들어가지 않는다. 익명 집계의 입력일 뿐이다.
            "_author_key": hashlib.sha256(author_email.encode()).hexdigest(),
            "sha": sha, "parents": parent_list, "committer_time": when,
            "subject": subject, "paths": sorted(set(paths)),
            "added": added, "deleted": deleted,
            "is_merge": len(parent_list) >= 2,
        })
    return commits


# --------------------------------------------------------------------------
# §2.7 규칙 — 여기서 직접 판정한다
# --------------------------------------------------------------------------

def levenshtein(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1,
                               previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def resolve_rename(old_path: str, candidates: list[dict]) -> dict:
    """§2.7 tie-break: 유사도 → 경로 편집 거리 → 사전순. 동률은 `rename_ambiguous`.

    유사도는 케이스가 선언한다 — JGit의 유사도 지표를 여기서 흉내 내면 픽스처가
    계약이 아니라 그 구현을 고정한다. 케이스는 유사도가 **설계상 명백한** 모양
    (내용 동일 = 100)으로 만들어 이 문제를 피한다.

    `rename_ambiguous`의 읽기: 앞의 두 기준(유사도·편집 거리)이 동률이면 표기한다.
    사전순은 전순서라 승자는 언제나 하나지만, **사전순이 결정했다는 사실 자체가
    신호**다 — §2.7이 동률을 기록하라는 것은 그 뜻으로 읽었다.
    """
    ranked = sorted(
        candidates,
        key=lambda c: (-int(c["similarity"]), levenshtein(old_path, c["path"]), c["path"]))
    best = ranked[0]
    top_key = (int(best["similarity"]), levenshtein(old_path, best["path"]))
    tied = [c for c in ranked
            if (int(c["similarity"]), levenshtein(old_path, c["path"])) == top_key]
    return {
        "from": old_path,
        "to": best["path"],
        "similarity": int(best["similarity"]),
        "path_edit_distance": levenshtein(old_path, best["path"]),
        "candidates": [
            {"path": c["path"], "similarity": int(c["similarity"]),
             "path_edit_distance": levenshtein(old_path, c["path"])}
            for c in ranked
        ],
        "decided_by": "lexicographic" if len(tied) > 1 else (
            "similarity" if len({int(c["similarity"]) for c in candidates}) > 1
            else "path_edit_distance"),
        "rename_ambiguous": len(tied) > 1,
    }


def shallow_clone(source: Path, depth: int, target: Path) -> Path:
    """§2.1 — shallow clone에서는 조상이 없어 마지막 변경 커밋을 못 찾는 파일이 생긴다."""
    env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null",
           "GIT_CONFIG_SYSTEM": "/dev/null", "TZ": "UTC"}
    subprocess.run(["git", "clone", "-q", "--depth", str(depth), "--no-local",
                    f"file://{source}", str(target)],
                   env=env, check=True, capture_output=True, text=True)
    return target


def days_display(days: Fraction):
    """D184·D155-1 — 경과 시간(일)의 인쇄는 2자리 HALF_EVEN, 후행 0 유지(`90.00`). 값 자체는 유리수다."""
    from decimal import Decimal
    return exact.round_half_even(Decimal(days.numerator) / Decimal(days.denominator), 2)


def build_expected(inp: dict, workdir: Path) -> dict:
    spec = inp["repo"]
    build_repo(spec, workdir)
    scanned = workdir
    if inp.get("shallow_depth"):
        scanned = shallow_clone(workdir, int(inp["shallow_depth"]),
                                workdir.parent / "shallow")
    # D189 — 미커밋 신규 파일: 작업트리에만 있고 어느 커밋에도 없다. 명세가 주면 스캔 대상 트리에 쓴다.
    for rel, content in inp.get("uncommitted_files", {}).items():
        target = scanned / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    commits = read_history(scanned)
    boundary = shallow_boundary(scanned)
    for c in commits:
        c["is_shallow_boundary"] = c["sha"] in boundary
    head = commits[0]

    # §2.7 앵커 — HEAD 커밋의 **커미터 시각**. scanned_at이 아니다(D25).
    head_time = datetime.fromisoformat(head["committer_time"])
    window = inp["window"]
    months, max_commits = int(window["months"]), int(window["max_commits"])
    earliest = head_time - timedelta(days=round(months * 30.4375))

    # 머지 커밋(부모 ≥ 2) 제외 후 최신순. 두 상한 중 **먼저 닥치는 쪽**을 적용한다.
    non_merge = [c for c in commits if not c["is_merge"]]
    in_time = [c for c in non_merge
               if datetime.fromisoformat(c["committer_time"]) >= earliest]
    bound_hit = "none"
    if len(in_time) < len(non_merge):
        bound_hit = "time"
    selected = in_time
    if len(selected) > max_commits:
        selected = selected[:max_commits]
        bound_hit = "count" if bound_hit == "none" else "time+count"

    # §2.7 거칠기 — median(files per commit) > 20 이면 coarse.
    counts = sorted(len(c["paths"]) for c in selected)
    if counts:
        mid = len(counts) // 2
        median_files = (Fraction(counts[mid]) if len(counts) % 2
                        else Fraction(counts[mid - 1] + counts[mid], 2))
    else:
        median_files = None
    granularity = "coarse" if (median_files is not None and median_files > 20) else "fine"

    renames = [resolve_rename(r["from"], r["candidates"])
               for r in inp.get("renames", [])]
    rename_map = {r["from"]: r["to"] for r in renames}

    # 파일별 측정(§2.1). rename 매핑을 적용해 옛 경로의 활동을 새 경로로 접는다.
    def canonical(path: str) -> str:
        seen = set()
        while path in rename_map and path not in seen:
            seen.add(path)
            path = rename_map[path]
        return path

    files: dict[str, dict] = {}
    for path in inp["measure_files"]:
        touching = [c for c in selected
                    if any(canonical(p) == path for p in c["paths"])]
        days = {c["committer_time"][:10] for c in touching}
        entry = {
            "chg_commits": len(touching),
            "chg_days": len(days),
            "churn": sum(c["added"] + c["deleted"] for c in touching),
            "touched_by": [c["sha"][:9] for c in touching],
        }
        if touching and touching[0]["is_shallow_boundary"]:
            # §2.1 — shallow clone의 graft 경계에서는 조상이 잘려 그 커밋이 파일을
            # 실제로 바꿨는지 알 수 없다. 트리 전체가 추가로 보이기 때문이다.
            entry["age_last_days"] = None
            entry["age_reason"] = "age_unknown"
            entry["age_basis"] = "shallow_boundary_commit"
        elif touching:
            last = datetime.fromisoformat(touching[0]["committer_time"])
            delta = (head_time - last).total_seconds()
            if delta < 0:
                # §2.1 — 음수 나이는 잘못된 메타데이터·시계다. 0이 아니라 null.
                entry["age_last_days"] = None
                entry["age_reason"] = "invalid_metadata"
            else:
                # D184 — '일' = 초/86400의 정확 유리수. 비교(≥ 180·> P90)는 이 값으로, 인쇄는 2자리(D155-1 경과 시간 행).
                exact_days = Fraction(int(delta), SECONDS_PER_DAY)
                entry["age_last_days"] = days_display(exact_days)
                if inp.get("age_boundary"):
                    # §3.3의 지시변수 둘째 항을 **정확값**으로 — 179일 23시간은 ≥ 180이 아니다.
                    entry["age_at_least_180_exact"] = exact_days >= 180
        elif (not boundary and (scanned / path).exists()
              and not any(canonical(p) == path for c in commits for p in c["paths"])):
            # §2.1·D189 — **미커밋 신규 파일**: 작업트리에는 있는데 마지막 커밋이 없다. 이름은
            # `uncommitted`이지 `age_unknown`이 아니다 — 사유마다 구제가 다르다(커밋하라 / shallow를
            # 풀라 / 도구의 한계). `age_unknown`으로 접으면 `history_complete`가 shallow만 설명하고
            # 이 null은 다시 이름 없는 null이 된다. 이름은 §2.5 사전(D188)에서 온다.
            entry["age_last_days"] = None
            entry["age_reason"] = "uncommitted"
            entry["age_basis"] = "no_commit"
        else:
            # §2.1 — 결정 불가(shallow clone·rename 조상 복구 실패)면 null.
            # "오래되지 않았다"와 "나이를 모른다"는 다른 상태다(D37). F도 null이 된다(§3.3).
            entry["age_last_days"] = None
            entry["age_reason"] = inp.get("age_unknown_reason", "age_unknown")
        files[path] = entry

    # ------------------------------------------------------------------
    # §2.4 파일 쌍 — shared·tc·보고 임계 (D134)
    # ------------------------------------------------------------------
    # 그래프는 이 계약의 입력이 아니다. `static_dependency`는 명세가 준다 —
    # §2.4가 "정적 의존 없으면 숨은 결합"이라 말할 때 그 판정의 **입력**이고,
    # 그것을 계산하는 것은 §2.2의 일이다.
    static_dependency = {tuple(sorted(k.split("|"))): v
                         for k, v in inp.get("static_dependency", {}).items()}
    # D176·D190 — 그래프 밖 **파일**의 이유를 명세가 준다: `outside_bytecode_scope`(범위 밖 — 테스트
    # 소스 세트) 또는 `no_bytecode`(적격이지만 클래스 없음). 쌍의 `reason`은 여기서 **계산**한다 —
    # 쌍에 직접 적게 하면 동률 규칙이 계산이 아니라 입력이 된다.
    graph_absent = inp.get("class_graph_absent", {})
    for path, why in graph_absent.items():
        if why not in ("outside_bytecode_scope", "no_bytecode"):
            raise ValueError(f"class_graph_absent[{path}]: §2.5 사전의 쌍 자리 이름이 아니다 — {why}")
    pairs = []
    measured = list(files)
    for i, a in enumerate(measured):
        for b in measured[i + 1:]:
            lo, hi = sorted((a, b))
            commits_a = {c["sha"] for c in selected
                         if any(canonical(p) == lo for p in c["paths"])}
            commits_b = {c["sha"] for c in selected
                         if any(canonical(p) == hi for p in c["paths"])}
            shared = len(commits_a & commits_b)
            if not shared:
                continue
            denominator = min(len(commits_a), len(commits_b))
            tc = Fraction(shared, denominator) if denominator else None
            # §2.4 보고 기준: shared >= 5 AND tc >= 0.5. 임계 비교는 반올림 전
            # 정확값으로 한다(§2.5 산술 계약) — 직렬화된 tc로 비교하면 경계가 흔들린다.
            reported = bool(shared >= 5 and tc is not None and tc >= Fraction(1, 2))
            # D176 — 명세가 명시적으로 `null`을 주면 그래프 밖 파일(테스트 소스 세트)이 든 쌍이다:
            # 정적 의존을 **판정하지 않는다**(`reason: outside_bytecode_scope`), `hidden_coupling`도 판정 없음.
            # 명세에 아예 없는 쌍(옛 케이스)은 그대로 None/False — 기존 expected를 움직이지 않는다.
            sd = static_dependency.get((lo, hi), "unspecified")
            absent = [graph_absent[f] for f in (lo, hi) if f in graph_absent]
            if sd is None and not absent:
                raise ValueError(f"({lo}, {hi}): 명세가 null을 줬는데 그래프 밖 파일이 없다 — class_graph_absent에 적어라(D190)")
            if isinstance(sd, bool) and absent:
                # D176이 막은 오류 그 자체 — 그래프 밖 파일이 든 쌍을 false/true로 계산하면 가장
                # 노골적인 정적 의존이 숨은 결합으로 인쇄된다.
                raise ValueError(f"({lo}, {hi}): 그래프 밖 파일이 들었는데 static_dependency가 {sd}다(D176·D190)")
            entry = {
                "a": lo, "b": hi,
                "shared": shared,
                "chg_commits_a": len(commits_a), "chg_commits_b": len(commits_b),
                "denominator": denominator,
                "tc": tc,
                "reported": reported,
                "static_dependency": None if sd == "unspecified" else sd,
                # §3.5 — 정적 의존이 없는 쌍이 숨은 결합이다. 판정이 아니라 목록이며
                # 테스트-대상 쌍은 긍정 해석을 병기한다.
                "hidden_coupling": (None if sd is None else (reported and sd is False)),
                "commit_granularity": granularity,
            }
            if sd is None:
                # D190 **동률 규칙** — 두 파일이 모두 밖이고 사유가 다르면 `outside_bytecode_scope`가
                # 앞선다: 범위 결정이 클래스 유무보다 앞선다. 한쪽만 밖이면 그 파일의 이유.
                entry["reason"] = ("outside_bytecode_scope" if "outside_bytecode_scope" in absent
                                   else "no_bytecode")
                entry["graph_absent"] = {f: graph_absent[f] for f in (lo, hi) if f in graph_absent}
            pairs.append(entry)

    # §2.7·§5.5·D174 — 창 W(측정: 비머지, 브랜치 포함)와 first-parent(전이의 후보: main에
    # 닿은 순서)는 **다른 집합, 다른 질문**이다. 케이스가 요구하면 두 집합을 나란히 인쇄해
    # 다름을 값으로 남긴다 — 후보 쪽의 전이 계산은 `ledger/`(G2b)의 일이고 여기서는 집합만.
    first_parent_view = None
    if inp.get("compare_first_parent"):
        by_sha = {c["sha"]: c for c in commits}
        chain, cur = [], head["sha"]
        while cur in by_sha:
            chain.append(by_sha[cur])
            cur = by_sha[cur]["parents"][0] if by_sha[cur]["parents"] else None
        w_set = [c["sha"][:9] for c in selected]
        fp_set = [c["sha"][:9] for c in chain]
        first_parent_view = {
            "window_commits": w_set,
            "first_parent_commits": fp_set,
            "in_window_not_first_parent": [x for x in w_set if x not in fp_set],
            "first_parent_not_in_window": [x for x in fp_set if x not in w_set],
            "sets_differ": set(w_set) != set(fp_set),
        }

    # §3.5·D167 — `hidden_couplings`는 §7에서 배열이라 순서가 바이트다(D154). 정렬 키 =
    # static_dependency asc(false 먼저) · tc desc · shared desc · a asc · b asc, 비교는
    # 반올림 전 정확값(Fraction). 정렬은 인쇄되는 키이지 점수가 아니다(B.2).
    hidden_couplings = sorted(
        ({"a": p["a"], "b": p["b"], "shared": p["shared"], "tc": p["tc"],
          "static_dependency": p["static_dependency"], "hidden_coupling": p["hidden_coupling"],
          **({"reason": p["reason"]} if "reason" in p else {})}
         for p in pairs if p["reported"]),
        # D176 — false · true · null: 모르는 것은 숨은 결합의 증거가 아니라 앞에 올 수 없다.
        key=lambda p: (p["static_dependency"] is not False, p["static_dependency"] is None,
                       -p["tc"], -p["shared"], p["a"], p["b"]))

    # §2.4·D164 — 분자(shared)와 분모(chg_commits)가 같은 구간(W 안)이라 tc ≤ 1이 불변식이다.
    # 이 계산기는 둘 다 `selected`에서 세므로 구조적으로 성립한다 — 케이스가 요구하면 인쇄한다.
    invariants = None
    if "tc_at_most_one" in inp.get("invariants", []):
        invariants = {"tc_at_most_one": all(
            p["tc"] is not None and p["tc"] <= 1 for p in pairs)}

    # ------------------------------------------------------------------
    # §2.1 저자 사실 — 익명 집계만 (D48·D135)
    # ------------------------------------------------------------------
    ninety_days_ago = head_time - timedelta(days=90)
    # 창이 실제로 덮는 일수. `min(90, HEAD_TIME − 창의 가장 오래된 커밋 시각)`.
    # 음수로 내려가지 않게 0에서 자른다 — 커미터 시각이 뒤죽박죽이면(§2.1
    # `invalid_metadata`) HEAD가 자기 조상보다 이를 수 있고, 그때 '음수 일수'는
    # 아무 뜻이 없다. 창이 비면 0 — 아무것도 덮지 못했다.
    if selected:
        oldest = datetime.fromisoformat(selected[-1]["committer_time"])
        span = Fraction(int((head_time - oldest).total_seconds()), SECONDS_PER_DAY)
        authors_window_days = days_display(min(Fraction(90), max(Fraction(0), span)))
    else:
        authors_window_days = days_display(Fraction(0))

    # **절단은 "창이 90일보다 짧다"가 아니라 "상한이 90일 구간을 잘랐다"다.**
    # 10일 된 리포의 `distinct_authors_90d`는 90일을 못 봤지만 **볼 것이 없었다** —
    # 그것을 truncated로 표기하면 "데이터를 잃었다"로 읽힌다. 판정은 존재로 한다:
    # 최근 90일 안에 있는 비머지 커밋 중 **창이 제외한 것이 있는가.**
    #
    # 따라서 시간 상한(12개월)은 90일 구간을 자를 수 없다 — 90일 ⊂ 12개월이다.
    # 자를 수 있는 것은 개수 상한뿐이다.
    selected_shas = {c["sha"] for c in selected}
    excluded_within_90d = [
        c for c in commits
        if not c["is_merge"] and c["sha"] not in selected_shas
        and datetime.fromisoformat(c["committer_time"]) >= ninety_days_ago]
    authors_window_truncated = bool(excluded_within_90d)
    for path, entry in files.items():
        touching = [c for c in selected
                    if any(canonical(p) == path for p in c["paths"])]
        # `distinct_authors_90d`는 §2.1이 "최근 90일"이라 적고 **W 안이라 말하지 않는다** —
        # 나머지 둘은 "(W 안)"을 명시한다. 계약이 둘을 구별하므로 여기서도 구별한다.
        # D137 — 90일 지표는 `[HEAD_TIME − 90d, HEAD_TIME] ∩ W`에서 계산한다.
        # `commits`(전체)를 돌면 창 밖 커밋이 값을 움직여 **같은 analysis_input_id가
        # 다른 값을 낸다** — `analysis_input_id`의 입력은 창 안 커밋 SHA 목록이므로
        # D87("포함되지 않은 입력은 결과에 영향을 주어서는 안 된다")이 막는 자리다.
        # 창을 넓히지 않는다: 넓히면 그 커밋들이 id에 들어가야 한다.
        recent = [c for c in selected
                  if datetime.fromisoformat(c["committer_time"]) >= ninety_days_ago
                  and any(canonical(p) == path for p in c["paths"])]
        entry["distinct_authors_90d"] = len({c["_author_key"] for c in recent})

        counts: dict[str, int] = {}
        for c in touching:
            counts[c["_author_key"]] = counts.get(c["_author_key"], 0) + 1
        total = sum(counts.values())
        if total:
            entry["contributor_count"] = len(counts)
            entry["ownership_max_share"] = Fraction(max(counts.values()), total)
            # §2.1 — 비중이 **5% 미만**인 기여자들의 합. 5%는 미만이 아니다.
            minor = sum(n for n in counts.values() if Fraction(n, total) < Fraction(1, 20))
            entry["minor_contributor_share"] = Fraction(minor, total)
            entry["contribution_shares_sorted"] = sorted(
                (Fraction(n, total) for n in counts.values()), reverse=True)
        else:
            entry["contributor_count"] = 0
            entry["ownership_max_share"] = None
            entry["minor_contributor_share"] = None

    # ------------------------------------------------------------------
    # §2.1 팀 집계 — k 하한은 여기에만 건다 (D161·D162)
    # ------------------------------------------------------------------
    # `off`에서는 이 블록이 돌지 않고 `team_count`·`teams_folded`는 **필드 부재**다(D162).
    # 매핑은 명세의 저자 id → 팀. 3인 미만 팀은 `other`로 접고, 접힌 팀의 수를
    # `teams_folded`(파일 단위)와 `folded_from`(`other` 항목)에 남긴다 — 값은 있고
    # 라벨은 없다. 팀 라벨은 합성 리포의 가짜 값이라 expected에 남아도 정체가 아니다.
    people = inp.get("people")
    if people and people.get("attribution") in ("team", "individual"):
        mapping = people["team_mapping"]
        key_of = {hashlib.sha256(spec["authors"][a]["email"].encode()).hexdigest(): team
                  for team, members in mapping.items() for a in members}
        small = {team for team, members in mapping.items() if len(members) < K_THRESHOLD}
        for path, entry in files.items():
            touching = [c for c in selected
                        if any(canonical(p) == path for p in c["paths"])]
            per_team: dict[str, int] = {}
            folded: set[str] = set()
            for c in touching:
                team = key_of[c["_author_key"]]  # 매핑 밖 저자는 이 픽스처가 만들지 않는다
                if team in small:
                    folded.add(team)
                    team = "other"
                per_team[team] = per_team.get(team, 0) + 1
            teams = [{"team": t, "commits": n} for t, n in sorted(per_team.items())]
            for t in teams:
                if t["team"] == "other":
                    t["folded_from"] = len(folded)
            entry["teams"] = teams
            entry["team_count"] = len(per_team)
            entry["teams_folded"] = len(folded)

    return {
        "case": inp["case"],
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "shallow_depth": inp.get("shallow_depth"),
        "window_anchor": {"type": "head_committer_time", "timestamp": head["committer_time"]},
        "head": head["sha"][:9],
        "window_applied": {
            "months": months, "max_commits": max_commits, "bound_hit": bound_hit,
            "commits_in_window": len(selected),
            "merge_commits_excluded": sum(1 for c in commits if c["is_merge"]),
            # D137 — 90일 지표가 실제로 본 일수. 이름이 `90d`인데 1.6일을 본 경우를
            # 아는 자리다. **창의 속성이므로 여기 한 번만 적고 파일마다 적지 않는다**:
            # 파일별 표기는 "이 파일이 잘린 구간에 커밋을 가졌나"를 아는 것처럼
            # 읽히는데, 그 커밋들이 창에서 사라져 판정하는 것이므로 알 수 없다.
            "authors_window_truncated": authors_window_truncated,
            "authors_window_days": authors_window_days,
            "commits_excluded_within_90d": len(excluded_within_90d),
        },
        "commits": [
            {"sha": c["sha"][:9], "at": c["committer_time"], "subject": c["subject"],
             "is_merge": c["is_merge"], "shallow_boundary": c["is_shallow_boundary"],
             "paths": c["paths"],
             "in_window": any(s["sha"] == c["sha"] for s in selected)}
            for c in commits
        ],
        "median_files_per_commit": median_files,
        "commit_granularity": granularity,
        "renames": renames,
        "files": files,
        "pairs": pairs,
        # 쌍이 있는 케이스만 인쇄한다 — 빈 배열을 열넷에 더하는 것은 계약이 아니라 잡음이다.
        **({"hidden_couplings": hidden_couplings} if pairs else {}),
        **({"invariants": invariants} if invariants is not None else {}),
        **({"first_parent_view": first_parent_view} if first_parent_view is not None else {}),
        "authorship_note": ("저자 정체는 이 파일에 없다 — 익명 집계만 기록한다"
                            "(§2.7·D48·D135). 합성 리포의 저자는 고정 가짜 값이고 "
                            "계산기는 그것을 메모리에서만 쓴다."),
    }


# 대소문자를 무시하고 **부분 문자열**로 본다. `git blame`처럼 띄어쓰기를 가정하면
# `new ProcessBuilder("git", "blame", "-p")`가 빠져나간다 — bite_check가 그것을 잡았다.
# scan/change 경로에서는 blame이라는 말 자체가 신호다. "여기서는 blame을 부르지
# 않는다" 같은 주석도 걸리는데, 그 주석은 여기 말고 계약 문서에 쓰는 것이 맞다.
# 검사에서 빼는 자리. **좁게** 둔다 — 넓게 빼면 검사가 공집합을 훑고 그 "통과"는
# "검사하지 않았다"와 구별되지 않는다.
#   ledger/     §5.6의 유일한 예외 — 캠페인 생성 시 1회, 원장 finding 영역 한정(D57)
#   violations/ 자체 ArchUnit 규칙의 반례. 일부러 어기는 것이 존재 이유다
# 테스트 소스 전체를 빼지 않는다: 스캐너가 주석과 리터럴을 가르므로 계약을 인용하는
# 테스트 코드는 어차피 걸리지 않고, scan/change를 부르는 테스트는 걸려야 한다.
BLAME_SANCTIONED = ("io/jqradar/ledger/", "io/jqradar/arch/violations/")


def split_java(source: str) -> tuple[str, list[str]]:
    """Java 소스를 (주석 뺀 코드, 문자열 리터럴 목록)으로 가른다.

    **이 함수가 이 케이스의 핵심이다.** 주석과 문자열 리터럴을 같이 다루면 규칙이
    둘 중 하나로 망가진다:

    - 둘 다 보면 "매 스캔 blame 금지(D18)" 같은 **계약을 인용하는 주석**이 걸린다.
      이 리포의 코드 스타일이 정확히 그것이라(JqradarArchRules.java도 compute.py도
      계약 인용 주석으로 가득하다) 규칙이 G1에 "계약을 설명하는 주석 금지"가 된다.
    - 둘 다 안 보면 `new ProcessBuilder("git", "blame", "-p")`를 놓친다 — 타입
      의존이 없어 자체 ArchUnit 규칙 2도 못 잡는 경로다.

    그래서 **주석은 버리고 문자열 리터럴은 남긴다.** `contract/judgment-vocabulary.json`이
    `not_judgment` 절과 단어 경계로 오탐을 다루는 것과 같은 규율이다.

    코드 쪽에서는 리터럴을 `""`로 지워 토큰만 남긴다 — 그래야 `.blame(`이 주석이나
    문자열이 아니라 **호출**일 때만 걸린다.
    """
    out, literals = [], []
    i, n = 0, len(source)
    while i < n:
        two = source[i:i + 2]
        if two == "//":
            while i < n and source[i] != "\n":
                i += 1
            continue
        if two == "/*":
            end = source.find("*/", i + 2)
            i = n if end < 0 else end + 2
            continue
        if source[i:i + 3] == '"""':                      # 텍스트 블록(Java 15+)
            end = source.find('"""', i + 3)
            literals.append(source[i + 3:end] if end >= 0 else source[i + 3:])
            out.append('""')
            i = n if end < 0 else end + 3
            continue
        if source[i] in '"\'':
            quote, j, buf = source[i], i + 1, []
            while j < n and source[j] != quote:
                if source[j] == "\\":
                    buf.append(source[j:j + 2])
                    j += 2
                    continue
                buf.append(source[j])
                j += 1
            literals.append("".join(buf))
            out.append('""')
            i = j + 1
            continue
        out.append(source[i])
        i += 1
    return "".join(out), literals


# 코드 토큰 마커 — **주석을 뺀 코드**에서만 찾는다.
CODE_MARKERS = ("BlameCommand", ".blame(")

# 문자열 리터럴 마커 — ProcessBuilder로 부르는 네이티브 blame 경로.
#
# 리터럴이면 다 증거는 아니다. `@DisplayName("어기면 잡는다 — git.blame()")` 같은
# **산문**이 실제로 걸렸다(이 리포에 있는 문장이다). 그래서 리터럴이 **명령 조각**
# 모양일 때만 증거로 센다: 공백으로 쪼갠 토큰이 전부 CLI 모양이고, 그중 하나가
# 정확히 `blame`일 때. ProcessBuilder 인자는 정확한 토큰이고 산문은 아니다.
CLI_TOKEN = re.compile(r"^[A-Za-z0-9._/=-]+$")


def is_command_fragment_with_blame(literal: str) -> bool:
    tokens = literal.split()
    if not tokens or not all(CLI_TOKEN.match(t) for t in tokens):
        return False
    return any(t.lower() == "blame" for t in tokens)

# 단독으로는 **증거가 아니다.** `git status --porcelain`·`git push --porcelain`이
# 흔하다. blame 리터럴과 **연접**할 때만 증거로 센다.
LITERAL_CORROBORATING = "--porcelain"


def scan_source(source: str) -> list[dict]:
    """한 소스에서 찾은 증거 목록. 비면 통과다."""
    code, literals = split_java(source)
    found = []
    for marker in CODE_MARKERS:
        if marker in code:
            found.append({"kind": "code_token", "marker": marker})
    blame_literals = [lit for lit in literals if is_command_fragment_with_blame(lit)]
    for lit in blame_literals:
        found.append({"kind": "string_literal", "marker": lit})
    if blame_literals and any(LITERAL_CORROBORATING in lit for lit in literals):
        found.append({"kind": "corroborating_literal", "marker": LITERAL_CORROBORATING})
    return found


def check_no_blame(inp: dict) -> dict:
    """D113 — `scan`·`change` 경로에 blame이 없다. **값이 아니라 부재를 본다.**

    같은 선을 자체 ArchUnit 규칙 2가 바이트코드 수준에서 지킨다(CLAUDE.md §3.5).
    이 케이스는 소스 수준이라 주석·문자열·셸 호출(`git blame --porcelain`)까지 본다 —
    ArchUnit은 타입 의존만 보므로 `ProcessBuilder`로 부르는 blame을 놓친다.
    강제 장치가 대상 코드보다 앞선다: G0에는 scan/change 코드가 없고, 생기는 순간부터 돈다.
    """
    root = CASE_DIR.parent.parent
    seen, scanned, skipped, hits = [], [], [], []
    for path in sorted(root.glob("jqradar-*/src/**/*.java")):
        rel = path.relative_to(root).as_posix()
        seen.append(rel)
        if any(marker in rel for marker in BLAME_SANCTIONED):
            skipped.append(rel)
            continue
        scanned.append(rel)
        for evidence in scan_source(path.read_text(encoding="utf-8")):
            hits.append({"path": rel, **evidence})

    # **검사가 무는지 확인한다.** G0에는 scan/change 코드가 없어 위 루프가 공집합을
    # 훑는다 — 그 상태의 "통과"는 "검사하지 않았다"와 구별되지 않는다(D124와 같은 논리).
    # 아래 조각들은 각각 반드시 걸려야 한다.
    bite = []
    for sample in inp["must_be_caught"]:
        evidence = scan_source(sample["source"])
        bite.append({"name": sample["name"], "why": sample["why"],
                     "evidence": evidence, "caught": bool(evidence)})
    missed = [b["name"] for b in bite if not b["caught"]]

    # **오탐 검사.** schema/에는 긍정과 변조가 둘 다 있는데 여기엔 변조만 있었다.
    # 이 셋이 걸리면 규칙이 G1에 "계약을 설명하는 주석 금지"가 된다.
    false_positives = []
    for sample in inp["must_not_be_caught"]:
        evidence = scan_source(sample["source"])
        false_positives.append({"name": sample["name"], "why": sample["why"],
                                "evidence": evidence, "passed": not evidence})
    wrongly_caught = [f["name"] for f in false_positives if not f["passed"]]

    return {
        "case": inp["case"],
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "check": "no_blame_on_scan_change_path",
        "sanctioned_prefixes": list(BLAME_SANCTIONED),
        "markers": {
            "code_tokens": list(CODE_MARKERS),
            "string_literal": "명령 조각 모양의 리터럴에서 토큰이 정확히 `blame`일 때만 "
                              "(산문은 증거가 아니다)",
            "corroborating_literal": LITERAL_CORROBORATING
                                     + " — blame 리터럴과 연접할 때만",
        },
        "comment_handling": "주석은 스캔 전에 제거한다. 문자열 리터럴은 남긴다.",
        # 부재 검사가 증명하는 것은 "훑은 파일 중 blame 호출이 0건"이지 "훑은 파일이 이 열 개"가 아니다.
        # 목록을 기록하면 소스가 늘 때마다 expected가 움직인다(2026-10-06 — 반례 다섯째 종). 수만 남긴다;
        # 어느 파일인지는 `sanctioned_prefixes`와 리포 트리가 말한다.
        "files_seen": len(seen),
        "files_scanned": len(scanned),
        "files_skipped_as_sanctioned": len(skipped),
        "violations": hits,
        "bite_check": bite,
        "false_positive_check": false_positives,
        "verdict": "reject" if (hits or missed or wrongly_caught) else "accept",
        "note": ("G0에는 scan/change 코드가 없어 실제 스캔 대상이 0일 수 있다. "
                 "그래서 bite_check가 함께 있다 — 검사가 무는지는 공집합이 아니라 "
                 "반례가 증명한다."),
    }


def identity_hashes(identifiers: list[str]) -> dict[str, list[str]]:
    """알고 있는 저자 식별자의 해시들. **모양이 아니라 출처로 가른다**(D135).

    산출물에는 `sha256:`이 정당하게 가득하다 — `repository_state_id`·
    `analysis_input_id`·`validated_tree_id`·`token_hash`·`policy_hash`. 저자 해시와
    이것들을 **문자열 모양으로 가를 방법은 없다**: 둘 다 64 hex다.

    합성 리포의 저자 식별자는 우리가 정했으므로 그 값들의 해시를 미리 계산할 수 있다.
    그러면 무해한 해시를 무해하다고 증명할 필요 없이 **유해한 해시가 없음**을
    증명하면 된다. 접두도 함께 본다 — 12자만 실어도 재식별에 충분하다.
    """
    out: dict[str, list[str]] = {}
    for value in identifiers:
        raw = value.encode()
        digests = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "sha1": hashlib.sha1(raw).hexdigest(),
            "md5": hashlib.md5(raw).hexdigest(),
        }
        forbidden = []
        for algorithm, digest in digests.items():
            forbidden.append(digest)
            forbidden.extend(digest[:n] for n in (8, 12, 16))
        out[value] = forbidden
    return out


def scan_for_identity(document: str, forbidden: dict[str, list[str]]) -> list[dict]:
    """산출물 텍스트에서 금지된 문자열을 찾는다. 원문 그대로 본다 — `double`이나
    파서를 거치지 않는다(정체는 값이 아니라 바이트로 샌다)."""
    lowered = document.lower()
    found = []
    for identifier, hashes in forbidden.items():
        for digest in hashes:
            if digest.lower() in lowered:
                found.append({"derived_from": "<저자 식별자 — 기록하지 않는다>",
                              "matched_prefix_length": len(digest)})
                break
    return found


def check_identity_absence(inp: dict) -> dict:
    """§2.1·D48·D135 — `attribution=off`에서 정체가 산출물에 없다.

    **부재 검사이므로 `must_be_caught`와 `must_not_be_caught`를 함께 둔다**(D131).
    """
    identifiers = [a["email"] for a in inp["authors"].values()]
    identifiers += [a["name"] for a in inp["authors"].values()]
    forbidden = identity_hashes(identifiers)

    caught = []
    for sample in inp["must_be_caught"]:
        hits = scan_for_identity(json.dumps(sample["document"], ensure_ascii=False), forbidden)
        caught.append({"name": sample["name"], "why": sample["why"],
                       "hits": len(hits), "caught": bool(hits)})
    passed = []
    for sample in inp["must_not_be_caught"]:
        hits = scan_for_identity(json.dumps(sample["document"], ensure_ascii=False), forbidden)
        passed.append({"name": sample["name"], "why": sample["why"],
                       "hits": len(hits), "passed": not hits})

    # D195 — "산출물 어디에도"는 **`build/jqradar/`의 캐시 디렉터리까지**다. 캐시 키는 저장되는 값이라
    # 저자 집합을 키에 두면 "해시도 저장하지 않는다"(§2.7, D48)가 캐시에서 깨진다. 명세의 캐시 항목을 임시
    # `build/jqradar/`에 실제 파일로 쓰고 디렉터리를 통째로 훑는다 — 저자 해시는 `{"$author_hash": "<id>"}`
    # 자리표시자로 적고 여기서만 계산한다(금지 문자열을 입력 파일에도 두지 않는다).
    cache_check = None
    if inp.get("cache_directory"):
        emails = {k: a["email"] for k, a in inp["authors"].items()}

        def materialize(node):
            if isinstance(node, dict):
                if set(node) == {"$author_hash"}:
                    return hashlib.sha256(emails[node["$author_hash"]].encode()).hexdigest()
                return {k: materialize(v) for k, v in node.items()}
            if isinstance(node, list):
                return [materialize(v) for v in node]
            return node

        def scan_dir(sample: dict) -> int:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "build" / "jqradar"
                for rel, content in sample["files"].items():
                    target = root / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(json.dumps(materialize(content), ensure_ascii=False), encoding="utf-8")
                blob = "\n".join(f.read_text(encoding="utf-8") for f in sorted(root.rglob("*")) if f.is_file())
            return len(scan_for_identity(blob, forbidden))

        c_caught = [{"name": x["name"], "why": x["why"], "files": len(x["files"]), "caught": scan_dir(x) > 0}
                    for x in inp["cache_directory"]["must_be_caught"]]
        c_passed = [{"name": x["name"], "why": x["why"], "files": len(x["files"]), "passed": scan_dir(x) == 0}
                    for x in inp["cache_directory"]["must_not_be_caught"]]
        cache_check = {"scanned_root": "build/jqradar/", "bite_check": c_caught, "false_positive_check": c_passed}
        caught = caught + [{"name": "cache:" + c["name"], "caught": c["caught"]} for c in c_caught]
        passed = passed + [{"name": "cache:" + c["name"], "passed": c["passed"]} for c in c_passed]

    missed = [c["name"] for c in caught if not c["caught"]]
    wrong = [f["name"] for f in passed if not f["passed"]]
    return {
        "case": inp["case"],
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "check": "identity_absence",
        **({"cache_directory": cache_check} if cache_check else {}),
        "method": "provenance — 알고 있는 저자 식별자의 해시(sha256·sha1·md5 × 전체·접두 8·12·16자)가 "
                  "산출물에 없음을 본다. 모양으로 가르지 않는다(둘 다 64 hex).",
        "forbidden_string_count": sum(len(v) for v in forbidden.values()),
        "identifiers_recorded": False,
        "bite_check": caught,
        "false_positive_check": passed,
        "verdict": "reject" if (missed or wrong) else "accept",
        "note": "금지 문자열 자체도 이 파일에 적지 않는다 — 적으면 그것이 정체의 사본이다. "
                "개수와 판정만 기록한다(D48).",
    }


def _keys_with_paths(node, prefix=""):
    if isinstance(node, dict):
        for k, v in node.items():
            path = f"{prefix}/{k}"
            yield path, k, v
            yield from _keys_with_paths(v, path)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _keys_with_paths(v, f"{prefix}/{i}")


def closed_list_violations(document: dict) -> list[str]:
    """§2.7·D162 — off 산출물에 닫힌 목록 셋 밖의 저자 유래 필드가 없다. D126·D161 —
    저자 사실은 어느 모드에서도 report에 없다. 위반한 경로를 돌려준다."""
    attribution = document.get("reproduce", {}).get("people", {}).get("attribution")
    out = []
    for path, key, value in _keys_with_paths(document):
        if key in NEVER_IN_REPORT:
            out.append(path)
        elif attribution == "off" and key in TEAM_ONLY_FIELDS:
            out.append(path)
        elif attribution == "off" and key == "people_artifact" and value is not None:
            out.append(path)
    return out


def check_closed_list_absence(inp: dict) -> dict:
    """부재 검사이므로 `must_be_caught`와 `must_not_be_caught`를 함께 둔다(D131)."""
    caught, passed = [], []
    for sample in inp["must_be_caught"]:
        hits = closed_list_violations(sample["document"])
        caught.append({"name": sample["name"], "why": sample["why"], "hits": hits, "caught": bool(hits)})
    for sample in inp["must_not_be_caught"]:
        hits = closed_list_violations(sample["document"])
        passed.append({"name": sample["name"], "why": sample["why"], "hits": hits, "passed": not hits})
    missed = [c["name"] for c in caught if not c["caught"]]
    wrong = [f["name"] for f in passed if not f["passed"]]
    return {
        "case": inp["case"],
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "check": "closed_list_absence",
        "off_allowed_author_fields": list(OFF_ALLOWED_AUTHOR_FIELDS),
        "team_only_fields": list(TEAM_ONLY_FIELDS),
        "never_in_report": list(NEVER_IN_REPORT),
        "bite_check": caught,
        "false_positive_check": passed,
        "verdict": "reject" if (missed or wrong) else "accept",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="§2.7 이력 계약")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("cases", nargs="*")
    args = ap.parse_args()

    dirs = sorted(p.parent for p in CASE_DIR.glob("*/input.json"))
    if args.cases:
        dirs = [p for p in dirs if p.name in set(args.cases)]

    failures = 0
    for case_dir in dirs:
        inp = json.loads((case_dir / "input.json").read_text(encoding="utf-8"))
        if inp.get("check") == "no_blame_on_scan_change_path":
            expected = check_no_blame(inp)
        elif inp.get("check") == "identity_absence":
            expected = check_identity_absence(inp)
        elif inp.get("check") == "closed_list_absence":
            expected = check_closed_list_absence(inp)
        elif "variants" in inp:
            # 같은 작업을 두 이력으로 만들어 값을 나란히 둔다(§2.4 스쿼시 대조, D134).
            expected = {"case": inp["case"], "contract_refs": inp["contract_refs"],
                        "what_this_pins": inp["what_this_pins"], "variants": {}}
            for name, repo in inp["variants"].items():
                one = dict(inp)
                one.pop("variants")
                one["repo"] = repo
                # 변이마다 창을 달리 줄 수 있다 — 같은 이력을 두 창으로 보는 케이스가
                # 필요하기 때문이다(D137의 절단은 창이 만든다).
                if "window_per_variant" in inp:
                    one["window"] = inp["window_per_variant"][name]
                tmp = tempfile.mkdtemp()
                try:
                    built = build_expected(one, Path(tmp) / "repo")
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)
                for key in ("case", "contract_refs", "what_this_pins", "shallow_depth"):
                    built.pop(key, None)
                expected["variants"][name] = built
        else:
            # git이 백그라운드 프로세스를 남길 수 있어 정리가 경쟁한다(CI에서
            # Errno 39로 터졌다). 정리 실패로 픽스처가 깨지면 안 되므로 직접 지운다.
            # `ignore_cleanup_errors`는 Python 3.10+라 쓰지 않는다.
            tmp = tempfile.mkdtemp()
            try:
                expected = build_expected(inp, Path(tmp) / "repo")
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
        text = exact.finish(expected, GENERATED_BY)
        target = case_dir / "expected.json"
        if args.check:
            current = target.read_text(encoding="utf-8") if target.exists() else None
            if current == text:
                print(f"ok    {case_dir.name}")
            else:
                failures += 1
                print(f"FAIL  {case_dir.name}: expected.json "
                      f"{'없음' if current is None else '다름'} — §2.7 이력 계약")
                if current is not None:
                    # 무엇이 다른지 말하지 않는 실패는 CI에서 쓸모가 없다.
                    import difflib
                    diff = list(difflib.unified_diff(
                        current.splitlines(), text.splitlines(),
                        fromfile="committed", tofile="recomputed", lineterm="", n=1))
                    for line in diff[:40]:
                        print(f"      {line}")
                    if len(diff) > 40:
                        print(f"      … 그리고 {len(diff) - 40}줄 더")
        else:
            target.write_text(text, encoding="utf-8")
            print(f"wrote {case_dir.name}/expected.json")

    if failures:
        print(f"\n{failures}개 실패. 의도한 변경이면 fixture_change를 같은 커밋에(§2.9·D129).")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
