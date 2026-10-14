from __future__ import annotations

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


# S4-16 — team 모드에서 팀 매핑에 없는 저자의 커밋이 `team_count`에 어떻게 드는가. §2.1은 `team_count` = "이 파일을 만진 팀 수 —
# 매핑에서 3인 미만 팀을 `other`로 접은 뒤의 수"이고, 매핑에 없는 저자를 `unmapped`로 접는 문장(§2.7·D163)은 `individual`의
# `author_id`에 대한 것이며 `authors_unmapped`는 individual 전용이다(§2.1 표). 입력: `history/team-folding-k-threshold`(team 모드,
# 매핑 payments 4·platform 3·billing 1)에 매핑에 없는 저자 z를 더한다 — z만 만진 파일, payments의 a와 z가 만진 파일.
history = load("history", "contract/history/compute.py")
inp = json.loads((ROOT / "contract/history/team-folding-k-threshold/input.json").read_text(encoding="utf-8"))
inp = copy.deepcopy(inp)
inp["case"] = "S4-16-counterexample"
inp["repo"]["authors"]["z"] = {"name": "Author Z", "email": "z@example.invalid"}
start = max(c["at_seconds"] for c in inp["repo"]["commits"]) + 100000
added = [
    {"id": "ou-z", "at_seconds": start, "author": "z", "repeat": 2, "step_seconds": 3600,
     "message": "z -> src/OnlyUnmapped.java", "write": {"src/OnlyUnmapped.java": "class X { int v{id}; }\n"}},
    {"id": "pu-a", "at_seconds": start + 100000, "author": "a", "repeat": 2, "step_seconds": 3600,
     "message": "a -> src/PaymentsAndUnmapped.java", "write": {"src/PaymentsAndUnmapped.java": "class X { int v{id}; }\n"}},
    {"id": "pu-z", "at_seconds": start + 200000, "author": "z", "repeat": 1, "step_seconds": 3600,
     "message": "z -> src/PaymentsAndUnmapped.java", "write": {"src/PaymentsAndUnmapped.java": "class X { int v{id}; }\n"}},
]
inp["repo"]["commits"] += added
targets = ["src/OnlyUnmapped.java", "src/PaymentsAndUnmapped.java"]
inp["measure_files"] = inp["measure_files"] + targets

# 계산기는 이 입력을 정의하지 않는다 — 매핑 밖 저자에서 멈춘다(`key_of[...]`, "매핑 밖 저자는 이 픽스처가 만들지 않는다").
tmp = tempfile.mkdtemp()
try:
    history.build_expected(inp, Path(tmp) / "repo")
    calculator = "값을 냈다"
except KeyError:
    calculator = "정의 없음 — 매핑 밖 저자에서 KeyError"
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# 두 읽기 — 파일을 만진 저자(입력의 커밋 명세)에서 팀을 센다. k 접기는 매핑의 팀에만(둘 다 같은 규칙).
mapping = inp["people"]["team_mapping"]
team_of = {a: t for t, members in mapping.items() for a in members}
small = {t for t, m in mapping.items() if len(m) < history.K_THRESHOLD}
touched: dict[str, set] = {p: set() for p in targets}
for c in inp["repo"]["commits"]:
    for path in c["write"]:
        if path in touched:
            touched[path].add(c["author"])


def team_count(authors: set, unmapped_is_a_team: bool) -> int:
    teams = set()
    for a in authors:
        t = team_of.get(a)
        if t is None:
            if unmapped_is_a_team:
                teams.add("unmapped")
            continue
        teams.add("other" if t in small else t)
    return len(teams)


print(json.dumps({"key": "S4-16", "values": {
    "§2.1 글자 — '이 파일을 만진 팀 수': 매핑에 없는 저자는 어느 팀도 아니다": {p: team_count(touched[p], False) for p in targets},
    "D163의 접기(매핑에 없는 저자 → `unmapped`, '팀의 other와 같은 처리')를 team 모드에": {p: team_count(touched[p], True) for p in targets}},
    "history 계산기": calculator,
    "team 모드에서 매핑 밖 저자의 수를 적는 자리": "없음 — `authors_unmapped`는 individual 전용(§2.1 표)"},
    ensure_ascii=False))
