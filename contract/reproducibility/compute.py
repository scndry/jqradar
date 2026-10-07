#!/usr/bin/env python3
"""contract/reproducibility — §2.8 재현성 정체성 셋의 기대값 계산기 (G0).

이 계약은 **합성 리포**를 먹는다(§2.9): 트리는 커밋되고 git 이력은 스크립트가
결정적으로 만든다(커미터 이름·메일·시각 고정 → 커밋 SHA 고정). `analysis_input_id`의
입력에 창 안 커밋 SHA 목록과 `window_anchor`가 들어가므로(§2.8) 트리만으로는
전제가 닫히지 않는다 — 그래서 순수 수치 계약이 아니다.

    python3 contract/reproducibility/compute.py            # expected.json 재생성
    python3 contract/reproducibility/compute.py --check     # CI

**산술·해시는 정확값으로.** 부동소수점을 쓰지 않는다(D115).

**정규 인코딩은 RFC 8785 JCS**(§2.8, D138). `contract/tools/jcs.py`.
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
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parent
PRD = CASE_DIR.parent.parent / "prd.md"
sys.path.insert(0, str(CASE_DIR.parent / "tools"))
import historywalk  # noqa: E402  — §4.5 걷기는 history/와 같은 구현(D205: 두 구현이 같은 shallow에서 같은 id)
import jcs  # noqa: E402

GENERATED_BY = "contract/reproducibility/compute.py"

# §2.8 — `analysis_input_id`의 **정규 인코딩은 RFC 8785 JCS**(D138). 해시는 바이트에
# 대한 것이므로 입력을 바이트로 펴는 방법이 계약이다. 이전 판은 여기서
# "sorted-key compact UTF-8 JSON"을 자리표시자로 **선언하고** 썼다(계약에 없었다).
# 두 인코딩은 지금 입력 영역(ASCII 키·정수·문자열)에서 바이트 동일하고,
# `jcs-canonical-encoding` 케이스가 그것을 증명한다 — 그래서 기존 두 케이스의
# 해시는 움직이지 않고 선언 문자열만 바뀐다.
CANONICAL_ENCODING = "RFC8785-JCS"


def canonical(obj) -> bytes:
    return jcs.encode(obj)


def sha256(obj) -> str:
    return "sha256:" + hashlib.sha256(canonical(obj)).hexdigest()


def content_id(data: bytes) -> str:
    """§2.8 파일 내용 ID — 추적/미추적 무관 git blob 공식."""
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def tree_files(root: Path) -> list[tuple[str, str]]:
    out = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        out.append((path.relative_to(root).as_posix(), content_id(path.read_bytes())))
    return out


def repository_state_id(files: list[tuple[str, str]]) -> str:
    """§2.8 — 정렬된 `(path, content_id)` 전체의 sha256."""
    return sha256([[p, c] for p, c in files])


def canonical_time(unix_seconds: int) -> str:
    """§2.7 시각의 정규 표기(D157) — UTC · RFC 3339 · 초 · `Z` · 소수 초 없음, unix 초에서.

    `%cI`가 아니라 `%ct`(unix 초). git 버전에 따라 UTC를 `Z`로도 `+00:00`으로도
    써서 두 머신에서 문자열이 갈리고, 이 값은 `analysis_input_id`에 **해시로
    들어간다** — 그러면 같은 트리·같은 툴체인인데 id가 달라진다(PR #4에서 CI가
    잡았다). `%ct`로 바꾼 뒤에도 파이썬 `isoformat()`이 `+00:00`을 냈다 — 표기가
    계약이 아니어서 계산기가 제 사정대로 적은 것이다. v3.9.0이 표기를 정했다.
    JCS는 문자열 안을 건드리지 않으므로 여기서 한 형식으로 만들어야 한다.
    """
    return datetime.fromtimestamp(unix_seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_history(tree: Path, spec: dict, workdir: Path) -> dict:
    """합성 git 이력을 결정적으로 만든다 — 같은 스크립트는 언제나 같은 SHA를 낸다."""
    shutil.copytree(tree, workdir, dirs_exist_ok=True)
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": spec["committer"]["name"],
        "GIT_AUTHOR_EMAIL": spec["committer"]["email"],
        "GIT_COMMITTER_NAME": spec["committer"]["name"],
        "GIT_COMMITTER_EMAIL": spec["committer"]["email"],
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
    }

    def git(*args, **kw):
        return subprocess.run(["git", "-C", str(workdir), *args], env=env,
                              check=True, capture_output=True, text=True, **kw).stdout.strip()

    git("init", "-q", "-b", "main")
    base = datetime.fromisoformat(spec["base_time"])
    shas = []
    for i, commit in enumerate(spec["history"]):
        when = (base + timedelta(seconds=int(commit["at_seconds"]) if "at_seconds" in commit
                                 else spec["step_seconds"] * i)).isoformat()
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
        # 같은 경로를 다시 커밋하려면 내용이 바뀌어야 한다 — `write`가 그 경로의 내용을 준다(트리의 파일은 첫 커밋용).
        for rel, content in commit.get("write", {}).items():
            (workdir / rel).parent.mkdir(parents=True, exist_ok=True)
            (workdir / rel).write_text(content, encoding="utf-8")
        for rel in commit["paths"]:
            git("add", "--", rel)
        git("commit", "-q", "-m", commit["message"])
        shas.append(git("rev-parse", "HEAD"))
    # 도달 불가 커밋 — main에서 도달할 수 없는 브랜치. §2.7의 창은 HEAD에서 도달
    # 가능한 비머지 커밋이므로 이것들은 창 밖이고, `analysis_input_id`의 입력도
    # 아니다. 값이든 id든 여기에 영향을 받으면 D87이 깨진다.
    unreachable = []
    for k, commit in enumerate(spec.get("unreachable", []), start=1):
        when = (base + timedelta(seconds=int(commit["at_seconds"]))).isoformat()
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
        env["GIT_AUTHOR_NAME"] = commit.get("name", spec["committer"]["name"])
        env["GIT_AUTHOR_EMAIL"] = commit.get("email", spec["committer"]["email"])
        env["GIT_COMMITTER_NAME"] = env["GIT_AUTHOR_NAME"]
        env["GIT_COMMITTER_EMAIL"] = env["GIT_AUTHOR_EMAIL"]
        git("checkout", "-q", "-b", f"abandoned-{k}")
        for path, content in commit["write"].items():
            (workdir / path).parent.mkdir(parents=True, exist_ok=True)
            (workdir / path).write_text(content, encoding="utf-8")
            git("add", "--", path)
        git("commit", "-q", "-m", commit["message"])
        unreachable.append(git("rev-parse", "HEAD"))
        git("checkout", "-q", "main")
        # 작업트리를 main 상태로 되돌린다 — 도달 불가 커밋이 트리를 오염시키면
        # `repository_state_id`가 달라져 케이스가 무의미해진다.
        git("clean", "-qfd")

    facts = history_facts(workdir, [p for p, _ in tree_files(workdir) if not p.startswith(".git/")],
                          spec.get("parameters", {"window.months": 12, "window.max_commits": 2000}))
    return {**facts, "unreachable_commit_count": len(unreachable)}


def git_commits(workdir: Path) -> list[dict]:
    """HEAD에서 도달 가능한 커밋 — 관측된 부모·커미터 시각·바꾼 경로. graft 경계는 `.git/shallow`로 안다(D148)."""
    env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null", "TZ": "UTC"}
    def git(*args):
        return subprocess.run(["git", "-C", str(workdir), *args], env=env, check=True, capture_output=True, text=True).stdout
    boundary = set()
    marker = workdir / ".git" / "shallow"
    if marker.exists():
        boundary = {l.strip() for l in marker.read_text().splitlines() if l.strip()}
    out = []
    for line in git("log", "--format=%H%x00%P%x00%ct").strip().splitlines():
        sha, parents, ct = line.split("\x00")
        plist = parents.split() if parents else []
        paths = [] if len(plist) >= 2 else [l for l in git("show", "--name-only", "--format=", sha).splitlines() if l]
        out.append({"sha": sha, "parents": plist, "committer_time": int(ct), "is_merge": len(plist) >= 2,
                    "paths": sorted(set(paths)), "is_boundary": sha in boundary})
    return out


def history_facts(workdir: Path, files: list[str], parameters: dict) -> dict:
    """§2.7·§4.5·D203–D205 — 창 안 커밋 목록, HEAD 시각, **파일별 마지막 비머지 커밋 맵**(걷기 포함), 완전성.
    맵의 값: 정하지 못한 셋은 null, 음수 나이(invalid_metadata)는 그 SHA — 맵은 마지막 커밋의 맵이지 나이의 맵이 아니다(D205)."""
    commits = git_commits(workdir)
    by_sha = {c["sha"]: c for c in commits}
    head = commits[0]
    months, max_commits = int(parameters["window.months"]), int(parameters["window.max_commits"])
    earliest = head["committer_time"] - round(months * 30.4375) * 86400
    non_merge = [c for c in commits if not c["is_merge"]]
    selected = [c for c in non_merge if c["committer_time"] >= earliest][:max_commits]
    oldest = selected[-1]["committer_time"] if selected else head["committer_time"]
    in_window = {c["sha"] for c in selected} | {c["sha"] for c in commits if c["is_merge"] and c["committer_time"] >= oldest}
    start = historywalk.frontier(by_sha, in_window)
    last_map, boundary_hit = {}, set()
    for path in sorted(files):
        touching = [c for c in selected if path in c["paths"]]
        if touching and touching[0]["is_boundary"]:
            last_map[path] = None; boundary_hit.add(touching[0]["sha"]); continue
        if touching:
            last_map[path] = touching[0]["sha"]; continue
        w = historywalk.last_touch(by_sha, start, path)
        if w["sha"] is not None:
            last_map[path] = w["sha"]
        else:
            last_map[path] = None
            if w["touched_boundary"]:
                boundary_hit |= {c["sha"] for c in commits if c["is_boundary"]}
    return {"commit_shas": [c["sha"] for c in reversed(selected)], "head": head["sha"],
            "head_committer_time": canonical_time(head["committer_time"]),
            "last_commit_map": last_map, "history_complete": not boundary_hit,
            "graft_boundary_shas": sorted(boundary_hit)}


DEFAULT_PEOPLE = {"attribution": "off", "team_mapping_sha256": None}
# §2.5·§2.8 — `percentile_method`는 [id]다. 이 스펙은 v3.10.0 전까지 그것을 **빠뜨리고 있었다**
# (3차 T8과 같은 자리 — reproduce 세 종류에 자리 없는 값). D182가 `output`의 키를 바꾸면서
# 넣었고, 그래서 기존 케이스 전부의 id가 움직였다(fixture_change 2026-10-06).
PERCENTILE_METHOD = {
    "rank": "average", "formula": "(rank_avg-1)/(N-1)", "quantile": "type7-linear",
    "arithmetic": "exact-rational",
    "output": {"irrational": "BigDecimal MathContext(34, HALF_EVEN)", "rounding": "HALF_EVEN", "scales": "D155-1"},
}
K_THRESHOLD = 3  # §2.7·D161 — 팀 집계의 k 하한. 익명 집계에는 걸지 않는다(D162).
# §2.8 (i)·§7 — `bytecode_scope`의 **범위 정의**는 [id]다. 이 스펙은 v3.10.2까지 그것을 **빠뜨리고 있었다**
# (`percentile_method`와 같은 종류의 구멍 — 계약 목록에 있는데 계산기에 없던 입력). D194가 전이 사영에
# `bytecode_scope`를 넣으면서 "사영 ⊆ §2.8 스펙" 검사가 그것을 드러냈다. 기존 케이스 전부의 id가 움직인다.
# `external_edges`는 [fn]이라 범위 정의가 아니다.
DEFAULT_BYTECODE_SCOPE = {"class_roots": ["build/classes/java/main", "build/classes/kotlin/main"],
                          "test_classes_included": False, "generated_excluded": True,
                          "external_included_in_metrics": False}
BYTECODE_SCOPE_ID_FIELDS = tuple(DEFAULT_BYTECODE_SCOPE)


def team_mapping_sha256(text: str | None) -> str | None:
    """조직 제공 팀 매핑 파일의 해시(D160). 파일 하나의 해시라 정체가 아니다."""
    if text is None:
        return None
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def analysis_input_id(shared: dict, environment: dict, files: list[tuple[str, str]],
                      history: dict) -> tuple[str, dict]:
    """§2.8 — 툴체인·계약·입력 전부. 여기 없는 입력은 결과에 영향을 주면 안 된다(D87)."""
    spec = {
        "schema_version": shared["schema_version"],
        "contract_version": shared["contract_version"],
        "core_tool_version": shared["core_tool_version"],
        "environment": environment,
        "history_backend": shared["history_backend"],
        "component": shared["component"],
        "algorithm_versions": shared["algorithm_versions"],
        "source_files": [[p, c] for p, c in files],
        "class_files": [],
        "window_anchor": {"type": "head_committer_time",
                          "timestamp": history["head_committer_time"]},
        "commit_list_sha256": hashlib.sha256(
            canonical(history["commit_shas"])).hexdigest(),
        # D146·D205 — 파일별 마지막 비머지 커밋 맵의 해시. v3.10.5까지 이 스펙은 그것을 **빠뜨리고 있었다**(§2.8 (i)에 있는
        # 이름 — `percentile_method`·`bytecode_scope`와 같은 종류, §0-45). `reproduce`에서 재계산할 때는 인쇄된 해시를 그대로 쓴다.
        "last_commit_map_sha256": history.get("last_commit_map_sha256") or hashlib.sha256(
            canonical(history["last_commit_map"])).hexdigest(),
        "parameters": shared["parameters"],
        # D160 — 저작 정책은 산출물을 바꾸므로 id 입력이다. off에서도 들어간다(모드가
        # 무엇이었나도 재현의 일부). `parameters`와 별도인 이유는 B.6 — 조직이 적는 자리가 다르다.
        "people": shared.get("people", DEFAULT_PEOPLE),
        "percentile_method": PERCENTILE_METHOD,
        # D186 — 세 종류에 자리 없던 값들이 (i)로: 정규 인코딩, 분할 기준, history_backend 전체.
        # 창 파라미터(`window.months`·`window.max_commits`)는 `parameters` 안에 있다(입력이 그렇게 준다).
        "canonical_encoding": CANONICAL_ENCODING,
        "bytecode_scope": {k: shared.get("bytecode_scope", DEFAULT_BYTECODE_SCOPE)[k]
                           for k in BYTECODE_SCOPE_ID_FIELDS},
    }
    assert "window.months" in spec["parameters"], "D186 — 창 파라미터는 parameters에 있어야 한다"
    assert "split_share_basis" in spec["component"], "D186 — component.split_share_basis는 id 입력이다"
    return sha256(spec), spec


def id_from_reproduce(reproduce: dict, files: list[tuple[str, str]], history: dict) -> str:
    """§2.8·D111 — **§7 모양의 `reproduce` 블록**과 리포(트리·head)만으로 id를 다시 만든다.

    reproduce에 값으로 있는 것은 값을 쓰고, 해시로만 있는 것(소스 파일 목록·창 안 커밋 목록)은 §2.8대로
    리포에서 재생성한다. 세 종류 어디에도 자리가 없는 값이 생기면 이 함수가 그것을 읽을 수 없어 id가
    갈린다 — 3차 T8이 그런 값을 넷 찾았고 D186이 자리를 정했다. 그래서 이 케이스가 먼저 드러낸다."""
    shared = {
        "schema_version": reproduce["schema_version"],
        "contract_version": reproduce["contract_version"],
        "core_tool_version": reproduce["tool_version"],
        "history_backend": reproduce["history_backend"],
        "component": {k: reproduce["component"][k] for k in ("strategy", "split_share_basis")}
                     | {"algorithm_version": reproduce["algorithm_versions"]["component_strategy"]},
        "algorithm_versions": {k: v for k, v in reproduce["algorithm_versions"].items() if k != "component_strategy"},
        "parameters": reproduce["parameters"],
        "people": reproduce["people"],
        # §7의 `bytecode_scope`는 [id](범위 정의)와 [fn](`external_edges`)이 섞여 있다 — 범위 정의만 읽는다.
        "bytecode_scope": {k: reproduce["bytecode_scope"][k] for k in BYTECODE_SCOPE_ID_FIELDS},
    }
    history = {**history, "last_commit_map_sha256": reproduce["window_applied"]["last_commit_map_sha256"]}
    aid, _ = analysis_input_id(shared, reproduce["environment"], files, history)
    return aid


def run_repo_variants(case_dir: Path, inp: dict) -> dict:
    """창 밖(도달 불가) 커밋만 다른 두 리포 — **id와 값이 함께 같아야 한다**.

    `max_commits`로 잘린 커밋으로는 이 쌍을 만들 수 없다: 커밋 SHA가 조상을 물고
    가므로 창 밖이 달라지면 창 안 SHA도 달라지고, 그러면 `commit_list_sha256`이
    달라져 `analysis_input_id`가 구조적으로 갈린다(실험으로 확인했다). 도달 불가
    커밋은 HEAD의 조상이 아니므로 HEAD SHA가 동일하고, 그래서 **원칙의 양면(id의
    동일성과 값의 독립성)이 한 케이스에서 닫힌다.**

    잡는 실패: 구현이 `git log --all`이나 `--branches`로 이력을 읽는 것. 그러면
    도달 불가 커밋이 창에 섞여 값이 갈리는데 id는 같다 — 재현성 주장이 조용히 샌다.
    """
    results = {}
    for name, repo in inp["repo_variants"].items():
        tree = case_dir / repo["tree"]
        files = tree_files(tree)
        with tempfile.TemporaryDirectory() as tmp:
            history = build_history(tree, repo, Path(tmp) / "repo")
        aid, _ = analysis_input_id(inp["shared_inputs"],
                                   inp["runs"]["a"]["environment"], files, history)
        results[name] = {
            "unreachable_commit_count": history["unreachable_commit_count"],
            "reachable_commit_count": len(history["commit_shas"]),
            "head": history["head"],
            "head_committer_time": history["head_committer_time"],
            "repository_state_id": repository_state_id(files),
            "analysis_input_id": aid,
        }
    names = list(results)
    a, b = results[names[0]], results[names[1]]
    return {
        "case": inp["case"],
        "generated_by": GENERATED_BY,
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "canonical_encoding": CANONICAL_ENCODING,
        "variants": results,
        "assertions": {
            "head_sha_equal": a["head"] == b["head"],
            "repository_state_id_equal":
                a["repository_state_id"] == b["repository_state_id"],
            "analysis_input_id_equal": a["analysis_input_id"] == b["analysis_input_id"],
            "reachable_commit_count_equal":
                a["reachable_commit_count"] == b["reachable_commit_count"],
            "unreachable_counts_differ":
                a["unreachable_commit_count"] != b["unreachable_commit_count"],
        },
    }


def naive_sorted_key(obj) -> bytes:
    """이전 판이 쓰던 인코딩. **계약이 아니다** — JCS와 갈리는지 보려고만 둔다."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def run_canonical_vectors(inp: dict) -> dict:
    """§2.8·D138 — 정규 인코딩이 RFC 8785 JCS라는 것을 벡터로 못 박는다.

    일치만 보이는 검사는 아무것도 증명하지 않으므로(D131) 세 가지를 같이 본다:
    RFC 벡터를 **재현하는가**, 순진한 sorted-key 인코딩이 그 벡터에서 **갈리는가**,
    그리고 id 입력 영역에서는 둘이 **바이트 동일한가**(기존 해시가 안 움직이는 근거).
    """
    spec = inp["canonical_vectors"]
    vectors, assertions = [], {}

    for vec in spec["rfc_vectors"]:
        parsed = json.loads(vec["input_json"])
        produced = jcs.dumps(parsed)
        naive = naive_sorted_key(parsed).decode("utf-8")
        entry = {"name": vec["name"], "source": vec["source"],
                 "jcs": produced, "naive_sorted_key": naive,
                 "naive_diverges": produced != naive}
        if "expected_property_order" in vec:
            entry["property_order"] = list(json.loads(produced).values())
            entry["reproduces_rfc"] = \
                entry["property_order"] == vec["expected_property_order"]
            entry["naive_property_order"] = list(json.loads(naive).values())
            entry["naive_reproduces_rfc"] = \
                entry["naive_property_order"] == vec["expected_property_order"]
        else:
            entry["reproduces_rfc"] = produced == vec["expected_canonical"]
        vectors.append(entry)
        assertions[f"rfc_{vec['name'].replace('-', '_')}_reproduced"] = entry["reproduces_rfc"]

    sorting = next(v for v in vectors if v["name"] == "property-sorting")
    # 검사가 무는 것을 보인다: 순진한 인코딩은 이 벡터에서 RFC와 다르다.
    assertions["naive_sorted_key_diverges_on_rfc_vector"] = sorting["naive_diverges"]
    assertions["naive_sorted_key_fails_rfc_vector"] = not sorting["naive_reproduces_rfc"]

    # id 입력 영역(§2.8): ASCII 키·정수·문자열. 여기서는 둘이 바이트 동일하다.
    sample = spec["id_input_domain_sample"]
    jcs_bytes, naive_bytes = jcs.encode(sample), naive_sorted_key(sample)
    domain = {
        "jcs_sha256": "sha256:" + hashlib.sha256(jcs_bytes).hexdigest(),
        "naive_sha256": "sha256:" + hashlib.sha256(naive_bytes).hexdigest(),
        "bytes_identical": jcs_bytes == naive_bytes,
        "byte_length": len(jcs_bytes),
    }
    assertions["id_input_domain_bytes_identical"] = domain["bytes_identical"]

    rejected = []
    for case in spec["rejected_inputs"]:
        parsed = json.loads(case["input_json"])
        try:
            jcs.dumps(parsed)
            caught, detail = False, "통과해 버렸다"
        except jcs.FloatInCanonicalInput as exc:
            caught, detail = True, str(exc)
        rejected.append({"name": case["name"], "why": case["why"],
                         "rejected": caught, "detail": detail})
        assertions[f"rejects_{case['name'].replace('-', '_')}"] = caught

    return {
        "case": inp["case"],
        "generated_by": GENERATED_BY,
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "canonical_encoding": CANONICAL_ENCODING,
        "rfc_vectors": vectors,
        "id_input_domain": domain,
        "rejected_inputs": rejected,
        "assertions": assertions,
    }


D157_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


def _keys_recursive(obj, prefix=""):
    """중첩 객체의 모든 키 경로. 제외 필드가 id 입력에 없음을 보이는 데 쓴다(D154)."""
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            out.add(k)
            out |= _keys_recursive(v, path)
    elif isinstance(obj, list):
        for v in obj:
            out |= _keys_recursive(v, prefix)
    return out


def _delete_path(obj: dict, dotted: str) -> None:
    node = obj
    parts = dotted.split(".")
    for part in parts[:-1]:
        node = node[part]
    del node[parts[-1]]


def comparison_target(report: dict, excluded: list[str]) -> dict:
    """D154 — "두 머신 바이트 동일"의 비교 대상 = 산출물에서 제외 목록을 뺀 전부."""
    target = json.loads(json.dumps(report))
    for field in excluded:
        _delete_path(target, field)
    return target


def run_byte_identity(case_dir: Path, inp: dict) -> dict:
    """§2.8·D154 — 비교 대상의 정의를 네 단언으로 못 박는다(케이스 `what_this_pins` 참조)."""
    tree = case_dir / inp["repo"]["tree"]
    files = tree_files(tree)
    with tempfile.TemporaryDirectory() as tmp:
        history = build_history(tree, inp["repo"], Path(tmp) / "repo")
    shared, env = inp["shared_inputs"], inp["environment"]
    aid, spec = analysis_input_id(shared, env, files, history)
    rsid = repository_state_id(files)
    excluded = inp["excluded_fields"]

    def report_for(machine: dict, file_order: list | None = None, sort_arrays: bool = True) -> dict:
        # G0에는 측정 코드가 없다 — 산출물은 reproduce 블록과 그 결정적 함수들로 이뤄진
        # 최소 리포트다. 필드는 세 종류뿐(D158): [id] · [fn] · [x].
        # D202 — 배열은 순서가 바이트라 삽입 순서가 아니라 표 D202-1의 키(`files: path asc`)로 정렬해 인쇄한다.
        # 비교는 코드 포인트 순 = UTF-8 바이트 순(§2.8 — 경로는 git 트리 바이트, 정규화 없음).
        printed = list(file_order if file_order is not None else files)
        if sort_arrays:
            printed = sorted(printed, key=lambda pc: pc[0])
        return {
            "schema": shared["schema_version"],
            "reproduce": {
                "tool_version": shared["core_tool_version"],                      # [id]
                "schema_version": shared["schema_version"],                       # [id]
                "contract_version": shared["contract_version"],                   # [id]
                "scanned_at": canonical_time(machine["scanned_at_unix"]),         # [x]
                "algorithm_versions": shared["algorithm_versions"],               # [id]
                "window_anchor": spec["window_anchor"],                           # [id]
                "canonical_encoding": CANONICAL_ENCODING,                         # [id] (D186)
                "head": history["head"],                                          # [fn]
                "repository_state_id": rsid,                                      # [fn]
                "analysis_input_id": aid,                                         # [fn]
                "environment": env,                                               # [id]
                "classes_reproduction_inputs": machine["classes_reproduction_inputs"],  # [x]
                "history_backend": shared["history_backend"],                     # [id]
                "window_applied": {
                    "commits_in_window": len(history["commit_shas"]),             # [fn]
                    "commit_list_sha256": spec["commit_list_sha256"],             # [id]
                    "last_commit_map_sha256": spec["last_commit_map_sha256"],     # [id] (D146·D205)
                    "history_complete": history["history_complete"],              # [fn] (D204 — 걷기의 함수)
                    "graft_boundary_shas": history["graft_boundary_shas"],        # [fn]
                },
                "component": {"strategy": shared["component"]["strategy"],
                              "split_share_basis": shared["component"]["split_share_basis"],
                              "algorithm_version": shared["component"]["algorithm_version"]},   # [id]
                "parameters": shared["parameters"],                               # [id]
                "percentile_method": PERCENTILE_METHOD,                           # [id]
                "canonical_encoding": CANONICAL_ENCODING,                         # [id]
            },
            "tree": {"file_count": len(printed),
                     "files": [{"path": p, "content_id": c} for p, c in printed]},  # [id]
        }

    reports = {name: report_for(m) for name, m in inp["machines"].items()}
    # D202 — 같은 입력을 **섞은 삽입 순서**로 넣어도 같은 바이트: 정렬 규칙이 있을 때만 성립하고, 없으면(변조)
    # 두 머신이 같은 트리를 다른 순서로 인쇄한다(F3-8·O3-8 — 같은 구현을 두 번 돌리면 못 보는 구멍).
    shuffled = list(reversed(files))
    insertion = None
    if len(files) >= 2 and inp.get("shuffled_insertion", True):
        first = inp["machines"][next(iter(inp["machines"]))]
        sorted_a = canonical(comparison_target(report_for(first, files), excluded))
        sorted_b = canonical(comparison_target(report_for(first, shuffled), excluded))
        raw_a = canonical(comparison_target(report_for(first, files, sort_arrays=False), excluded))
        raw_b = canonical(comparison_target(report_for(first, shuffled, sort_arrays=False), excluded))
        insertion = {"orders": {"natural": [p for p, _ in files], "shuffled": [p for p, _ in shuffled]},
                     "same_bytes_when_sorted_by_D202_1": sorted_a == sorted_b,
                     "mutation_without_sort_rule": {"bytes_differ": raw_a != raw_b}}
    names = list(reports)
    ra, rb = reports[names[0]], reports[names[1]]
    ta, tb = (comparison_target(r, excluded) for r in (ra, rb))
    full_a, full_b = canonical(ra), canonical(rb)
    tgt_a, tgt_b = canonical(ta), canonical(tb)

    # 넷째 종류(D158): id 입력도 함수도 아닌데 비교 목록에서 빠지지 않은 필드. 규칙이 잡아야 한다.
    mut = inp["fourth_kind_mutation"]
    mutated = {}
    for name, r in reports.items():
        m = json.loads(json.dumps(r))
        m["reproduce"][mut["field"]] = mut["values"][name]
        mutated[name] = canonical(comparison_target(m, excluded))
    mutation_caught = mutated[names[0]] != mutated[names[1]]

    id_keys = _keys_recursive(spec)
    excluded_leaves = [f.split(".")[-1] for f in excluded]

    machines = {}
    for name, r in reports.items():
        machines[name] = {
            "scanned_at": r["reproduce"]["scanned_at"],
            "classes_reproduction_inputs": r["reproduce"]["classes_reproduction_inputs"],
            "output_sha256": "sha256:" + hashlib.sha256(canonical(r)).hexdigest(),
            "comparison_target_sha256":
                "sha256:" + hashlib.sha256(canonical(comparison_target(r, excluded))).hexdigest(),
        }

    return {
        "case": inp["case"],
        "generated_by": GENERATED_BY,
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "canonical_encoding": CANONICAL_ENCODING,
        "excluded_fields": excluded,
        "repository_state_id": rsid,
        "analysis_input_id": aid,
        "comparison_target": ta,
        "machines": machines,
        "fourth_kind_mutation": {"field": mut["field"], "caught": mutation_caught},
        **({"shuffled_insertion": insertion} if insertion else {}),
        "assertions": {
            "comparison_targets_byte_identical": tgt_a == tgt_b,
            **({"shuffled_insertion_same_bytes": insertion["same_bytes_when_sorted_by_D202_1"],
                "without_sort_rule_bytes_differ": insertion["mutation_without_sort_rule"]["bytes_differ"]} if insertion else {}),
            "full_outputs_differ": full_a != full_b,
            "scanned_at_differs":
                ra["reproduce"]["scanned_at"] != rb["reproduce"]["scanned_at"],
            "classes_reproduction_inputs_differ":
                ra["reproduce"]["classes_reproduction_inputs"]
                != rb["reproduce"]["classes_reproduction_inputs"],
            "excluded_fields_are_not_id_inputs":
                not any(leaf in id_keys for leaf in excluded_leaves),
            "fourth_kind_field_is_caught": mutation_caught,
            "scanned_at_is_d157_notation": all(
                D157_PATTERN.match(r["reproduce"]["scanned_at"]) for r in reports.values()),
        },
    }


def run_time_notations(inp: dict) -> dict:
    """§2.7·D157 — 같은 unix 초의 네 표기가 정규 표기로 한 바이트·한 id가 된다."""
    spec = inp["time_notations"]
    unix = spec["unix_seconds"]
    pattern = re.compile(spec["d157_pattern"])
    skeleton = {k: v for k, v in spec["id_input_skeleton"].items() if not k.startswith("$")}

    def id_with(ts: str) -> str:
        s = json.loads(json.dumps(skeleton))
        s["window_anchor"]["timestamp"] = ts
        return sha256(s)

    canon = canonical_time(unix)
    notations = {}
    for name, raw in spec["notations"].items():
        # 파이썬 3.10 이하의 fromisoformat은 `Z`를 모른다 — 파싱 편의일 뿐, 표기 규칙은 D157이다.
        parsed = int(datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp())
        notations[name] = {
            "raw": raw,
            "unix_seconds": parsed,
            "same_instant": parsed == unix,
            "raw_id": id_with(raw),
            "canonical": canonical_time(parsed),
            "canonical_id": id_with(canonical_time(parsed)),
        }
    raw_ids = {n["raw_id"] for n in notations.values()}
    raw_strings = {n["raw"] for n in notations.values()}
    canon_ids = {n["canonical_id"] for n in notations.values()}
    canon_strings = {n["canonical"] for n in notations.values()}

    # 겪은 사고의 대역: 파이썬 isoformat()은 UTC를 `+00:00`으로 적는다 — D157 패턴에 실패해야 한다.
    isoformat_out = datetime.fromtimestamp(unix, timezone.utc).isoformat()

    return {
        "case": inp["case"],
        "generated_by": GENERATED_BY,
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "canonical_encoding": CANONICAL_ENCODING,
        "unix_seconds": unix,
        "canonical": canon,
        "notations": notations,
        "non_canonical_producers": {
            "python_isoformat": {"output": isoformat_out,
                                 "matches_d157": bool(pattern.match(isoformat_out))},
        },
        "assertions": {
            "all_notations_same_instant": all(n["same_instant"] for n in notations.values()),
            "raw_strings_differ": len(raw_strings) == len(notations) and len(notations) > 1,
            "raw_ids_differ": len(raw_ids) == len(notations),
            "canonical_strings_identical": canon_strings == {canon},
            "canonical_ids_identical": len(canon_ids) == 1,
            "canonical_matches_d157_pattern": bool(pattern.match(canon)),
            "python_isoformat_fails_d157_pattern": not pattern.match(isoformat_out),
        },
    }


def measure_cache_key(projection: dict, files: dict[str, str], env: dict,
                      algorithm_versions: dict, parameters: dict,
                      people: dict | None = None, history: dict | None = None) -> tuple[str, dict]:
    """§4.5·D159 — 캐시 키 = 내용 + 닿는 엔진·알고리즘 버전 + 읽는 파라미터. 사영이다."""
    key = {
        "content": [files[p] for p in projection["content"]],
        "environment": {e: env[e] for e in projection["environment"]},
        "algorithm_versions": {a: algorithm_versions[a] for a in projection["algorithm_versions"]},
        "parameters": {p: parameters[p] for p in projection["parameters"]},
    }
    # D195 — `team_count`(와 같은 종류의 저자 유래 측정)의 키 = (`commit_list_sha256`, attribution,
    # team_mapping_sha256). **저자 집합이 아니다**: 캐시는 `build/jqradar/`에 저장되는 값이라 저자 집합을
    # 키에 두면 "해시도 저장하지 않는다"(§2.7, D48)가 캐시에서 깨진다 — 저자는 창 안 커밋 SHA에서
    # 재도출된다. k 하한은 계약 상수라 키에 없다(`contract_version`이 덮는다, D186) — v3.10.2까지
    # 이 키에 `k_threshold`가 있었고 D195의 키 교체가 그것을 뺐다(fixture_change 2026-10-07).
    if projection.get("people"):
        key["people"] = {k: people[k] for k in projection["people"]}
    if projection.get("history"):
        key["history"] = {h: history[h] for h in projection["history"]}
    return sha256(key), key


def projection_within_2_8(projection: dict, env: dict, algorithm_versions: dict,
                          parameters: dict, people: dict | None = None,
                          history: dict | None = None) -> bool:
    """어느 키에 있는 것은 §2.8 입력 목록에 있어야 한다(D159)."""
    return (set(projection["environment"]) <= set(env)
            and set(projection["algorithm_versions"]) <= set(algorithm_versions)
            and set(projection["parameters"]) <= set(parameters)
            and set(projection.get("people", [])) <= set(people or DEFAULT_PEOPLE)
            and set(projection.get("history", [])) <= {"commit_list_sha256"})


def run_parameter_projection(case_dir: Path, inp: dict) -> dict:
    """§4.5·D159 — 파라미터 하나 변경 → 그것을 읽는 측정만 캐시 미스."""
    tree = case_dir / inp["repo"]["tree"]
    files = tree_files(tree)
    fmap = dict(files)
    with tempfile.TemporaryDirectory() as tmp:
        history = build_history(tree, inp["repo"], Path(tmp) / "repo")
    shared, env = inp["shared_inputs"], inp["environment"]
    algo = shared["algorithm_versions"]
    change = inp["parameter_change"]

    p_before = dict(shared["parameters"])
    assert p_before[change["name"]] == change["from"], "input.json의 from이 parameters와 다르다"
    p_after = {**p_before, change["name"]: change["to"]}

    def ids(params):
        aid, _ = analysis_input_id({**shared, "parameters": params}, env, files, history)
        return aid

    projections = inp["measure_projections"]
    keys = {"before": {}, "after": {}}
    for m, proj in projections.items():
        keys["before"][m], _ = measure_cache_key(proj, fmap, env, algo, p_before)
        keys["after"][m], _ = measure_cache_key(proj, fmap, env, algo, p_after)
    misses = sorted(m for m in projections if keys["before"][m] != keys["after"][m])
    hits = sorted(m for m in projections if keys["before"][m] == keys["after"][m])
    readers = sorted(m for m, proj in projections.items() if change["name"] in proj["parameters"])

    # 변조 1: 키에서 파라미터를 빼면 거짓 적중이 난다(D159 문장 그대로).
    m1 = inp["mutations"]["projection_missing_parameter"]
    proj1 = json.loads(json.dumps(projections[m1["measure"]]))
    proj1["parameters"] = [p for p in proj1["parameters"] if p != m1["drop_parameter"]]
    k1b, _ = measure_cache_key(proj1, fmap, env, algo, p_before)
    k1a, _ = measure_cache_key(proj1, fmap, env, algo, p_after)
    false_hit = k1b == k1a

    # 변조 2: §2.8 밖의 입력을 키에 넣으면 부분집합 검사가 거부한다.
    m2 = inp["mutations"]["projection_with_foreign_input"]
    proj2 = json.loads(json.dumps(projections[m2["measure"]]))
    proj2["parameters"] = proj2["parameters"] + [m2["add_parameter"]]
    foreign_rejected = not projection_within_2_8(proj2, env, algo, p_before)

    return {
        "case": inp["case"],
        "generated_by": GENERATED_BY,
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "canonical_encoding": CANONICAL_ENCODING,
        "parameter_change": change,
        "repository_state_id": repository_state_id(files),
        "analysis_input_id": {"before": ids(p_before), "after": ids(p_after)},
        "measure_projections": projections,
        "cache_keys": keys,
        "cache": {"miss": misses, "hit": hits, "readers_of_changed_parameter": readers},
        "mutations": {
            "projection_missing_parameter": {"measure": m1["measure"], "dropped": m1["drop_parameter"],
                                             "key_before": k1b, "key_after": k1a, "false_hit": false_hit},
            "projection_with_foreign_input": {"measure": m2["measure"], "added": m2["add_parameter"],
                                              "rejected": foreign_rejected},
        },
        "assertions": {
            "analysis_input_id_changes": ids(p_before) != ids(p_after),
            "repository_state_id_unchanged": True,   # 트리는 손대지 않았다 — 같은 files에서 계산
            "only_readers_miss": misses == readers and len(misses) >= 1,
            "non_readers_hit": hits == sorted(set(projections) - set(readers)) and len(hits) >= 1,
            "projections_subset_of_2_8_inputs": all(
                projection_within_2_8(p, env, algo, p_before) for p in projections.values()),
            "dropping_parameter_from_key_yields_false_hit": false_hit,
            "foreign_input_is_rejected": foreign_rejected,
        },
    }


def run_people_variants(case_dir: Path, inp: dict) -> dict:
    """§2.8·D160 — 저작 정책 두 변이(같은 트리·같은 이력): `analysis_input_id`는 다르고
    `repository_state_id`는 같다. 그리고 사영(D159): `people`을 읽는 측정(`team_count`)만
    캐시 미스, `cx`·`pair_dup_tokens`는 적중 — 매핑 한 줄이 바뀌어도 리포트는 다시
    조립되지만 내용 주소 측정은 다시 재지 않는다."""
    tree = case_dir / inp["repo"]["tree"]
    files = tree_files(tree)
    fmap = dict(files)
    with tempfile.TemporaryDirectory() as tmp:
        history = build_history(tree, inp["repo"], Path(tmp) / "repo")
    shared, env = inp["shared_inputs"], inp["environment"]
    algo, params = shared["algorithm_versions"], shared["parameters"]
    hist_inputs = {"commit_list_sha256": hashlib.sha256(canonical(history["commit_shas"])).hexdigest()}

    variants, keys = {}, {}
    for name, v in inp["people_variants"].items():
        people = {"attribution": v["attribution"],
                  "team_mapping_sha256": team_mapping_sha256(v.get("team_mapping"))}
        aid, _ = analysis_input_id({**shared, "people": people}, env, files, history)
        variants[name] = {"people": people,
                          "team_mapping_lines": (len(v["team_mapping"].splitlines())
                                                 if v.get("team_mapping") is not None else None),
                          "repository_state_id": repository_state_id(files),
                          "analysis_input_id": aid}
        keys[name] = {m: measure_cache_key(proj, fmap, env, algo, params, people, hist_inputs)[0]
                      for m, proj in inp["measure_projections"].items()}
    a, b = list(variants)
    projections = inp["measure_projections"]
    misses = sorted(m for m in projections if keys[a][m] != keys[b][m])
    hits = sorted(m for m in projections if keys[a][m] == keys[b][m])
    readers = sorted(m for m, proj in projections.items() if proj.get("people"))

    # 변조: team_count 사영에서 매핑 해시를 빼면 매핑이 바뀌어도 거짓 적중이 난다(D160).
    mut = inp["mutation_drop_mapping_from_key"]
    proj = json.loads(json.dumps(projections[mut["measure"]]))
    proj["people"] = [f for f in proj["people"] if f != "team_mapping_sha256"]
    k_a = measure_cache_key(proj, fmap, env, algo, params, variants[a]["people"], hist_inputs)[0]
    k_b = measure_cache_key(proj, fmap, env, algo, params, variants[b]["people"], hist_inputs)[0]
    mutation = {"measure": mut["measure"], "dropped": "team_mapping_sha256",
                "false_hit": k_a == k_b}

    people_fields_differ = variants[a]["people"] != variants[b]["people"]
    return {
        "case": inp["case"],
        "generated_by": GENERATED_BY,
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "canonical_encoding": CANONICAL_ENCODING,
        "variants": variants,
        "measure_projections": projections,
        "cache_keys": keys,
        "cache": {"miss": misses, "hit": hits, "readers_of_people": readers},
        "mutation_drop_mapping_from_key": mutation,
        "assertions": {
            "people_inputs_differ": people_fields_differ,
            "repository_state_id_equal":
                variants[a]["repository_state_id"] == variants[b]["repository_state_id"],
            "analysis_input_id_differs":
                variants[a]["analysis_input_id"] != variants[b]["analysis_input_id"],
            "only_people_readers_miss": misses == readers and len(misses) >= 1,
            "content_measures_hit": hits == sorted(set(projections) - set(readers)) and len(hits) >= 1,
            "projections_subset_of_2_8_inputs": all(
                projection_within_2_8(pr, env, algo, params, variants[a]["people"], hist_inputs)
                for pr in projections.values()),
            **({"dropping_mapping_hash_yields_false_hit": mutation["false_hit"]}
               if mut.get("expect_false_hit", True) else {}),
        },
    }


def run_recompute_from_reproduce(case_dir: Path, inp: dict) -> dict:
    """§2.8·D111·D186 — reproduce만으로 id 재계산. 단언 둘: 같은 블록에서 같은 id, 블록의 id 입력 하나를
    바꾸면(창 12 → 24개월, 커밋 목록은 그대로) id가 **갈린다** — 창 파라미터가 [fn] 자리에 있던 v3.10.0까지는
    그 변경이 id에 닿지 않았다(O3-6)."""
    tree = case_dir / inp["repo"]["tree"]
    files = tree_files(tree)
    with tempfile.TemporaryDirectory() as tmp:
        history = build_history(tree, inp["repo"], Path(tmp) / "repo")
    shared, env = inp["shared_inputs"], inp["environment"]
    aid, spec = analysis_input_id(shared, env, files, history)
    # 한 번 스캔한 결과의 reproduce 블록(§7 모양)을 만든다 — 이것만 들고 다시 계산한다.
    reproduce = {
        "tool_version": shared["core_tool_version"], "schema_version": shared["schema_version"],
        "contract_version": shared["contract_version"], "scanned_at": canonical_time(inp["scanned_at_unix"]),
        "algorithm_versions": {"component_strategy": shared["component"]["algorithm_version"], **shared["algorithm_versions"]},
        "window_anchor": spec["window_anchor"], "head": history["head"],
        "repository_state_id": repository_state_id(files), "analysis_input_id": aid,
        "canonical_encoding": CANONICAL_ENCODING, "environment": env,
        "history_backend": shared["history_backend"],
        "window_applied": {"commits_in_window": len(history["commit_shas"]), "commit_list_sha256": spec["commit_list_sha256"],
                           "last_commit_map_sha256": spec["last_commit_map_sha256"],
                           "history_complete": history["history_complete"], "graft_boundary_shas": history["graft_boundary_shas"]},
        "component": {"strategy": shared["component"]["strategy"], "split_share_basis": shared["component"]["split_share_basis"], "count": 1},
        "parameters": shared["parameters"], "percentile_method": PERCENTILE_METHOD,
        "people": shared.get("people", DEFAULT_PEOPLE),
        "bytecode_scope": {**spec["bytecode_scope"], "external_edges": 0},   # [id] 범위 정의 + [fn] 집계
    }
    recomputed = id_from_reproduce(reproduce, files, history)
    mutated = json.loads(json.dumps(reproduce)); mutated["parameters"]["window.months"] = 24
    recomputed_mutated = id_from_reproduce(mutated, files, history)
    return {
        "case": inp["case"], "generated_by": GENERATED_BY, "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"], "canonical_encoding": CANONICAL_ENCODING,
        "printed_analysis_input_id": aid,
        "recomputed_from_reproduce": recomputed,
        "recomputed_after_window_months_24": recomputed_mutated,
        "assertions": {
            "recompute_matches_printed": recomputed == aid,
            "window_parameter_reaches_id": recomputed_mutated != aid,
        },
    }



# ── D193 — 이력 캐시 층 1의 키 = (커밋, 관측된 부모, 백엔드 이름 + 버전) ────────────────────────
#
# 층 1("커밋별 변경 경로 집합", rename 탐지 전)이 읽는 입력은 커밋 자신·관측된 부모·백엔드뿐이다.
# `rename.similarity`는 읽지 않으므로 키에 없다 — D159의 "읽지 않는 파라미터는 키에 없다"는 양방향이다:
# 키에 없는 것을 읽으면 거짓 적중, 읽지 않는 것이 키에 있으면 **헛미스**(파라미터 하나가 바뀌면
# 캐시 전부가 죽는다 — (b) "큰 키"를 포기한 이유, §0-42).
LAYER1_FIELDS = ("commit", "observed_parents", "history_backend.name", "history_backend.version")


def backend_version(history_backend: dict, env: dict):
    """D186·D193 — jgit이면 `environment.jgit`, native면 `history_backend.git_version`이 백엔드 버전의 정본."""
    return env["jgit"] if history_backend["name"] == "jgit" else history_backend["git_version"]


def layer1_key(projection: list[str], commit: str, parents: list[str],
               history_backend: dict, env: dict, parameters: dict) -> str:
    key = {}
    for f in projection:
        if f == "commit":
            key["commit"] = commit
        elif f == "observed_parents":
            key["observed_parents"] = parents
        elif f == "history_backend.name":
            key["history_backend.name"] = history_backend["name"]
        elif f == "history_backend.version":
            key["history_backend.version"] = backend_version(history_backend, env)
        elif f.startswith("parameters."):
            key[f] = parameters[f[len("parameters."):]]
        else:
            raise KeyError(f"층 1 키에 둘 수 없는 입력: {f}")
    return sha256(key)


def layer1_projection_within_2_8(projection: list[str], parameters: dict) -> bool:
    """어느 키에 있는 것은 §2.8에 있어야 한다(D159·D192). 커밋·관측된 부모·백엔드는 D193이 §2.8에 적은
    층 1의 입력이고, 파라미터는 §2.8 `parameters`의 것이어야 한다."""
    return all(f in LAYER1_FIELDS or (f.startswith("parameters.") and f[len("parameters."):] in parameters)
               for f in projection)


def observed_commits(workdir: Path) -> list[tuple[str, list[str]]]:
    """HEAD에서 도달 가능한 커밋과 **관측된** 부모 — graft 경계는 부모 없이 보인다(D148·D193)."""
    env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}
    raw = subprocess.run(["git", "-C", str(workdir), "log", "--format=%H %P"], env=env,
                         check=True, capture_output=True, text=True).stdout
    out = []
    for line in raw.strip().splitlines():
        parts = line.split()
        out.append((parts[0], parts[1:]))
    return out


def run_history_cache_projection(case_dir: Path, inp: dict) -> dict:
    """D193 — 같은 SHA에서 백엔드 토글(jgit → native, jgit 버전 변경) → 층 1 전부 미스;
    `rename.similarity` 변경 → 전부 **적중**(층 1은 읽지 않는다)."""
    tree = case_dir / inp["repo"]["tree"]
    files = tree_files(tree)
    with tempfile.TemporaryDirectory() as tmp:
        history = build_history(tree, inp["repo"], Path(tmp) / "repo")
        commits = observed_commits(Path(tmp) / "repo")
    shared = inp["shared_inputs"]
    projection = inp["layer1_projection"]
    variants = inp["backend_variants"]
    base_name = next(iter(variants))

    def keys_for(history_backend, env, parameters):
        return {sha: layer1_key(projection, sha, parents, history_backend, env, parameters)
                for sha, parents in commits}

    def aid_for(history_backend, env, parameters):
        return analysis_input_id({**shared, "history_backend": history_backend, "parameters": parameters},
                                 env, files, history)[0]

    base = variants[base_name]
    base_keys = keys_for(base["history_backend"], base["environment"], shared["parameters"])
    base_aid = aid_for(base["history_backend"], base["environment"], shared["parameters"])
    toggles = {}
    for name, v in variants.items():
        if name == base_name:
            continue
        k = keys_for(v["history_backend"], v["environment"], shared["parameters"])
        toggles[name] = {
            "history_backend": v["history_backend"], "backend_version": backend_version(v["history_backend"], v["environment"]),
            "analysis_input_id": aid_for(v["history_backend"], v["environment"], shared["parameters"]),
            "layer1_miss": sorted(sha[:9] for sha in k if k[sha] != base_keys[sha]),
            "layer1_hit": sorted(sha[:9] for sha in k if k[sha] == base_keys[sha]),
        }
    pv = inp["parameter_variant"]
    p_after = {**shared["parameters"], pv["name"]: pv["to"]}
    k_param = keys_for(base["history_backend"], base["environment"], p_after)
    param = {"name": pv["name"], "from": shared["parameters"][pv["name"]], "to": pv["to"],
             "analysis_input_id": aid_for(base["history_backend"], base["environment"], p_after),
             "layer1_miss": sorted(sha[:9] for sha in k_param if k_param[sha] != base_keys[sha]),
             "layer1_hit": sorted(sha[:9] for sha in k_param if k_param[sha] == base_keys[sha])}

    # 변조 1: 키에서 백엔드를 빼면 백엔드 토글이 거짓 적중한다 — jgit로 채운 캐시를 native가 적중(F3-4).
    proj1 = [f for f in projection if not f.startswith("history_backend.")]
    tgl = next(iter(toggles))
    k1_base = {sha: layer1_key(proj1, sha, par, base["history_backend"], base["environment"], shared["parameters"]) for sha, par in commits}
    k1_tgl = {sha: layer1_key(proj1, sha, par, variants[tgl]["history_backend"], variants[tgl]["environment"], shared["parameters"]) for sha, par in commits}
    false_hit = all(k1_base[s] == k1_tgl[s] for s in k1_base)
    # 변조 2: 읽지 않는 파라미터를 키에 넣으면 파라미터 하나가 캐시 전부를 죽인다 — 헛미스(큰 키, §0-42 포기한 것).
    proj2 = projection + [f"parameters.{pv['name']}"]
    k2_before = {sha: layer1_key(proj2, sha, par, base["history_backend"], base["environment"], shared["parameters"]) for sha, par in commits}
    k2_after = {sha: layer1_key(proj2, sha, par, base["history_backend"], base["environment"], p_after) for sha, par in commits}
    spurious_miss = all(k2_before[s] != k2_after[s] for s in k2_before)
    # 변조 3: §2.8 밖의 입력은 부분집합 검사가 거부한다.
    proj3 = projection + [inp["mutations"]["foreign_input"]]
    foreign_rejected = not layer1_projection_within_2_8(proj3, shared["parameters"])

    return {
        "case": inp["case"], "generated_by": GENERATED_BY, "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"], "canonical_encoding": CANONICAL_ENCODING,
        "layer1_projection": projection,
        "commits": [{"sha": sha[:9], "observed_parents": [p[:9] for p in par]} for sha, par in commits],
        "base": {"name": base_name, "history_backend": base["history_backend"],
                 "backend_version": backend_version(base["history_backend"], base["environment"]),
                 "analysis_input_id": base_aid,
                 "layer1_keys": {sha[:9]: base_keys[sha] for sha in base_keys}},
        "backend_toggles": toggles,
        "parameter_variant": param,
        "mutations": {
            "projection_missing_backend": {"dropped": ["history_backend.name", "history_backend.version"],
                                           "toggle": tgl, "false_hit_on_backend_toggle": false_hit},
            "projection_with_unread_parameter": {"added": f"parameters.{pv['name']}", "spurious_miss": spurious_miss},
            "projection_with_foreign_input": {"added": inp["mutations"]["foreign_input"], "rejected": foreign_rejected},
        },
        "assertions": {
            "backend_toggle_changes_analysis_input_id": all(t["analysis_input_id"] != base_aid for t in toggles.values()),
            "backend_toggle_misses_every_commit": all(not t["layer1_hit"] and len(t["layer1_miss"]) == len(commits) for t in toggles.values()),
            "rename_similarity_changes_analysis_input_id": param["analysis_input_id"] != base_aid,
            "rename_similarity_hits_every_commit": not param["layer1_miss"] and len(param["layer1_hit"]) == len(commits),
            "projection_subset_of_2_8_inputs": layer1_projection_within_2_8(projection, shared["parameters"]),
            "dropping_backend_from_key_yields_false_hit": false_hit,
            "unread_parameter_in_key_yields_spurious_miss": spurious_miss,
            "foreign_input_is_rejected": foreign_rejected,
        },
    }


# ── D193·D148 — shallow → unshallow 재스캔: 관측된 부모가 키에 있어 거짓 적중이 구조로 막힌다 ────────
#
# O3-5의 시나리오 그대로: shallow 스캔이 graft 경계 커밋을 "모든 파일을 추가한 커밋"으로 층 1에 넣는다.
# `git fetch --unshallow` 뒤 **같은 캐시**로 재스캔할 때 그 항목이 재사용되면 경계 전의 파일들이
# 경계 커밋에서 "마지막으로 바뀐" 것이 되어 **그럴듯한 틀린 수**(D148)가 완전한 클론에서 돌아온다.
# 관측된 부모가 키에 있으면 경계 커밋의 두 모습(부모 없음/있음)이 다른 키라 재사용되지 않는다.

def _git(workdir: Path, *args: str) -> str:
    env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null", "TZ": "UTC"}
    return subprocess.run(["git", "-C", str(workdir), *args], env=env, check=True,
                          capture_output=True, text=True).stdout.strip()


def scan_with_layer1_cache(workdir: Path, cache: dict, projection: list[str],
                           shared: dict, env: dict, files: list[tuple[str, str]]) -> tuple[dict, dict]:
    """합성 `scan` — 층 1 캐시를 거쳐 파일별 마지막 커밋 맵을 만든다. 돌려주는 산출물이 비교 대상이다."""
    commits = observed_commits(workdir)
    boundary = {l.strip() for l in (workdir / ".git" / "shallow").read_text().splitlines()} \
        if (workdir / ".git" / "shallow").exists() else set()
    log = {"hit": [], "miss": []}
    paths_of = {}
    for sha, parents in commits:
        key = layer1_key(projection, sha, parents, shared["history_backend"], env, shared["parameters"])
        if key in cache:
            log["hit"].append(sha[:9])
        else:
            # 층 1의 값 — 그 커밋이 바꾼 경로 집합. graft 경계는 부모가 없어 트리 전체가 추가로 보인다.
            changed = _git(workdir, "show", "--name-only", "--format=", sha).splitlines()
            cache[key] = {"commit": sha, "observed_parents": parents, "paths": sorted(p for p in changed if p)}
            log["miss"].append(sha[:9])
        paths_of[sha] = cache[key]["paths"]
    last = {}
    for path, _ in files:
        last[path] = None
        for sha, _p in commits:            # 최신순
            if path in paths_of[sha]:
                # D148 — graft 경계에서 "생긴" 것으로 보이면 나이를 모른다.
                last[path] = None if sha in boundary else sha
                break
    head_time = canonical_time(int(_git(workdir, "show", "-s", "--format=%ct", "HEAD")))
    history = {"commit_shas": [sha for sha, _ in reversed(commits)], "head_committer_time": head_time,
               "last_commit_map": last}
    aid, _ = analysis_input_id(shared, env, files, history)
    artifact = {
        "analysis_input_id": aid,
        "repository_state_id": repository_state_id(files),
        "history_complete": not boundary,
        "graft_boundary_count": len(boundary),
        "last_commit_map": {p: (v[:9] if v else None) for p, v in last.items()},
        "age_reason": {p: "age_unknown" for p, v in last.items() if v is None},
    }
    return artifact, log


def run_shallow_unshallow(case_dir: Path, inp: dict) -> dict:
    tree = case_dir / inp["repo"]["tree"]
    files = tree_files(tree)
    shared, env, projection = inp["shared_inputs"], inp["environment"], inp["layer1_projection"]
    depth = int(inp["shallow_depth"])
    with tempfile.TemporaryDirectory() as tmp:
        full = Path(tmp) / "full"
        build_history(tree, inp["repo"], full)
        shallow = Path(tmp) / "shallow"
        _git(Path(tmp), "clone", "-q", "--depth", str(depth), "--no-local", f"file://{full}", str(shallow))
        fresh = Path(tmp) / "fresh"
        _git(Path(tmp), "clone", "-q", "--no-local", f"file://{full}", str(fresh))
        boundary = sorted(l.strip() for l in (shallow / ".git" / "shallow").read_text().splitlines())

        def scenario(proj):
            cache = {}
            a, log_a = scan_with_layer1_cache(shallow, cache, proj, shared, env, files)
            return cache, a, log_a

        # 올바른 키
        cache, shallow_art, log_shallow = scenario(projection)
        _git(shallow, "fetch", "-q", "--unshallow")
        unshallow_art, log_unshallow = scan_with_layer1_cache(shallow, cache, projection, shared, env, files)
        fresh_art, log_fresh = scan_with_layer1_cache(fresh, {}, projection, shared, env, files)
        boundary_entries = [e for e in cache.values() if e["commit"] in boundary]

        # 변조: 관측된 부모가 키에 없으면 — 같은 시나리오를 새 shallow clone에서 다시
        shallow2 = Path(tmp) / "shallow2"
        _git(Path(tmp), "clone", "-q", "--depth", str(depth), "--no-local", f"file://{full}", str(shallow2))
        proj_bad = [f for f in projection if f != "observed_parents"]
        cache_bad = {}
        scan_with_layer1_cache(shallow2, cache_bad, proj_bad, shared, env, files)
        _git(shallow2, "fetch", "-q", "--unshallow")
        bad_art, log_bad = scan_with_layer1_cache(shallow2, cache_bad, proj_bad, shared, env, files)

    same_bytes = render(unshallow_art) == render(fresh_art)
    wrong_map = {p: {"false_hit": bad_art["last_commit_map"][p], "truth": fresh_art["last_commit_map"][p]}
                 for p in fresh_art["last_commit_map"]
                 if bad_art["last_commit_map"][p] != fresh_art["last_commit_map"][p]}
    return {
        "case": inp["case"], "generated_by": GENERATED_BY, "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"], "canonical_encoding": CANONICAL_ENCODING,
        "shallow_depth": depth, "layer1_projection": projection,
        "graft_boundary": [b[:9] for b in boundary],
        "shallow_scan": {"artifact": shallow_art, "cache": log_shallow},
        "unshallow_rescan_same_cache": {"artifact": unshallow_art, "cache": log_unshallow},
        "fresh_full_clone_scan": {"artifact": fresh_art, "cache": log_fresh},
        "boundary_layer1_entries": [{"commit": e["commit"][:9], "observed_parents": [p[:9] for p in e["observed_parents"]],
                                     "paths": e["paths"]} for e in boundary_entries],
        "mutation_without_observed_parents": {
            "projection": proj_bad, "rescan_cache": log_bad,
            "artifact_last_commit_map": bad_art["last_commit_map"],
            "plausible_wrong_numbers": wrong_map,
        },
        "assertions": {
            "shallow_scan_marks_boundary_files_age_unknown": bool(shallow_art["age_reason"]) and not shallow_art["history_complete"],
            "unshallow_rescan_is_byte_identical_to_fresh_full_clone": same_bytes,
            "boundary_commit_has_two_layer1_entries": len(boundary_entries) == 2 * len(boundary)
                and len({tuple(e["observed_parents"]) for e in boundary_entries}) == 2 * len(boundary),
            "boundary_entry_not_reused_after_unshallow": all(b[:9] in log_unshallow["miss"] for b in boundary),
            "non_boundary_entries_reused_after_unshallow": any(log_unshallow["hit"]),
            "projection_subset_of_2_8_inputs": layer1_projection_within_2_8(projection, shared["parameters"]),
            "without_observed_parents_boundary_entry_is_reused": all(b[:9] in log_bad["hit"] for b in boundary),
            "without_observed_parents_plausible_wrong_numbers_return": bool(wrong_map) and bad_art["history_complete"],
        },
    }


# ── D194 — 전이 캐시 키 = (finding_id, commit, 전이 사영 해시) ──────────────────────────────────────

def resolve_in_spec(spec: dict, field: str):
    """점 경로를 §2.8 id 스펙(dict)에서 푼다. `parameters.*`는 파라미터 이름에 점이 있어 통째로 본다.
    풀리지 않으면 §2.8 밖의 입력이다(KeyError)."""
    if field.startswith("parameters."):
        return spec["parameters"][field[len("parameters."):]]
    node = spec
    for part in field.split("."):
        node = node[part]
    return node


def transition_projection_within_2_8(projection: list[str], spec: dict) -> bool:
    try:
        for f in projection:
            resolve_in_spec(spec, f)
        return True
    except (KeyError, TypeError):
        return False


def transition_keys(projection: list[str], spec: dict, findings: list[dict]) -> dict:
    proj_hash = sha256({f: resolve_in_spec(spec, f) for f in projection})
    return {f"{fd['finding_id']}@{fd['commit'][:9]}":
            sha256({"finding_id": fd["finding_id"], "commit": fd["commit"], "transition_projection": proj_hash})
            for fd in findings}


def run_transition_cache(case_dir: Path, inp: dict) -> dict:
    tree = case_dir / inp["repo"]["tree"]
    files = tree_files(tree)
    shared, env, projection = inp["shared_inputs"], inp["environment"], inp["transition_projection"]
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        history = build_history(tree, inp["repo"], repo)
        # 새 커밋 하나 — HEAD·앵커·창 안 커밋 목록이 바뀐다.
        extra = inp["head_plus_one"]
        (repo / extra["path"]).parent.mkdir(parents=True, exist_ok=True)
        (repo / extra["path"]).write_text(extra["content"], encoding="utf-8")
        when = (datetime.fromisoformat(inp["repo"]["base_time"])
                + timedelta(seconds=inp["repo"]["step_seconds"] * (len(inp["repo"]["history"]) + 1))).isoformat()
        env_git = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
                   "GIT_AUTHOR_NAME": inp["repo"]["committer"]["name"], "GIT_AUTHOR_EMAIL": inp["repo"]["committer"]["email"],
                   "GIT_COMMITTER_NAME": inp["repo"]["committer"]["name"], "GIT_COMMITTER_EMAIL": inp["repo"]["committer"]["email"],
                   "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
        subprocess.run(["git", "-C", str(repo), "add", "--", extra["path"]], env=env_git, check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", extra["message"]], env=env_git, check=True, capture_output=True)
        new_head = _git(repo, "rev-parse", "HEAD")
        files_plus = tree_files(repo)
        history_plus = history_facts(repo, [p for p, _ in files_plus if not p.startswith(".git")], shared["parameters"])
    files_plus = [(p, c) for p, c in files_plus if not p.startswith(".git")]
    findings = [{"finding_id": f["finding_id"], "commit": history["commit_shas"][f["commit_index"]]} for f in inp["findings"]]

    aid0, spec0 = analysis_input_id(shared, env, files, history)
    keys0 = transition_keys(projection, spec0, findings)
    aid1, spec1 = analysis_input_id(shared, env, files_plus, history_plus)
    keys1 = transition_keys(projection, spec1, findings)

    bump = inp["variants"]["succession_bump"]
    shared_b = json.loads(json.dumps(shared)); shared_b["algorithm_versions"]["succession"] = bump
    aid2, spec2 = analysis_input_id(shared_b, env, files, history)
    keys2 = transition_keys(projection, spec2, findings)

    roots = inp["variants"]["class_roots"]
    shared_c = json.loads(json.dumps(shared)); shared_c["bytecode_scope"]["class_roots"] = roots
    aid3, spec3 = analysis_input_id(shared_c, env, files, history)
    keys3 = transition_keys(projection, spec3, findings)

    def diff(a, b):
        return {"miss": sorted(k for k in a if a[k] != b[k]), "hit": sorted(k for k in a if a[k] == b[k])}

    # 변조 1: 사영에서 bytecode_scope를 빼면 class_roots 변경이 거짓 적중한다(순환 finding의 그래프가 바뀌었는데).
    proj1 = [f for f in projection if f != "bytecode_scope"]
    fh = transition_keys(proj1, spec0, findings) == transition_keys(proj1, spec3, findings)
    # 변조 2: 들지 말아야 할 것(창 안 커밋 목록)을 넣으면 새 커밋 하나가 전부를 죽인다 — 증분이 서지 않는다(S3-15).
    proj2 = projection + ["commit_list_sha256"]
    k2a, k2b = transition_keys(proj2, spec0, findings), transition_keys(proj2, spec1, findings)
    spurious = all(k2a[k] != k2b[k] for k in k2a)
    # 변조 3: §2.8 밖의 입력은 거부.
    proj3 = projection + [inp["mutations"]["foreign_input"]]
    foreign_rejected = not transition_projection_within_2_8(proj3, spec0)

    return {
        "case": inp["case"], "generated_by": GENERATED_BY, "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"], "canonical_encoding": CANONICAL_ENCODING,
        "transition_projection": projection,
        "findings": [{"finding_id": f["finding_id"], "commit": f["commit"][:9]} for f in findings],
        "base": {"analysis_input_id": aid0, "transition_keys": keys0},
        "head_plus_one": {"head": new_head[:9], "analysis_input_id": aid1, "cache": diff(keys0, keys1)},
        "succession_bump": {"to": bump, "analysis_input_id": aid2, "cache": diff(keys0, keys2)},
        "class_roots_change": {"to": roots, "analysis_input_id": aid3, "cache": diff(keys0, keys3)},
        "mutations": {
            "projection_missing_bytecode_scope": {"dropped": "bytecode_scope", "false_hit_on_class_roots_change": fh},
            "projection_with_commit_list": {"added": "commit_list_sha256", "spurious_miss_on_new_commit": spurious},
            "projection_with_foreign_input": {"added": inp["mutations"]["foreign_input"], "rejected": foreign_rejected},
        },
        "assertions": {
            "new_commit_changes_analysis_input_id": aid1 != aid0,
            "new_commit_hits_every_transition_key": not diff(keys0, keys1)["miss"] and len(keys0) >= 2,
            "succession_bump_misses_every_transition_key": not diff(keys0, keys2)["hit"],
            "class_roots_change_misses_every_transition_key": not diff(keys0, keys3)["hit"],
            "projection_subset_of_2_8_inputs": transition_projection_within_2_8(projection, spec0),
            # D194 "들지 않는 것" — 창·앵커·head·커밋 목록·people·canonical_encoding은 사영에 없다.
            "projection_excludes_window_anchor_head_and_commit_list": not any(
                f in projection for f in ("window_anchor", "commit_list_sha256", "head", "people", "canonical_encoding"))
                and not any(f.startswith(("window", "parameters.window", "people.")) for f in projection),
            "dropping_bytecode_scope_from_key_yields_false_hit": fh,
            "commit_list_in_key_breaks_increment": spurious,
            "foreign_input_is_rejected": foreign_rejected,
        },
    }



# ── D204·D205 — 깊은 shallow vs full: 걷기가 경계 전에 끝나면 맵·완전성·id가 같다 ──────────────────────

def run_clone_depths(case_dir: Path, inp: dict) -> dict:
    tree = case_dir / inp["repo"]["tree"]
    shared, env = inp["shared_inputs"], inp["environment"]
    with tempfile.TemporaryDirectory() as tmp:
        full = Path(tmp) / "full"
        build_history(tree, inp["repo"], full)
        runs = {}
        for name, depth in [("full", None)] + list(inp["clone_depths"].items()):
            wd = full if depth is None else Path(tmp) / name
            if depth is not None:
                _git(Path(tmp), "clone", "-q", "--depth", str(depth), "--no-local", f"file://{full}", str(wd))
            files = [(p, c) for p, c in tree_files(wd) if not p.startswith(".git/")]
            facts = history_facts(wd, [p for p, _ in files], shared["parameters"])
            aid, spec = analysis_input_id(shared, env, files, facts)
            runs[name] = {"depth": depth, "analysis_input_id": aid, "repository_state_id": repository_state_id(files),
                          "commits_in_window": len(facts["commit_shas"]), "history_complete": facts["history_complete"],
                          "graft_boundary_shas": [b[:9] for b in facts["graft_boundary_shas"]],
                          "last_commit_map": {p: (v[:9] if v else None) for p, v in facts["last_commit_map"].items()},
                          "last_commit_map_canonical": canonical(facts["last_commit_map"]).decode("utf-8")[:400],
                          "last_commit_map_sha256": spec["last_commit_map_sha256"]}
    names = list(inp["clone_depths"])
    full_r, deep, shallow = runs["full"], runs[names[0]], runs[names[1]]
    return {
        "case": inp["case"], "generated_by": GENERATED_BY, "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"], "canonical_encoding": CANONICAL_ENCODING,
        "runs": runs,
        "assertions": {
            "repository_state_id_equal_in_all_clones": len({r["repository_state_id"] for r in runs.values()}) == 1,
            "deep_shallow_same_id_as_full": deep["analysis_input_id"] == full_r["analysis_input_id"],
            "deep_shallow_history_complete_true": deep["history_complete"] is True and deep["graft_boundary_shas"] == [],
            "deep_shallow_map_equals_full": deep["last_commit_map"] == full_r["last_commit_map"],
            "shallow_id_differs_from_full": shallow["analysis_input_id"] != full_r["analysis_input_id"],
            "shallow_history_complete_false": shallow["history_complete"] is False and len(shallow["graft_boundary_shas"]) >= 1,
            "shallow_map_null_where_boundary_reached": any(v is None for v in shallow["last_commit_map"].values())
                and all(v == full_r["last_commit_map"][p] for p, v in shallow["last_commit_map"].items() if v is not None),
            "map_hash_is_the_only_id_difference_between_clones": (
                shallow["commits_in_window"] == full_r["commits_in_window"]
                and shallow["last_commit_map_sha256"] != full_r["last_commit_map_sha256"]),
        },
    }


# ── §2.8 (i) ↔ id 스펙 — 자기 반례 ────────────────────────────────────────────────────────────────
# 계약 목록에 있는데 계산기가 빠뜨린 입력이 두 번 났다(`percentile_method` v3.10.0, `bytecode_scope` v3.10.3) — 그리고
# 이 판에서 셋째(`last_commit_map_sha256`). 이름을 글자로 대조해 넷째를 막는다. 표는 (i)의 이름 → 스펙 키.
I_TO_SPEC = {
    "tool_version": "core_tool_version", "schema_version": "schema_version", "contract_version": "contract_version",
    "algorithm_versions": "algorithm_versions", "environment": "environment", "history_backend": "history_backend",
    "name": "history_backend", "git_version": "history_backend",          # history_backend의 두 필드 — 전체가 id 입력(D186)
    "window_anchor": "window_anchor", "head": "commit_list_sha256",           # head는 창 안 목록의 끝 — 목록 해시가 봉인
    "repository_state_id": "source_files", "classes_id": "class_files",
    "commit_list_sha256": "commit_list_sha256", "last_commit_map_sha256": "last_commit_map_sha256",
    "component.strategy": "component", "component.split_share_basis": "component",
    "canonical_encoding": "canonical_encoding", "parameters": "parameters",
    "percentile_method": "percentile_method", "bytecode_scope": "bytecode_scope", "people": "people",
}


def selftest() -> int:
    text = PRD.read_text(encoding="utf-8")
    m = re.search(r"\(i\) \*\*id 입력\*\* — 위 목록의 값 또는 해시\((.*?)\), \(ii\)", text, re.S)
    if not m:
        print("  BAD  §2.8의 (i) 목록을 찾지 못했다"); return 1
    names = re.findall(r"`([A-Za-z_.0-9]+)`", m.group(1))   # 이름에 숫자가 있다(`sha256`) — 첫 판의 정규식이 그 둘을 빠뜨렸다
    # 스펙 키: 최소 입력으로 한 번 만든다
    spec_keys = set(analysis_input_id(
        {"schema_version": "x", "contract_version": "x", "core_tool_version": "x", "history_backend": {"name": "jgit", "git_version": None},
         "component": {"strategy": "auto", "algorithm_version": "auto-1", "split_share_basis": "class_count"},
         "algorithm_versions": {}, "parameters": {"window.months": 12, "window.max_commits": 2000}},
        {}, [], {"commit_shas": [], "head_committer_time": canonical_time(0), "last_commit_map": {}})[1])
    checks, bad = [], 0
    for n in names:
        key = I_TO_SPEC.get(n)
        ok = key is not None and key in spec_keys
        checks.append((f"(i) `{n}` → 스펙 `{key}`" if key else f"(i) `{n}` → 표에 없다", ok))
        bad += 0 if ok else 1
    unmapped = sorted(spec_keys - set(I_TO_SPEC.values()))
    checks.append((f"스펙 키가 전부 (i)의 이름에 대응한다" + (f" — 대응 없음 {unmapped}" if unmapped else ""), not unmapped))
    bad += 1 if unmapped else 0
    for name, ok in checks:
        print(f"  {'ok ' if ok else 'BAD'}  {name}")
    print(f"  (i)의 이름 {len(names)} · 스펙 키 {len(spec_keys)}")
    return 1 if bad else 0


def run_case(case_dir: Path) -> dict:
    inp = json.loads((case_dir / "input.json").read_text(encoding="utf-8"))
    if "canonical_vectors" in inp:
        return run_canonical_vectors(inp)
    if "repo_variants" in inp:
        return run_repo_variants(case_dir, inp)
    if "machines" in inp:
        return run_byte_identity(case_dir, inp)
    if "time_notations" in inp:
        return run_time_notations(inp)
    if "people_variants" in inp:
        return run_people_variants(case_dir, inp)
    if inp.get("recompute_from_reproduce"):
        return run_recompute_from_reproduce(case_dir, inp)
    if "measure_projections" in inp:
        return run_parameter_projection(case_dir, inp)
    if "backend_variants" in inp:
        return run_history_cache_projection(case_dir, inp)
    if "shallow_depth" in inp:
        return run_shallow_unshallow(case_dir, inp)
    if "transition_projection" in inp:
        return run_transition_cache(case_dir, inp)
    if "clone_depths" in inp:
        return run_clone_depths(case_dir, inp)
    tree = case_dir / inp["repo"]["tree"]
    files = tree_files(tree)
    rsid = repository_state_id(files)

    with tempfile.TemporaryDirectory() as tmp:
        history = build_history(tree, inp["repo"], Path(tmp) / "repo")

    runs = {}
    for name, run in inp["runs"].items():
        aid, _ = analysis_input_id(inp["shared_inputs"], run["environment"], files, history)
        runs[name] = {"environment": run["environment"],
                      "repository_state_id": rsid,
                      "analysis_input_id": aid}

    # 원칙 검사(D87): reproduce에 없는 입력을 바꿔도 두 id가 불변이어야 한다.
    changed_env = dict(os.environ)
    changed_env.update(inp.get("irrelevant_environment_change", {}))
    files_again = tree_files(tree)
    rsid_again = repository_state_id(files_again)
    aid_again, _ = analysis_input_id(
        inp["shared_inputs"], inp["runs"]["a"]["environment"], files_again, history)

    names = list(runs)
    a, b = runs[names[0]], runs[names[1]]
    return {
        "case": inp["case"],
        "generated_by": GENERATED_BY,
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "canonical_encoding": CANONICAL_ENCODING,
        "tree": {"file_count": len(files), "files": [{"path": p, "content_id": c} for p, c in files]},
        "history": history,
        "runs": runs,
        "assertions": {
            "repository_state_id_equal":
                a["repository_state_id"] == b["repository_state_id"],
            "analysis_input_id_differs":
                a["analysis_input_id"] != b["analysis_input_id"],
            "irrelevant_env_change_is_inert":
                rsid_again == rsid and aid_again == a["analysis_input_id"],
        },
    }


def render(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="§2.8 재현성 정체성 계약")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true", help="§2.8 (i)의 이름이 id 스펙에 전부 있는가")
    ap.add_argument("cases", nargs="*")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    dirs = sorted(p.parent for p in CASE_DIR.glob("*/input.json"))
    if args.cases:
        dirs = [p for p in dirs if p.name in set(args.cases)]
    if not dirs:
        print("케이스가 없다.")
        return 0

    failures = 0
    for case_dir in dirs:
        result = run_case(case_dir)
        bad = [k for k, v in result["assertions"].items() if not v]
        if bad:
            failures += 1
            print(f"FAIL  {case_dir.name}: 단언 실패 {bad} — §2.8 정체성 계약")
            continue
        text = render(result)
        target = case_dir / "expected.json"
        if args.check:
            current = target.read_text(encoding="utf-8") if target.exists() else None
            if current == text:
                print(f"ok    {case_dir.name}")
            else:
                failures += 1
                print(f"FAIL  {case_dir.name}: expected.json "
                      f"{'없음' if current is None else '다름'} — §2.8 정체성 계약")
                if current is not None:
                    import difflib
                    for line in list(difflib.unified_diff(
                            current.splitlines(), text.splitlines(),
                            fromfile="committed", tofile="recomputed",
                            lineterm="", n=1))[:30]:
                        print(f"      {line}")
        else:
            target.write_text(text, encoding="utf-8")
            print(f"wrote {case_dir.name}/expected.json")

    if failures:
        print(f"\n{failures}개 실패. 의도한 변경이면 §2.9의 fixture_change를 같은 커밋에.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
