#!/usr/bin/env python3
"""contract/schema — §7 산출물 스키마 7종의 적합성 케이스 (§2.9 `schema/` 행, D124).

케이스 하나 = `input.json`(전제, 손으로 쓴다) + `expected.json`(결론, 이 스크립트가 만든다).

    python3 contract/schema/compute.py            # expected.json 재생성
    python3 contract/schema/compute.py --check    # 커밋된 것과 같은지 (CI)

**전부 통과하는 스키마는 아무것도 지키지 않는다.** 그래서 케이스마다 `kind`를 달고
집계를 인쇄한다 — 하드룰을 겨눈 변조가 몇 개인지가 스키마가 계약인지 문법 검사인지를
가른다(D124).

  kind 판정 기준 — 계약을 모르는 사람이 §7 예시만 보고 스키마를 써도 잡혔을까?
    hard_rule   아니오. 특정 하드룰을 알고 구조를 넣었어야 한다
                (additionalProperties:false / not / if-then / const,
                 또는 어휘·사전 자체가 하드룰인 enum·pattern).
    structural  예. 타입·범위·required·전사한 enum이라 계약을 몰라도 잡힌다.

검사 종류(`check`):
  schema           JSON Schema 검증. 하드룰을 구조로 막는 층.
  scale_lint       **원문 텍스트** 린트(D125). 직렬화 스케일은 JSON Schema로 강제할 수
                   없다 — `multipleOf`가 이진 부동소수점에서 깨진다(`95.6 % 0.1` 거짓).
                   그래서 스키마에 `multipleOf`를 넣지 않고 텍스트로 본다. 읽을 때도
                   `double`을 경유하지 않는다(`parse_float=str`).
  vocabulary_sync  스키마에 심긴 판정 어휘 패턴이 사전과 같은지(D127).
  reason_sync      스키마의 `reason` 부분집합이 §2.5 사전의 셋째 열에서 생성한 것과 같은지(D278 — `reasons.py`).
                   `table_patch`가 있으면 사전 원문을 바꿔 생성한다 — 생성기가 표를 읽는다는 증거.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parent
ROOT = CASE_DIR.parent.parent
SCHEMAS = ROOT / "schemas"
PRD = ROOT / "prd.md"
GENERATED_BY = "contract/schema/compute.py"

sys.path.insert(0, str(CASE_DIR))
import vocabulary  # noqa: E402
import reasons  # noqa: E402  — D278: `reason` 부분집합은 §2.5 사전에서 생성된다

# §7의 jsonc 블록 순서. `prd:§7:<이름>`으로 참조한다.
PRD_BLOCKS = ["report", "gate", "validate", "fixture_change", "campaign", "event", "ledger_row", "people"]

# 스케일 표 `D155-1`(§2.5)의 읽기는 공용이다 — `contract/tools/scaletable.py`(D235; 픽스처 직렬화도 같은 읽기, D275).
sys.path.insert(0, str(ROOT / "contract" / "tools"))
from scaletable import SCALES_VERSION, read_scale_table, scale_for  # noqa: E402


class _Dec(str):
    """JSON **숫자** 리터럴(소수). 문자열 `"0.8"`(D156의 파라미터)과 구별하기 위한 표지."""


class _Int(str):
    """JSON **숫자** 리터럴(정수)."""



# --------------------------------------------------------------------------
# §7 블록 추출 (D128 전까지 §7이 원본이다)
# --------------------------------------------------------------------------

def strip_jsonc(text: str) -> str:
    out, in_string, escaped = [], False, False
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def prd_blocks(text: str) -> dict[str, str]:
    section = text[text.index("\n## 7. "):text.index("\n### 7.1 ")]
    found = re.findall(r"```jsonc\n(.*?)\n```", section, flags=re.DOTALL)
    if len(found) != len(PRD_BLOCKS):
        sys.exit(f"§7 블록 {len(found)}개 — {len(PRD_BLOCKS)}개를 기대했다.")
    return {name: strip_jsonc(body) for name, body in zip(PRD_BLOCKS, found)}


def base_text(spec: str, blocks: dict[str, str]) -> str:
    """`prd:§7:report` 또는 `file:base/change.json`."""
    if spec.startswith("prd:§7:"):
        return blocks[spec.split(":")[-1]]
    if spec.startswith("file:"):
        return (CASE_DIR / spec[len("file:"):]).read_text(encoding="utf-8")
    raise ValueError(f"알 수 없는 base: {spec}")


# --------------------------------------------------------------------------
# 변조
# --------------------------------------------------------------------------

def apply_patch(doc, patch: list[dict]):
    for step in patch:
        node = doc
        path = step["path"]
        for key in path[:-1]:
            node = node[key]
        if step["op"] == "set":
            node[path[-1]] = step["value"]
        elif step["op"] == "remove":
            del node[path[-1]]
        elif step["op"] == "append":
            # 배열 끝에 원소를 더한다 — 긍정 케이스가 §7에 없는 파일(Kotlin)을 두는 용도. 정렬 키(D202)는 호출자가 지킨다.
            node[path[-1]].append(step["value"])
        elif step["op"] == "swap":
            # 배열의 두 원소를 바꾼다 — 순서 린트의 변조용(D202). 값은 하나도 안 바뀌고 자리만 바뀐다.
            arr = node[path[-1]]
            arr[step["i"]], arr[step["j"]] = arr[step["j"]], arr[step["i"]]
        else:
            raise ValueError(f"알 수 없는 op: {step['op']}")
    return doc


def apply_text_patch(text: str, patch: list[dict]) -> str:
    for step in patch:
        if step["find"] not in text:
            raise ValueError(f"원문에 없는 조각: {step['find']!r}")
        text = text.replace(step["find"], step["replace"], 1)
    return text


# --------------------------------------------------------------------------
# D125 — 직렬화 스케일 린트 (원문 텍스트)
# --------------------------------------------------------------------------

def path_matches(path: list, rule: list) -> bool:
    if len(path) != len(rule):
        return False
    return all(r == "*" or r == str(p) for p, r in zip(path, rule))


def decimals(literal: str) -> int | None:
    """리터럴 원문의 소수 자릿수. 지수 표기는 None(허용하지 않는다)."""
    if "e" in literal or "E" in literal:
        return None
    return len(literal.split(".", 1)[1]) if "." in literal else 0


def scale_violations(text: str, table: dict) -> list[dict]:
    """`double`을 거치지 않고 리터럴 원문으로 검사한다(D125). 규칙은 표 `D155-1`(D155)."""
    doc = json.loads(text, parse_float=_Dec, parse_int=_Int)
    found: list[dict] = []

    def walk(node, path, parent=None):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, path + [k], node)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, path + [i], parent)
        elif type(node) is _Int:
            # D155·D185 — 스케일이 있는 행의 이름에 정수 리터럴이면 후행 0을 뗀 것이다(90 ≠ 90.00).
            scale = scale_for(path, parent, table)
            if scale:
                found.append({"path": "/" + "/".join(map(str, path)), "literal": node,
                              "problem": "integer_in_scaled_field", "allowed_scale": scale})
        elif type(node) is _Dec:                       # 소수 리터럴. 문자열은 보지 않는다
            where = "/" + "/".join(map(str, path))
            got = decimals(node)
            scale = scale_for(path, parent, table)
            if got is None:
                found.append({"path": where, "literal": node, "problem": "exponent_notation"})
            elif scale is None:
                found.append({"path": where, "literal": node, "problem": "unlisted_rational_field",
                              "note": f"표 {SCALES_VERSION}에 없는 유리수 필드"})
            elif scale == 0:
                found.append({"path": where, "literal": node, "problem": "decimal_in_integer_field"})
            elif got != scale:
                found.append({"path": where, "literal": node,
                              "allowed_scale": scale, "actual_scale": got})

    walk(doc, [])
    return found


# --------------------------------------------------------------------------
# 케이스 실행
# --------------------------------------------------------------------------

# ── 배열 순서 린트 (D202, 표 `D202-1`) ──────────────────────────────────────────────────
#
# 산출물의 모든 배열은 정해진 키로 정렬된다 — 배열은 순서가 바이트라(D154) 키가 없으면 두 머신이 다른
# 바이트를 낸다. JSON Schema는 원소 사이의 순서를 말하지 못하므로 **파싱 후 린트**다(스케일 린트와
# 같은 자리, 다른 축: 스케일은 원문 텍스트, 순서는 파싱된 배열). 문자열 비교는 유니코드 코드 포인트 순
# = UTF-8 바이트 사전순(§2.8 — 경로는 git 트리 바이트, 정규화 없음). Python의 `str` 비교가 그것이다.
# `gate.json`의 `checks`는 프로필 선언 순서(조직의 것, B.6)라 보지 않는다.
FINDING_KIND_ORDER = ("hotspot", "duplication_exposure", "frozen_core", "component_cycle", "hidden_coupling")
_SD_ORDER = {False: 0, True: 1, None: 2}


def _order_key(name: str, item):
    """표 `D202-1`의 키. 반환값끼리 비교해 오름차순이어야 한다. `tc desc`·`priority desc`는 음수로."""
    if name in ("files",):
        return (item["path"],)
    if name == "findings":
        # D268 — `path`는 finding에 없는 필드라 키가 아니다; `id`가 유일해 전순서다. `priority`가 없는 종류(순환·숨은 결합)는
        # kind가 먼저 갈리므로 그 칸을 0으로 두어도 다른 종류와 섞이지 않는다.
        return (FINDING_KIND_ORDER.index(item["kind"]), -_num(item.get("priority")), item["id"])
    if name in ("duplicate_clusters", "components", "cycles"):
        return (item["id"],)
    if name == "occurrences":
        return (item["path"], item["start_token"])
    if name == "duplication_pairs":
        return (item["a"], item["b"])
    if name == "hidden_couplings":
        return (_SD_ORDER[item.get("static_dependency")], -_num(item["tc"]), -item["shared"], item["a"], item["b"])
    if name == "break_candidates":
        return (item["from"], item["to"])
    if name == "items":
        # D268 — `new_duplication`의 새 발생은 (HEAD 경로, 시작 줄)로 유일하다(같은 파일의 둘째 사본).
        return (item.get("file", item.get("path_head", "")), item.get("start_line", 0))
    if name == "teams":
        return (item["team"],)
    return None


def _num(x):
    from fractions import Fraction as _F
    return _F(0) if x is None else _F(str(x))


ORDERED_ARRAYS = ("files", "findings", "duplicate_clusters", "components", "cycles", "occurrences",
                  "duplication_pairs", "hidden_couplings", "break_candidates", "items", "teams")


def read_order_table(prd_text: str) -> dict[str, set]:
    """D269·D235 — 표 D202-1을 **읽는다**(린트 안에 표의 사본을 두지 않는다). 행의 첫 칸의 백틱 이름이 표의 덮음이고,
    이름 → 종류 집합을 돌려준다: `string_asc`(키 없는 문자열 배열 행 — 이름이 든 것만), `positional`(위치 순서 행 — 원소의
    자리가 뜻이라 정렬하지 않는다), `rule_asc`(`rule asc` 행), `keyed`(그 밖의 행 — 키는 `_order_key`). 같은 이름이 두 행에
    들 수 있다(`components` — report의 객체 배열과 gate·validate의 `[base, head]` 수 둘) — 종류는 원소의 모양으로 가른다."""
    lines = prd_text.split("\n")
    start = next(i for i, l in enumerate(lines) if "**배열 정렬 키 표 `D202-1`**" in l)
    table: dict[str, set] = {}
    seen = False
    for l in lines[start + 1:]:
        st = l.strip()
        if not st.startswith("|"):
            if seen:
                break
            continue
        cells = [c.strip() for c in st.strip("|").split("|")]
        if cells[0] == "배열" or set(cells[0]) <= set("-: "):
            continue
        seen = True
        first, key = cells[0], (cells[1] if len(cells) > 1 else "")
        if "위치 순서" in first:
            kind = "positional"
        elif "키 없는 문자열 배열" in first:
            kind = "string_asc"
        elif "rule asc" in key:
            kind = "rule_asc"
        else:
            kind = "keyed"
        for name in re.findall(r"`([A-Za-z_.]+)`", first):
            if name.endswith(".json"):
                continue                      # 산출물 이름(`gate.json`)은 배열이 아니다
            table.setdefault(name.split(".")[-1], set()).add(kind)
    # `members`는 `cycles` · `members` · `break_candidates` 행의 `asc`(문자열 배열) — 그 행은 객체 배열과 함께 든다.
    if "members" in table:
        table["members"].add("string_asc")
    return table
PAIR_ARRAYS = ("duplication_pairs", "hidden_couplings")


def order_violations(document, table: dict[str, set] | None = None) -> list[dict]:
    """D202·D268·D269 — 배열마다 표 D202-1의 키로 정렬돼 있는가, 그리고 **표에 없는 배열이 없는가**(D269). `table`은
    `read_order_table(prd.md)` — 없으면 리포의 prd.md를 읽는다."""
    if table is None:
        table = read_order_table(PRD.read_text(encoding="utf-8"))
    out = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, path + [k])
        elif isinstance(node, list):
            name = path[-1] if path and isinstance(path[-1], str) else None
            kinds = table.get(name, set()) if name else set()
            if name and not kinds:
                out.append({"path": "/" + "/".join(map(str, path)), "array": name, "kind": "not_in_D202_1"})
            dicts = bool(node) and all(isinstance(x, dict) for x in node)
            strings = bool(node) and all(isinstance(x, str) for x in node)
            keys = None
            if strings and "string_asc" in kinds:
                # §2.8의 경로 비교 — UTF-8 바이트 사전순(D202·D269)
                keys = [(m.encode("utf-8"),) for m in node]
            elif dicts and "rule_asc" in kinds:
                keys = [(it.get("rule", ""),) for it in node]
            elif dicts and "keyed" in kinds and name in ORDERED_ARRAYS:
                keys = [_order_key(name, it) for it in node]
            # 그 밖 — 위치 순서(원소의 자리가 뜻), 선언 순서(`checks`·`targets`·`guardrails` — 조직의 것), 문자열·수가 객체
            # 행의 이름과 겹친 것(`campaign`의 `scope.components`·gate의 `components: [41, 43]`)은 순서를 보지 않는다.
            if keys is not None:
                for i in range(1, len(keys)):
                    if keys[i - 1] is not None and keys[i] is not None and keys[i - 1] > keys[i]:
                        out.append({"path": "/" + "/".join(map(str, path)), "index": i, "array": name,
                                    "kind": "not_sorted_by_D202_1", "previous": list(map(str, keys[i - 1])), "this": list(map(str, keys[i]))})
                if name in PAIR_ARRAYS:
                    for i, it in enumerate(node):
                        if not (it["a"] < it["b"]):
                            out.append({"path": "/" + "/".join(map(str, path + [i])), "array": name,
                                        "kind": "pair_not_ordered_a_lt_b", "a": it["a"], "b": it["b"]})
            for i, v in enumerate(node):
                walk(v, path + [i])

    walk(document, [])
    return out


def run_case(inp: dict, blocks: dict[str, str], validator_cls, prd_text: str, table: dict) -> dict:
    check = inp["check"]
    out = {
        "case": inp["case"],
        "generated_by": GENERATED_BY,
        "check": check,
        "kind": inp["kind"],
        "contract_ref": inp["contract_ref"],
        "what": inp["what"],
    }
    if inp.get("mechanism"):
        out["mechanism"] = inp["mechanism"]

    if check == "vocabulary_sync":
        drift = vocabulary.check()
        out["verdict"] = "reject" if drift else "accept"
        out["drifted_schemas"] = drift
        return out

    if check == "reason_sync":
        # D278 — 사전의 셋째 열에서 생성한 부분집합 = 스키마. 표를 바꾸면(`table_patch`) 생성물이 바뀌어야 한다 — 사본이었다면 그대로다.
        source = apply_text_patch(prd_text, inp["table_patch"]) if inp.get("table_patch") else prd_text
        found = reasons.drift(source, json.loads((SCHEMAS / "report.schema.json").read_text(encoding="utf-8")))
        out["verdict"] = "reject" if found else "accept"
        out["drift"] = found
        return out

    text = base_text(inp["base"], blocks)
    if inp.get("text_patch"):
        text = apply_text_patch(text, inp["text_patch"])

    if check == "scale_lint":
        if inp.get("table_patch"):
            # 표를 읽는다는 증거(D235): §2.5 표 원문을 바꾸면 린트가 바뀐다. 사본이었다면 그대로다.
            table = read_scale_table(apply_text_patch(prd_text, inp["table_patch"]))
        violations = scale_violations(text, table)
        out["verdict"] = "reject" if violations else "accept"
        out["violations"] = violations
        return out

    if check == "order_lint":
        document = json.loads(text)
        if inp.get("patch"):
            document = apply_patch(document, inp["patch"])
        violations = order_violations(document, read_order_table(prd_text))
        out["verdict"] = "reject" if violations else "accept"
        out["violations"] = violations
        return out

    if check == "schema":
        document = json.loads(text)
        if inp.get("patch"):
            document = apply_patch(document, inp["patch"])
        schema = json.loads((SCHEMAS / inp["schema"]).read_text(encoding="utf-8"))
        errors = sorted(validator_cls(schema).iter_errors(document),
                        key=lambda e: list(e.absolute_path))
        out["schema"] = inp["schema"]
        out["verdict"] = "reject" if errors else "accept"
        out["rejected_at"] = ["/" + "/".join(str(p) for p in e.absolute_path) for e in errors]
        return out

    raise ValueError(f"알 수 없는 check: {check}")


def render(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def tally(results: list[dict]) -> None:
    neg = [r for r in results if r["kind"] != "positive"]
    hard = [r for r in neg if r["kind"] == "hard_rule"]
    struct = [r for r in neg if r["kind"] == "structural"]
    pos = [r for r in results if r["kind"] == "positive"]
    print(f"\n케이스 {len(results)} = 긍정 {len(pos)} + 변조 {len(neg)}"
          f"(하드룰 {len(hard)} + 구조 {len(struct)})")

    by_schema: dict[str, list[str]] = {}
    for r in results:
        target = r.get("schema", r["check"]).replace(".schema.json", "")
        by_schema.setdefault(target, []).append(r["kind"])
    print("대상별 (하드룰/변조):")
    gaps = 0
    for target in sorted(by_schema):
        kinds = by_schema[target]
        n_hard = sum(1 for k in kinds if k == "hard_rule")
        n_neg = sum(1 for k in kinds if k != "positive")
        mark = ""
        if n_neg and not n_hard:
            mark = "   <- 하드룰 변조 없음 (D124 미충족)"
            gaps += 1
        print(f"  {target:16} {n_hard}/{n_neg}{mark}")
    if gaps:
        print(f"\n{gaps}개 대상이 D124를 채우지 못했다.")

    mechs: dict[str, int] = {}
    for r in hard:
        mechs[r.get("mechanism", "?")] = mechs.get(r.get("mechanism", "?"), 0) + 1
    print("하드룰을 잡은 기구:", ", ".join(f"{m} {c}" for m, c in sorted(mechs.items())))


def main() -> int:
    ap = argparse.ArgumentParser(description="§7 스키마 계약 케이스")
    ap.add_argument("--check", action="store_true", help="커밋된 expected.json과 대조만")
    ap.add_argument("cases", nargs="*")
    args = ap.parse_args()

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("jsonschema가 없다:  python3 -m pip install -r schemas/requirements.txt",
              file=sys.stderr)
        return 2

    prd_text = PRD.read_text(encoding="utf-8")
    blocks = prd_blocks(prd_text)
    table = read_scale_table(prd_text)
    dirs = sorted(p.parent for p in CASE_DIR.glob("*/input.json"))
    if args.cases:
        dirs = [p for p in dirs if p.name in set(args.cases)]

    failures, results = 0, []
    for case_dir in dirs:
        inp = json.loads((case_dir / "input.json").read_text(encoding="utf-8"))
        result = run_case(inp, blocks, Draft202012Validator, prd_text, table)
        results.append(result)

        expected_verdict = "accept" if inp["kind"] == "positive" else "reject"
        if result["verdict"] != expected_verdict:
            failures += 1
            print(f"FAIL  {case_dir.name}: {expected_verdict}를 기대했는데 "
                  f"{result['verdict']} — {inp['contract_ref']} {inp['what']}")
            continue

        text = render(result)
        target = case_dir / "expected.json"
        if args.check:
            current = target.read_text(encoding="utf-8") if target.exists() else None
            if current == text:
                print(f"ok    [{inp['kind']:10}] {case_dir.name}")
            else:
                failures += 1
                state = "없음" if current is None else "다름"
                print(f"FAIL  {case_dir.name}: expected.json {state} — §7 스키마 계약")
        else:
            target.write_text(text, encoding="utf-8")
            print(f"wrote [{inp['kind']:10}] {case_dir.name}")

    tally(results)
    if failures:
        print(f"\n{failures}개 케이스 실패. 의도한 변경이면 §2.9의 fixture_change를 같은 커밋에.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
