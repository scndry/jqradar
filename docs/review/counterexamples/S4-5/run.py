import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_case(history, case: str) -> dict:
    """history 계산기를 그 케이스의 입력으로 돌린다 — 픽스처의 값을 낸 그 기계(반올림·직렬화 전)."""
    inp = json.loads((ROOT / "contract" / "history" / case / "input.json").read_text(encoding="utf-8"))
    tmp = tempfile.mkdtemp()
    try:
        return history.build_expected(inp, Path(tmp) / "repo"), inp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# S4-5 — §2.7의 창 W는 닫힌 구간 `[HEAD_TIME − months, HEAD_TIME]`인데 history 계산기는 아래 끝만 본다.
history = load("history", "contract/history/compute.py")
got, inp = run_case(history, "negative-age-invalid-metadata")
tmp = tempfile.mkdtemp()
try:
    workdir = Path(tmp) / "repo"
    history.build_repo(inp["repo"], workdir)
    commits = history.read_history(workdir)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
from datetime import datetime
head = int(datetime.fromisoformat(commits[0]["committer_time"]).timestamp())
earliest = head - int(inp["window"]["months"]) * history.MONTH_SECONDS
closed = [c for c in commits if not c["is_merge"]
          and earliest <= int(datetime.fromisoformat(c["committer_time"]).timestamp()) <= head]
reading_2_7 = {"commits_in_window": len(closed),
               "src/A.java chg_commits": sum(1 for c in closed if "src/A.java" in c["paths"])}
reading_calc = {"commits_in_window": got["window_applied"]["commits_in_window"],
                "src/A.java chg_commits": got["files"]["src/A.java"]["chg_commits"]}
print(json.dumps({"key": "S4-5", "values": {"§2.7 닫힌 위 끝(≤ HEAD_TIME)": reading_2_7,
                                            "history 계산기(아래 끝만)": reading_calc}}, ensure_ascii=False))
