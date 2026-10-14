#!/usr/bin/env python3
"""§2.5 `reason` 사전 → `report.schema.json`의 `reason` 부분집합 (D188·D278).

사전은 `prd.md` §2.5의 표 **한 곳**에만 있다. 셋째 열 "오는 자리"는 `reason` **키**가 오는 자리만이고(D278 — 사유 키
없이 나타나는 null은 표 아래 문장이 가리킨다), 스키마의 자리별 허용 부분집합은 이 열에서 **생성된다** — 손으로 맞추면
표가 둘이 된다(4차 U4: 사전은 `no_bytecode @ arch_context`를 허용하고 스키마는 거부했다). 스케일 린트가 표 `D155-1`을
읽는 것(D235)의 짝이다.

이 모듈이 갖는 것은 **열거(`enum`)와 성분 이름 자리의 있음·없음**뿐이다. 설명(`description`)은 손으로 쓴다 — 다만 사유
목록을 다시 적지 않고 사전을 가리킨다(D236).

    python3 contract/schema/reasons.py            # 생성한 부분집합과 스키마의 차이를 인쇄
    python3 contract/schema/reasons.py --write    # 스키마에 쓴다
    python3 contract/schema/reasons.py --check    # 차이가 있으면 실패

동기화는 `contract/schema/reason-subsets-from-dictionary/`가, 생성기가 표를 읽는다는 것은
`contract/schema/reason-dictionary-place-added/`가 본다(셋째 열에 자리를 더하면 생성물이 바뀐다).

셋째 열의 자리 어휘(괄호 밖 `·`로 나눈다; 괄호 안의 " — " 뒤는 설명):
  성분                 모든 성분 — `percentile_population`의 일반 자리
  성분(`x`·…)          그 이름의 성분 자리. 일반 자리의 사유를 물려받는다
  렌즈                 H·Dx·F 셋
  렌즈(H·…)            그 렌즈들
  쌍(…)                `hidden_couplings`의 `static_dependency` 사유
  `arch_context`       파일의 `arch_context`
  `component`(…)       컴포넌트
**읽을 수 없는 자리는 멈춘다** — 조용히 건너뛰면 그 사유가 어느 자리에서도 거부된다(빈 생성은 모든 사유를 거부한다).
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PRD = ROOT / "prd.md"
SCHEMA = ROOT / "schemas" / "report.schema.json"

DICT_HEAD = "- **`reason` 사전**"
LENSES = ("H", "Dx", "F")
GENERIC = "percentile_population"


def read_dictionary(prd_text: str) -> list[tuple[str, str]]:
    """§2.5 사전의 행 — (이름, 셋째 열). 표를 찾지 못하거나 칸이 셋이 아니면 멈춘다."""
    lines = prd_text.split("\n")
    heads = [i for i, l in enumerate(lines) if l.startswith(DICT_HEAD)]
    if len(heads) != 1:
        raise ValueError(f"`reason` 사전의 머리 `{DICT_HEAD}`가 {len(heads)}개 — 하나를 기대했다")
    rows: list[tuple[str, str]] = []
    for line in lines[heads[0] + 1:]:
        st = line.strip()
        if not st.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in st.strip("|").split("|")]
        if cells[0] == "이름" or set(cells[0]) <= set("-: "):
            continue
        if len(cells) != 3:
            raise ValueError(f"`reason` 사전: 칸이 셋이 아닌 행 — {st[:80]!r}")
        m = re.fullmatch(r"`([a-z_]+)`", cells[0])
        if not m:
            raise ValueError(f"`reason` 사전: 첫 칸이 백틱 이름 하나가 아니다 — {cells[0]!r}")
        rows.append((m.group(1), cells[2]))
    if not rows:
        raise ValueError("`reason` 사전에 행이 없다")
    return rows


def _split_outside_parens(cell: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in cell:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                raise ValueError(f"닫는 괄호가 남는다 — {cell!r}")
        if ch == "·" and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if depth:
        raise ValueError(f"괄호가 닫히지 않았다 — {cell!r}")
    parts.append(cur)
    return [p.strip() for p in parts]


def parse_places(reason: str, cell: str) -> list[str]:
    """셋째 열 한 칸 → 스키마 자리 이름들. 성분 이름 자리는 `percentile_population.<x>`."""
    places: list[str] = []
    for part in _split_outside_parens(cell):
        m = re.fullmatch(r"(성분|렌즈|쌍)(?:\((.*)\))?", part)
        if m:
            kind, inner = m.group(1), (m.group(2) or "").split(" — ")[0].strip()
            if kind == "성분":
                names = re.findall(r"`([a-z_]+)`", inner)
                if inner and not names:
                    raise ValueError(f"`{reason}`: 성분 자리의 괄호에 이름이 없다 — {part!r}")
                places += [f"{GENERIC}.{n}" for n in names] or [GENERIC]
            elif kind == "렌즈":
                lenses = [x.strip() for x in inner.split("·")] if inner else list(LENSES)
                unknown = [x for x in lenses if x not in LENSES]
                if unknown:
                    raise ValueError(f"`{reason}`: 렌즈가 아니다 — {unknown} ({part!r})")
                places += [f"lens_percentiles.{x}" for x in lenses]
            else:
                places.append("hidden_couplings")
            continue
        if part == "`arch_context`":
            places.append("arch_context")
            continue
        if re.fullmatch(r"`component`(?:\(.*\))?", part):
            places.append("component")
            continue
        raise ValueError(f"`{reason}`: 읽을 수 없는 자리 {part!r} — 셋째 열의 자리 어휘(이 모듈의 머리)에 없다")
    return places


def generate(prd_text: str) -> dict[str, list[str]]:
    """자리 → 허용 사유(사전의 행 순서). `$defs.reason`은 사전의 이름 전부."""
    rows = read_dictionary(prd_text)
    names = [r for r, _ in rows]
    by_place: dict[str, set[str]] = {}
    for reason, cell in rows:
        for place in parse_places(reason, cell):
            by_place.setdefault(place, set()).add(reason)
    generic = by_place.get(GENERIC, set())
    for place in list(by_place):
        if place.startswith(GENERIC + "."):
            by_place[place] |= generic          # 성분 이름 자리는 일반 자리를 물려받는다
    out = {"$defs.reason": names}
    for place in sorted(by_place):
        out[place] = [r for r in names if r in by_place[place]]
    return out


# ── 스키마의 자리 ──────────────────────────────────────────────────────────────

def _pp(schema: dict) -> dict:
    return schema["$defs"]["file"]["properties"]["percentile_population"]


def _enum_node(schema: dict, place: str) -> dict:
    """그 자리의 `enum`을 가진 노드."""
    d, f = schema["$defs"], schema["$defs"]["file"]["properties"]
    if place == "$defs.reason":
        return d["reason"]
    if place == GENERIC:
        return _pp(schema)["additionalProperties"]["additionalProperties"]["allOf"][1]["properties"]["reason"]
    if place.startswith(GENERIC + "."):
        name = place.split(".", 1)[1]
        return _pp(schema)["properties"][name]["additionalProperties"]["allOf"][1]["properties"]["reason"]
    if place.startswith("lens_percentiles."):
        return f["lens_percentiles"]["properties"][place.split(".", 1)[1]]["allOf"][1]["properties"]["reason"]
    if place == "arch_context":
        return f["arch_context"]["properties"]["reason"]["allOf"][1]
    if place == "component":
        return d["component"]["properties"]["reason"]["allOf"][1]
    if place == "hidden_couplings":
        return d["hiddenCoupling"]["properties"]["reason"]["allOf"][1]
    raise KeyError(place)


def current(schema: dict) -> dict[str, list[str]]:
    """스키마가 지금 가진 자리별 허용 사유."""
    places = ["$defs.reason", GENERIC, "arch_context", "component", "hidden_couplings"]
    places += [f"lens_percentiles.{x}" for x in LENSES]
    places += [f"{GENERIC}.{n}" for n in _pp(schema).get("properties", {})]
    return {p: list(_enum_node(schema, p)["enum"]) for p in sorted(places)}


def drift(prd_text: str, schema: dict) -> list[dict]:
    """생성한 것과 스키마의 차이 — 자리마다 (생성, 스키마). 순서도 본다(생성물의 바이트가 같아야 diff 0)."""
    gen, cur = generate(prd_text), current(schema)
    out = []
    for place in sorted(set(gen) | set(cur)):
        if gen.get(place) != cur.get(place):
            out.append({"place": place, "generated": gen.get(place), "schema": cur.get(place)})
    return out


def write(prd_text: str, schema: dict) -> dict:
    """스키마에 생성한 부분집합을 쓴다. 성분 이름 자리는 생기고 사라진다 — 새 자리는 일반 자리의 모양을 본뜬다."""
    schema = copy.deepcopy(schema)
    gen = generate(prd_text)
    pp = _pp(schema)
    named = {p.split(".", 1)[1] for p in gen if p.startswith(GENERIC + ".")}
    props = pp.setdefault("properties", {})
    for name in sorted(set(props) - named):
        del props[name]
    for name in sorted(named - set(props)):
        node = copy.deepcopy(pp["additionalProperties"])
        node["description"] = (f"성분 `{name}`의 자리 — 허용 사유는 §2.5 사전의 셋째 열에서 생성된다"
                               "(D278, `contract/schema/reasons.py`).")
        props[name] = node                     # 있던 자리는 그 순서 그대로, 새 자리는 뒤에(이름순) — 생성이 diff를 키우지 않는다
    for place, reasons in gen.items():
        _enum_node(schema, place)["enum"] = reasons
    return schema


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    prd_text = PRD.read_text(encoding="utf-8")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    if args.write:
        SCHEMA.write_text(json.dumps(write(prd_text, schema), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    found = drift(prd_text, schema)
    for d in found:
        print(f"차이  {d['place']}: 생성 {d['generated']} · 스키마 {d['schema']}")
    if not found:
        print("ok    `reason` 부분집합 — 사전과 같다")
    return 1 if (found and args.check) else 0


if __name__ == "__main__":
    sys.exit(main())
