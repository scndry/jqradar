#!/usr/bin/env python3
"""contract/reproducibility — §2.8 재현성 정체성 셋의 기대값 계산기 (G0).

이 계약은 **합성 리포**를 먹는다(§2.9): 트리는 커밋되고 git 이력은 스크립트가
결정적으로 만든다(커미터 이름·메일·시각 고정 → 커밋 SHA 고정). `analysis_input_id`의
입력에 창 안 커밋 SHA 목록과 `window_anchor`가 들어가므로(§2.8) 트리만으로는
전제가 닫히지 않는다 — 그래서 순수 수치 계약이 아니다.

    python3 contract/reproducibility/compute.py            # expected.json 재생성
    python3 contract/reproducibility/compute.py --check     # CI

**산술·해시는 정확값으로.** 부동소수점을 쓰지 않는다(D115).

미해결 — 아래 `CANONICAL_ENCODING` 참고.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parent
GENERATED_BY = "contract/reproducibility/compute.py"

# §2.8은 `analysis_input_id`의 **입력 목록**은 정하지만 그것을 바이트로 펴는
# **정규 인코딩**은 정하지 않는다. 해시는 인코딩에 의존하므로, 두 구현이 같은 입력에서
# 같은 id를 내려면 이것도 계약이어야 한다. 여기서는 아래를 선언하고 쓴다:
#   정렬된 키의 UTF-8 JSON, 구분자 (",", ":"), ensure_ascii=False -> sha256
# 이 케이스가 검사하는 성질(같은 트리 → 같은 repository_state_id, 다른 툴체인 →
# 다른 analysis_input_id)은 인코딩 선택과 무관하므로 케이스는 유효하다.
CANONICAL_ENCODING = "sorted-key compact UTF-8 JSON, separators=(',',':')"


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


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
    # `%cI`가 아니라 `%ct`(unix 초). git 버전에 따라 UTC를 `Z`로도 `+00:00`으로도
    # 써서 두 머신에서 문자열이 갈리고, 이 값은 `analysis_input_id`에 **해시로
    # 들어간다** — 그러면 같은 트리·같은 툴체인인데 id가 달라진다. 이 계약이
    # 막아야 할 바로 그것을 이 계산기가 하고 있었다(CI가 잡았다).
    head_time = datetime.fromtimestamp(
        int(git("show", "-s", "--format=%ct", "HEAD")), timezone.utc).isoformat()
    return {"commit_shas": shas, "head": shas[-1], "head_committer_time": head_time}


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
    }
    return sha256(spec), spec


def run_case(case_dir: Path) -> dict:
    inp = json.loads((case_dir / "input.json").read_text(encoding="utf-8"))
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
