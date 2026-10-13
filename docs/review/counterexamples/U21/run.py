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


# U21 — D202-1의 '모든 배열'이 덮지 않는 키 없는 배열 중 id 입력인 `source_scope.main_roots`: 순서를 정하는 문장이 없으니
# 두 순서가 둘 다 허용된다(갈림). 같은 트리·같은 범위를 두 순서로 넣어 analysis_input_id를 계산한다.
repro = load("reproducibility", "contract/reproducibility/compute.py")
case = ROOT / "contract" / "reproducibility" / "same-tree-different-origin"
inp = json.loads((case / "input.json").read_text(encoding="utf-8"))
tree = case / inp["repo"]["tree"]
files = repro.tree_files(tree)
tmp = tempfile.mkdtemp()
try:
    history = repro.build_history(tree, inp["repo"], Path(tmp) / "repo")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
scope = inp["source_scope_variants"]["convention"]
ids = {}
for name, roots in (("main_roots 사전순", sorted(scope["main_roots"])),
                    ("main_roots 역순", sorted(scope["main_roots"], reverse=True))):
    s = {**scope, "main_roots": roots}
    aid, _ = repro.analysis_input_id({**inp["shared_inputs"], "source_scope": s}, inp["environment"],
                                     repro.eligible_files(files, s, tree), history)
    ids[name] = aid
print(json.dumps({"key": "U21", "values": ids}, ensure_ascii=False))
