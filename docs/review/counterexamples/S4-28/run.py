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


# S4-28 — D155-1(비율 4자리, 고정 스케일)과 G0 픽스처의 직렬화(끝나지 않는 유리수는 12자리, 끝나는 것은 정확값).
from decimal import ROUND_HALF_EVEN, Decimal
history = load("history", "contract/history/compute.py")
exact = load("exact", "contract/tools/exact.py")
got, _ = run_case(history, "author-facts-minor-threshold")
value = got["files"]["src/Boundary21.java"]["ownership_max_share"]          # 정확 유리수(19/21)
d155 = format((Decimal(value.numerator) / Decimal(value.denominator)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN), "f")
fixture_text, _terminating = exact.decimal_text(value)
print(json.dumps({"key": "S4-28", "values": {"D155-1 비율 4자리": d155, "G0 픽스처의 직렬화": fixture_text},
                  "exact": f"{value.numerator}/{value.denominator}"}, ensure_ascii=False))
