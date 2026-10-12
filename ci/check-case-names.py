#!/usr/bin/env python3
"""D236 — §2.9 G0 행이 이름으로 가리키는 케이스가 `contract/<스위트>/`에 디렉터리로 있는가.

    python3 ci/check-case-names.py [prd.md]
    python3 ci/check-case-names.py --selftest

§2.9의 행은 케이스의 값을 다시 적지 않고 케이스 **이름**을 가리킨다(D236 — 문서 규칙 "한 사실은
한 자리에"). 가리키는 쪽을 택하면 가리킴이 끊기는 것을 잡는 장치가 함께 있어야 한다 — 이름만 남고
디렉터리가 없어도 문서는 멀쩡해 보인다(4차 S4-27: §2.9가 요구한 케이스가 디렉터리에 없었다).

읽는 규칙(§2.9 표 앞 문장):
  - 행 = `| \\`<스위트>/\\` | … | <게이트> |`. 게이트가 G0인 행만 본다 — G1 이후 행은 보지 않는다.
  - 행 안의 백틱 kebab-case(`a-b-c`)는 케이스 이름이다. 맨 이름은 그 행의 스위트, `<스위트>/<이름>`은
    그 스위트의 케이스다(스위트는 §2.9 표의 첫째 칸에서 읽는다 — 목록을 여기 두지 않는다).
  - G0 행 안의 뒤 게이트 케이스는 이름 바로 뒤에 `(G1)`처럼 게이트를 붙인다 — 그 이름은 보지 않는다.

이 검사가 보지 못하는 것: 행이 이름이 아니라 말로 적은 최소 케이스("언어 분리, 0 팽창")는 이름이
없으니 볼 수 없다. S4-27의 그 자리는 행이 이름을 적어야 이 검사에 들어온다.

검사도 틀릴 수 있으므로 자기 반례를 함께 둔다(`--selftest`, D131) — 무는지, 물지 말아야 할 것을
물지 않는지.
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROW_RE = re.compile(r"^\| `([a-z0-9-]+)/` \|")
TOKEN_RE = re.compile(r"`([^`]+)`(\((G\d+[a-z]?)\))?")
KEBAB = r"[a-z0-9]+(?:-[a-z0-9]+)+"
BARE_RE = re.compile(rf"^{KEBAB}$")
PREFIXED_RE = re.compile(rf"^([a-z0-9-]+)/({KEBAB})$")


def section_29(text: str) -> list[str]:
    lines = text.split("\n")
    starts = [i for i, l in enumerate(lines) if l.startswith("### 2.9 ")]
    if len(starts) != 1:
        raise SystemExit(f"§2.9 머리가 {len(starts)}개 — 하나를 기대했다")
    out = []
    for l in lines[starts[0] + 1:]:
        if l.startswith("#"):
            break
        out.append(l)
    return out


def check(text: str, contract: Path) -> tuple[list[str], int]:
    """(문제 목록, 본 이름 수). 문제가 없으면 빈 목록."""
    rows = []
    for l in section_29(text):
        m = ROW_RE.match(l)
        if m:
            gate = l.rstrip().rstrip("|").split("|")[-1].strip()
            rows.append((m.group(1), gate, l))
    if not rows:
        return ["§2.9에서 스위트 행을 하나도 읽지 못했다"], 0
    suites = {s for s, _, _ in rows}
    problems, seen = [], 0
    for suite, gate, line in rows:
        if gate != "G0":
            continue
        for m in TOKEN_RE.finditer(line):
            token, later_gate = m.group(1), m.group(3)
            if BARE_RE.match(token):
                where, name = suite, token
            else:
                pm = PREFIXED_RE.match(token)
                if not pm or pm.group(1) not in suites:
                    continue
                where, name = pm.group(1), pm.group(2)
            if later_gate:
                continue
            seen += 1
            if not (contract / where / name).is_dir():
                problems.append(f"`{suite}/` 행(G0)의 `{token}` — contract/{where}/{name}/ 가 없다")
    return problems, seen


# 자기 반례 — (이름, 기대 = 통과?, §2.9 원문, 만들 디렉터리)
SELFTEST = [
    ("01-present", True,
     "| `cpd/` | 겹침 `overlap-merge`, `self-dup` | G0 |",
     ["cpd/overlap-merge", "cpd/self-dup"]),
    ("02-missing-in-g0", False,
     "| `cpd/` | 겹침 `overlap-merge`, 없는 `no-such-case` | G0 |",
     ["cpd/overlap-merge"]),
    ("03-missing-in-g1-row", True,
     "| `cpd/` | `overlap-merge` | G0 |\n| `gate/` | `not-yet-built` | G1 |",
     ["cpd/overlap-merge"]),
    ("04-later-gate-marked", True,
     "| `cpd/` | 실측은 G1의 확인 픽스처(`cpd/kotlin-tokens`(G1)), `overlap-merge` | G0 |",
     ["cpd/overlap-merge"]),
    ("05-later-gate-unmarked", False,
     "| `cpd/` | 실측은 G1의 확인 픽스처(`cpd/kotlin-tokens`), `overlap-merge` | G0 |",
     ["cpd/overlap-merge"]),
    ("06-other-suite-only", False,
     "| `cpd/` | `window-bound-time` | G0 |\n| `history/` | `rename-tiebreak` | G0 |",
     ["history/window-bound-time", "history/rename-tiebreak"]),
    ("07-fields-and-paths-are-not-names", True,
     "| `history/` | `age_last_days`·`.git/shallow`·`src/main`·`truncated: false`, `rename-tiebreak` | G0 |",
     ["history/rename-tiebreak"]),
]


def selftest() -> int:
    print("자기 반례 — 검사가 무는지, 물지 말아야 할 것을 물지 않는지:")
    bad = 0
    for name, want_pass, table, dirs in SELFTEST:
        with tempfile.TemporaryDirectory() as tmp:
            contract = Path(tmp) / "contract"
            for d in dirs:
                (contract / d).mkdir(parents=True)
            text = f"## 2. x\n\n### 2.9 적합성 스위트\n\n| 계약 | 최소 케이스 | 게이트 |\n|---|---|---|\n{table}\n\n## 3. y\n"
            problems, _ = check(text, contract)
        got_pass = not problems
        ok = got_pass == want_pass
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:36} 기대={'pass' if want_pass else 'fail'}"
              + ("" if ok else f"  실제={'pass' if got_pass else 'fail'} {problems}"))
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if argv[1:] == ["--selftest"]:
        return selftest()
    prd = Path(argv[1]) if len(argv) > 1 else ROOT / "prd.md"
    problems, seen = check(prd.read_text(encoding="utf-8"), ROOT / "contract")
    print(f"§2.9 G0 행의 케이스 이름 검사 (D236) — {prd.name}")
    print(f"  본 이름 {seen} · 없는 디렉터리 {len(problems)}")
    for p in problems:
        print(f"  FAIL  {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
