import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# U21 — D202-1의 "모든 배열"이 표의 덮음보다 넓다. D269가 id 입력 루트의 순서를 닫았고(`reproducibility/source-scope-roots-order-canonical`)
# "표에 없는 배열이 산출물에 나오면 순서 린트가 실패한다"를 더했다 — 그러나 §7 블록에는 표에 없는 배열이 여전히 있다. 두 값:
# (1) D269대로 표(prd.md의 D202-1 — 행의 첫 칸 백틱 이름)에 없는 배열을 세면 §7 블록이 거부된다, (2) §7 예시는 긍정 케이스라 통과해야 한다.
# 표의 이름은 prd.md에서 읽는다(D235의 모양) — 코드 속 목록이 아니다.
import re
sc = load("schema_compute", "contract/schema/compute.py")
prd = (ROOT / "prd.md").read_text(encoding="utf-8")
blocks = sc.prd_blocks(prd)
lines = prd.split("\n")
start = next(i for i, l in enumerate(lines) if "**배열 정렬 키 표 `D202-1`**" in l)
table_names = set()
for l in lines[start + 1:]:
    if not l.strip().startswith("|"):
        if table_names:
            break
        continue
    first = l.strip().strip("|").split("|")[0]
    table_names |= {n.split(".")[-1] for n in re.findall(r"`([A-Za-z_.]+)`", first)}   # `bytecode_scope.class_roots` → class_roots


def arrays(node, path, out):
    if isinstance(node, dict):
        for k, v in node.items():
            arrays(v, path + [k], out)
    elif isinstance(node, list):
        name = path[-1] if path and isinstance(path[-1], str) else None
        if name:
            out.add(name)
        for i, v in enumerate(node):
            arrays(v, path + [i], out)


not_in_table = {}
for b in blocks:
    found = set()
    arrays(json.loads(sc.strip_jsonc(sc.base_text(f"prd:§7:{b}", blocks))), [], found)
    missing = sorted(found - table_names)
    if missing:
        not_in_table[b] = missing
n = sum(len(v) for v in not_in_table.values())
print(json.dumps({"key": "U21", "values": {
    "D269 — 표에 없는 배열은 린트 실패": f"§7 블록 거부 — 표에 없는 배열 {n}개",
    "§7 예시 — 긍정 케이스": "통과해야 한다"},
    "not_in_table": not_in_table,
    "positional_string_array_in_keyless_row_scope": "classes_reproduction_inputs.compiler_args — 위치가 뜻(javac 인자), asc로 정렬하면 다른 명령"},
    ensure_ascii=False))
