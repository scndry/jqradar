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


# O4-33 — D202-1의 `findings` 키 "… · `priority desc` · `path asc` · `id asc`"에서 `path`는 finding에 없는 필드다.
# 두 읽기: (1) finding의 `file`(파일 id)로 비교 — 지금의 순서 린트(`contract/schema/compute.py`의 `_order_key`),
# (2) 그 id가 가리키는 `files[]`의 `path`로 비교. id 순서와 경로 순서가 다른 두 파일에서 같은 priority의 hotspot 둘.
doc = block("report")
files = [{"id": "f:alpha", "path": "src/Z.java"}, {"id": "f:zeta", "path": "src/A.java"}]
path_of = {f["id"]: f["path"] for f in files}
findings = [{"id": "fnd:h-1", "kind": "hotspot", "lens": "H", "file": "f:zeta", "priority": 90.0},
            {"id": "fnd:h-2", "kind": "hotspot", "lens": "H", "file": "f:alpha", "priority": 90.0}]
by_file_id = [f["id"] for f in sorted(findings, key=lambda f: sc._order_key("findings", f))]
by_path = [f["id"] for f in sorted(findings, key=lambda f: (sc.FINDING_KIND_ORDER.index(f["kind"]), -sc._num(f["priority"]),
                                                             path_of[f["file"]], f["id"]))]
# 둘째 갈림 — `gate.json` `items`의 키 `path_head asc` 하나: 한 경로에 새 발생이 둘이면(§5.2 "A 안의 둘째 사본") 전순서가 아니다.
items = [{"path_head": "src/A.java", "path_base_mapped": None, "cluster_id": "c-2", "tokens": 120},
         {"path_head": "src/A.java", "path_base_mapped": None, "cluster_id": "c-1", "tokens": 140}]
gate = block("gate")
lint = {}
for name, order in (("c-2 먼저", items), ("c-1 먼저", list(reversed(items)))):
    g = copy.deepcopy(gate)
    g["checks"] = [{"rule": "new_duplication", "result": "FAIL", "items": order}]
    lint[name] = "린트 통과" if not sc.order_violations(g) else "린트 거부"
print(json.dumps({"key": "O4-33", "values": {
    "findings — `file`(id)로 비교(지금의 린트)": by_file_id,
    "findings — `files[]`의 `path`로 비교": by_path},
    "items — 같은 path_head 둘의 두 순서": lint}, ensure_ascii=False))
