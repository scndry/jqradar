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
sys.path.insert(0, str(CASE_DIR.parent / "tools"))
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
        when = (base + timedelta(seconds=spec["step_seconds"] * i)).isoformat()
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
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

    head_time = canonical_time(int(git("show", "-s", "--format=%ct", "HEAD")))
    return {"commit_shas": shas, "head": shas[-1], "head_committer_time": head_time,
            "unreachable_commit_count": len(unreachable)}


DEFAULT_PEOPLE = {"attribution": "off", "team_mapping_sha256": None}
K_THRESHOLD = 3  # §2.7·D161 — 팀 집계의 k 하한. 익명 집계에는 걸지 않는다(D162).


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
        "parameters": shared["parameters"],
        # D160 — 저작 정책은 산출물을 바꾸므로 id 입력이다. off에서도 들어간다(모드가
        # 무엇이었나도 재현의 일부). `parameters`와 별도인 이유는 B.6 — 조직이 적는 자리가 다르다.
        "people": shared.get("people", DEFAULT_PEOPLE),
    }
    return sha256(spec), spec


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

    def report_for(machine: dict) -> dict:
        # G0에는 측정 코드가 없다 — 산출물은 reproduce 블록과 그 결정적 함수들로 이뤄진
        # 최소 리포트다. 필드는 세 종류뿐(D158): [id] · [fn] · [x].
        return {
            "schema": shared["schema_version"],
            "reproduce": {
                "tool_version": shared["core_tool_version"],                      # [id]
                "schema_version": shared["schema_version"],                       # [id]
                "contract_version": shared["contract_version"],                   # [id]
                "scanned_at": canonical_time(machine["scanned_at_unix"]),         # [x]
                "algorithm_versions": shared["algorithm_versions"],               # [id]
                "window_anchor": spec["window_anchor"],                           # [id]
                "head": history["head"],                                          # [fn]
                "repository_state_id": rsid,                                      # [fn]
                "analysis_input_id": aid,                                         # [fn]
                "environment": env,                                               # [id]
                "classes_reproduction_inputs": machine["classes_reproduction_inputs"],  # [x]
                "history_backend": shared["history_backend"],                     # [id]
                "window_applied": {
                    "commits_in_window": len(history["commit_shas"]),             # [fn]
                    "commit_list_sha256": spec["commit_list_sha256"],             # [id]
                    "history_complete": True, "graft_boundary_shas": [],          # [fn]
                },
                "component": shared["component"],                                 # [id]
                "parameters": shared["parameters"],                               # [id]
                "canonical_encoding": CANONICAL_ENCODING,                         # [id]
            },
            "tree": {"file_count": len(files),
                     "files": [{"path": p, "content_id": c} for p, c in files]},  # [id]
        }

    reports = {name: report_for(m) for name, m in inp["machines"].items()}
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
        "assertions": {
            "comparison_targets_byte_identical": tgt_a == tgt_b,
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
    # D160 — `team_count`의 키 = (창 안 커밋의 저자 집합, attribution, team_mapping_sha256,
    # k 하한). 저자 집합은 창 안 커밋 목록의 함수이므로 이 픽스처는 `commit_list_sha256`을
    # 그 자리에 둔다(합성 이력의 저자는 하나다) — 정체를 키에 두지 않는다.
    if projection.get("people"):
        key["people"] = {k: people[k] for k in projection["people"]}
        key["k_threshold"] = K_THRESHOLD
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
    if "measure_projections" in inp:
        return run_parameter_projection(case_dir, inp)
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
    ap.add_argument("cases", nargs="*")
    args = ap.parse_args()

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
