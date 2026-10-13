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


# S4-7 — D157의 시각 정규 표기(`YYYY-MM-DDTHH:MM:SSZ`)와 history 계산기가 인쇄하는 `window_anchor.timestamp`.
history = load("history", "contract/history/compute.py")
repro = load("reproducibility", "contract/reproducibility/compute.py")
got, _ = run_case(history, "anchor-fixed")
printed = got["window_anchor"]["timestamp"]
from datetime import datetime
canonical = repro.canonical_time(int(datetime.fromisoformat(printed).timestamp()))
print(json.dumps({"key": "S4-7", "values": {"D157 정규 표기": canonical, "history 계산기(isoformat)": printed}},
                 ensure_ascii=False))
