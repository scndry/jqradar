import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sc = load("schema_compute", "contract/schema/compute.py")
BLOCKS = sc.prd_blocks((ROOT / "prd.md").read_text(encoding="utf-8"))


def block(name: str):
    return json.loads(sc.strip_jsonc(sc.base_text(f"prd:§7:{name}", BLOCKS)))


# O4-13 — §3.5 "각 행에 `shared`·`chg_commits_a`·`chg_commits_b`·정적 의존 유무·`commit_granularity` 경고" vs §7·스키마
# (`commit_granularity`는 `population`에 하나, `hiddenCoupling`은 `additionalProperties: false`). history 계산기의 쌍 행은
# 행마다 `commit_granularity`를 싣는다(`hidden-coupling-sort-order`) — 그 모양을 §7 report의 숨은 결합 행에 실어 스키마에 묻는다.
import jsonschema
import shutil
import tempfile
history = load("history", "contract/history/compute.py")
inp = json.loads((ROOT / "contract" / "history" / "hidden-coupling-sort-order" / "input.json").read_text(encoding="utf-8"))
tmp = tempfile.mkdtemp()
try:
    got = history.build_expected(inp, Path(tmp) / "repo")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
row_has_granularity = "commit_granularity" in got["pairs"][0]
granularity = got["pairs"][0].get("commit_granularity")
doc = block("report")
V = jsonschema.Draft202012Validator(json.loads((ROOT / "schemas" / "report.schema.json").read_text(encoding="utf-8")))


def verdict(d):
    errs = sorted(V.iter_errors(d), key=lambda e: list(e.path))
    return "accept" if not errs else "reject at /" + "/".join(str(x) for x in errs[0].path)


per_row = copy.deepcopy(doc)
per_row["hidden_couplings"][0]["commit_granularity"] = granularity
print(json.dumps({"key": "O4-13", "values": {
    "§3.5 — 행마다 commit_granularity(history 계산기의 행 모양)": verdict(per_row),
    "§7 — 리포에 하나(population)": verdict(doc)},
    "history_row_has_commit_granularity": row_has_granularity}, ensure_ascii=False))
