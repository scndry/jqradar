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


# S4-11 — §2.6은 자기 중복을 "분할로 읽는다"고 하지만 정의(D166)는 `union_dup_tokens ⊇ 교차 구간 ∪ 자기 중복 구간`이다.
# 자기 중복 클러스터가 교차 클러스터와 겹치는 입력에서 분할이면 성립해야 할 합이 성립하지 않는다.
cpd = load("cpd", "contract/cpd/compute.py")
inp = {
    "case": "S4-11-counterexample", "contract_refs": ["§2.6"], "what_this_pins": "반례 입력",
    "parameters": {"cpd.minimum_tokens": 100},
    "file_tokens": {"A.java": 1000, "B.java": 1000},
    "clusters": [
        {"token_hash": "x-mixed", "tokens": 150,
         "occurrences": [{"path": "A.java", "start_token": 0, "end_token": 150},
                         {"path": "B.java", "start_token": 0, "end_token": 150}]},
        {"token_hash": "y-self", "tokens": 150,
         "occurrences": [{"path": "A.java", "start_token": 100, "end_token": 250},
                         {"path": "A.java", "start_token": 300, "end_token": 450}]},
    ],
}
got = cpd.build_expected(inp)
a = got["files"]["A.java"]
cross = 150   # A의 교차 구간 [0,150) — 혼합 클러스터 x의 A쪽 발생
print(json.dumps({"key": "S4-11", "values": {"분할로 읽으면 union = self + 교차": a["self_dup_tokens"] + cross,
                                             "계산기(⊇) union_dup_tokens": a["union_dup_tokens"]},
                  "self_dup_tokens": a["self_dup_tokens"]}, ensure_ascii=False))
