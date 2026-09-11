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
import json
import os
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


# --------------------------------------------------------------------------
# 합성 리포 — 결정적으로 만든다
# --------------------------------------------------------------------------

def build_repo(spec: dict, workdir: Path) -> Path:
    workdir.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": spec["committer"]["name"],
        "GIT_AUTHOR_EMAIL": spec["committer"]["email"],
        "GIT_COMMITTER_NAME": spec["committer"]["name"],
        "GIT_COMMITTER_EMAIL": spec["committer"]["email"],
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

    for commit in spec["commits"]:
        when = (base + timedelta(seconds=int(commit["at_seconds"]))).isoformat()
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when

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
    raw = git("log", "--format=%H%x00%P%x00%ct%x00%s")
    commits = []
    for line in raw.strip().splitlines():
        sha, parents, epoch, subject = line.split("\x00")
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


def build_expected(inp: dict, workdir: Path) -> dict:
    spec = inp["repo"]
    build_repo(spec, workdir)
    scanned = workdir
    if inp.get("shallow_depth"):
        scanned = shallow_clone(workdir, int(inp["shallow_depth"]),
                                workdir.parent / "shallow")
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
                entry["age_last_days"] = Fraction(int(delta), SECONDS_PER_DAY)
        else:
            # §2.1 — 결정 불가(shallow clone·미커밋 신규·rename 조상 복구 실패)면 null.
            # "오래되지 않았다"와 "나이를 모른다"는 다른 상태다(D37). F도 null이 된다(§3.3).
            entry["age_last_days"] = None
            entry["age_reason"] = inp.get("age_unknown_reason", "age_unknown")
        files[path] = entry

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
    }


# 대소문자를 무시하고 **부분 문자열**로 본다. `git blame`처럼 띄어쓰기를 가정하면
# `new ProcessBuilder("git", "blame", "-p")`가 빠져나간다 — bite_check가 그것을 잡았다.
# scan/change 경로에서는 blame이라는 말 자체가 신호다. "여기서는 blame을 부르지
# 않는다" 같은 주석도 걸리는데, 그 주석은 여기 말고 계약 문서에 쓰는 것이 맞다.
SCAN_CHANGE_MARKERS = ("blamecommand", ".blame(", "blame", "--porcelain")

# §5.6의 유일한 예외 — 캠페인 생성 시 1회, 원장 finding 영역 한정.
BLAME_SANCTIONED = ("io/jqradar/ledger/", "contract/", "docs/", "/test/")


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
        text = path.read_text(encoding="utf-8").lower()
        for marker in SCAN_CHANGE_MARKERS:
            if marker in text:
                hits.append({"path": rel, "marker": marker})

    # **검사가 무는지 확인한다.** G0에는 scan/change 코드가 없어 위 루프가 공집합을
    # 훑는다 — 그 상태의 "통과"는 "검사하지 않았다"와 구별되지 않는다(D124와 같은 논리).
    # 아래 조각들은 각각 반드시 걸려야 한다.
    bite = []
    for sample in inp["must_be_caught"]:
        lowered = sample["source"].lower()
        caught = [m for m in SCAN_CHANGE_MARKERS if m in lowered]
        bite.append({"name": sample["name"], "why": sample["why"],
                     "matched_markers": caught, "caught": bool(caught)})
    missed = [b["name"] for b in bite if not b["caught"]]

    return {
        "case": inp["case"],
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "check": "no_blame_on_scan_change_path",
        "sanctioned_prefixes": list(BLAME_SANCTIONED),
        "markers": list(SCAN_CHANGE_MARKERS),
        "files_seen": len(seen),
        "files_scanned": len(scanned),
        "files_skipped_as_sanctioned": skipped,
        "scanned_paths": scanned,
        "violations": hits,
        "bite_check": bite,
        "verdict": "reject" if (hits or missed) else "accept",
        "note": ("G0에는 scan/change 코드가 없어 실제 스캔 대상이 0일 수 있다. "
                 "그래서 bite_check가 함께 있다 — 검사가 무는지는 공집합이 아니라 "
                 "반례가 증명한다."),
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
