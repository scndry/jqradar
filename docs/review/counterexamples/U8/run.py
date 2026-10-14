from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# U8 — §2.8 (i)·§7은 `repository_state_id`와 `head`를 [id](id 입력)로 적는다. id 입력이면 `analysis_input_id`가 같은 두 스캔은
# 그 필드도 같아야 한다. reproducibility 계산기(§2.8의 id 스펙)로 두 스캔을 만들어 본다 — id는 같은데 필드가 다르면 그 필드는
# id 입력이 아니고(입력이 다른데 id가 같다), id 입력의 함수([fn])도 아니다(같은 입력에서 다른 값).
rc = load("reproducibility", "contract/reproducibility/compute.py")
base = json.loads((ROOT / "contract/reproducibility/same-tree-different-origin/input.json").read_text(encoding="utf-8"))
shared, env = base["shared_inputs"], base["environment"]
params = shared["parameters"]
scope = rc.DEFAULT_SOURCE_SCOPE
GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
           "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
T0 = 1767225600  # 2026-01-01T00:00:00Z


def git(wd: Path, *args, at: int | None = None):
    e = dict(GIT_ENV)
    if at is not None:
        e["GIT_AUTHOR_DATE"] = e["GIT_COMMITTER_DATE"] = f"@{at} +0000"
    subprocess.run(["git", "-C", str(wd), *args], env=e, check=True, capture_output=True)


def write(wd: Path, rel: str, text: str):
    (wd / rel).parent.mkdir(parents=True, exist_ok=True)
    (wd / rel).write_text(text, encoding="utf-8")


def scan(wd: Path) -> dict:
    """한 스캔의 `head`·`repository_state_id`(D223)·`analysis_input_id`(§2.8 스펙)."""
    rsid, kept = rc.state_id_d223(wd)
    files = [(p, rc.content_id((wd / p).read_bytes())) for p in kept]
    eligible = rc.eligible_files(files, scope, wd)
    hist = rc.history_facts(wd, [p for p, _ in eligible], params)
    aid, _ = rc.analysis_input_id({**shared, "source_scope": scope}, env, eligible, hist)
    return {"head": hist["head"], "repository_state_id": rsid, "analysis_input_id": aid}


def seed(wd: Path):
    git(wd, "init", "-q", "-b", "main")
    write(wd, "src/main/java/com/example/A.java", "package com.example;\nclass A { int a; }\n")
    write(wd, "README.md", "# sample\n")
    git(wd, "add", "-A"); git(wd, "commit", "-q", "-m", "seed", at=T0)


with tempfile.TemporaryDirectory() as tmp:
    # (1) repository_state_id — 같은 커밋, 작업트리의 README만 다르다(D223: 내용은 작업트리 바이트; README는 적격 소스가 아니다)
    wd = Path(tmp) / "rsid"
    wd.mkdir()
    seed(wd)
    clean = scan(wd)
    write(wd, "README.md", "# sample — edited, not committed\n")
    dirty = scan(wd)

    # (2) head — 같은 비머지 이력, 머지 HEAD의 메시지만 다르다(머지는 W 밖 — §2.7; 커미터 시각은 같다)
    heads = {}
    for name in ("m1", "m2"):
        w = Path(tmp) / name
        w.mkdir()
        seed(w)
        git(w, "checkout", "-q", "-b", "feature")
        write(w, "src/main/java/com/example/B.java", "package com.example;\nclass B { int b; }\n")
        git(w, "add", "-A"); git(w, "commit", "-q", "-m", "feature B", at=T0 + 86400)
        git(w, "checkout", "-q", "main")
        write(w, "src/main/java/com/example/A.java", "package com.example;\nclass A { int a; int a2; }\n")
        git(w, "add", "-A"); git(w, "commit", "-q", "-m", "main A", at=T0 + 2 * 86400)
        git(w, "merge", "-q", "--no-ff", "-m", f"merge feature ({name})", "feature", at=T0 + 3 * 86400)
        heads[name] = scan(w)

same_id_rsid = clean["analysis_input_id"] == dirty["analysis_input_id"]
same_id_head = heads["m1"]["analysis_input_id"] == heads["m2"]["analysis_input_id"]
print(json.dumps({"key": "U8", "values": {
    "§2.8 (i)·§7 [id] — analysis_input_id가 같은 두 스캔": {"repository_state_id": "같다", "head": "같다"},
    "reproducibility 계산기(§2.8의 id 스펙)": {
        "repository_state_id": ("다르다 — analysis_input_id 같음" if same_id_rsid and clean["repository_state_id"] != dirty["repository_state_id"]
                                else f"id {'같음' if same_id_rsid else '다름'}"),
        "head": ("다르다 — analysis_input_id 같음" if same_id_head and heads["m1"]["head"] != heads["m2"]["head"]
                 else f"id {'같음' if same_id_head else '다름'}")}},
    "scans": {"clean": clean, "dirty_readme": dirty, "merge_head_m1": heads["m1"], "merge_head_m2": heads["m2"]}},
    ensure_ascii=False))
