import copy
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# U4 — §2.5 reason 사전의 셋째 열("오는 자리")은 스키마의 if/then과 "같은 표"라고 단언한다. 사전이 허용한 (사유, 자리)를
# §7 report에 넣어 스키마에 물어본다. 대조군 하나(사전·스키마 둘 다 허용)가 통과해야 검사가 무는 것이다.
import jsonschema
sc = load("schema_compute", "contract/schema/compute.py")
doc = json.loads(sc.strip_jsonc(sc.base_text("prd:§7:report", sc.prd_blocks((ROOT / "prd.md").read_text(encoding="utf-8")))))
V = jsonschema.Draft202012Validator(json.loads((ROOT / "schemas" / "report.schema.json").read_text(encoding="utf-8")))


def verdict(patch):
    d = copy.deepcopy(doc)
    patch(d["files"][0])
    errs = sorted(V.iter_errors(d), key=lambda e: list(e.path))
    return "accept" if not errs else "reject at /" + "/".join(str(x) for x in errs[0].path)


cases = {
    # 사전: no_bytecode — "`arch_context` 전체 null"
    "no_bytecode @ arch_context": lambda f: f.update(arch_context={"I": None, "A": None, "D": None, "zone": None,
                                                                    "cycle_id": None, "reason": "no_bytecode"}),
    # 사전: unsupported_language — "성분(`cx`·`loc`·`smells`)"
    "unsupported_language @ percentile_population.loc": lambda f: f["percentile_population"].update(
        loc={"all": {"lang": "kotlin", "n_ranked": 0, "reason": "unsupported_language"}}),
    # 대조군 — 사전과 스키마가 같은 자리: unsupported_language @ cx
    "(대조) unsupported_language @ percentile_population.cx": lambda f: f["percentile_population"]["cx"]["all"].update(
        reason="unsupported_language"),
}
schema_says = {name: verdict(p) for name, p in cases.items()}

# 사전의 판정은 prd.md §2.5 표의 그 행에서 읽는다 — (사유, 자리)가 셋째 열에 있으면 허용.
prd_text = (ROOT / "prd.md").read_text(encoding="utf-8")


def dictionary_row(reason: str) -> str:
    rows = [l for l in prd_text.split("\n") if l.strip().startswith(f"| `{reason}` |")]
    assert len(rows) == 1, (reason, len(rows))
    return rows[0].strip().strip("|").split("|")[2]


place_of = {"no_bytecode @ arch_context": ("no_bytecode", "`arch_context`"),
            "unsupported_language @ percentile_population.loc": ("unsupported_language", "`loc`"),
            "(대조) unsupported_language @ percentile_population.cx": ("unsupported_language", "`cx`")}
dictionary_says = {name: ("accept" if place in dictionary_row(reason) else "reject")
                   for name, (reason, place) in place_of.items()}
print(json.dumps({"key": "U4", "values": {"§2.5 reason 사전(오는 자리)": dictionary_says, "report.schema.json": schema_says}},
                 ensure_ascii=False))
