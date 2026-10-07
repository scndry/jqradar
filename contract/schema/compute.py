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

# §7의 jsonc 블록 순서. `prd:§7:<이름>`으로 참조한다.
PRD_BLOCKS = ["report", "gate", "validate", "fixture_change", "campaign", "event", "ledger_row", "people"]

# D115 직렬화 스케일 — 경로 패턴 -> 허용 소수 자릿수. `*`는 한 단계 와일드카드.
# 스케일 표 `D155-1`(§2.5) — **필드 이름**으로 매긴다. 표에 없는 유리수 필드는 위반이다.
# 스케일은 고정이다: 자릿수가 많아도, 적어도(후행 0을 떼도) 위반이다 — "바이트 동일"은 파싱된
# 수가 아니라 직렬화된 텍스트에 대한 주장이라(§2.5) 0.38과 0.3800은 다른 바이트다.
# D185 — 표는 산출물 **8종 전부**의 유리수 필드를 들고 린트도 §7 블록 전부를 본다.
# 정수 행의 뜻은 "정수여야 하는 이름"이다: 정수 리터럴은 표와 무관하게 통과하되, 정수 행의 이름에
# 소수가 오면 위반이고(decimal_in_integer_field), 스케일이 있는 행의 이름에 정수 리터럴이 오면
# 후행 0을 뗀 것이라 위반이다(integer_in_scaled_field — "0.38이 아니라 0.3800").
SCALES_VERSION = "D155-1"
KIND_SCALE = {"integer": 0, "ratio": 4, "lens": 1, "lakos": 2, "elapsed_days": 2}
FIELD_KIND = {
    **{f: "integer" for f in (
        "cx", "loc", "file_tokens", "chg_commits", "chg_days", "churn", "fan_in", "twins",
        "active_twins", "shared", "union_dup_tokens", "self_dup_tokens", "Ca", "Ce", "CCD",
        "components", "n_ranked", "n_population", "valid_n", "unknown_n",
        "change_exposure_90d", "distinct_authors_90d", "team_count", "teams_folded",
        "authors_unmapped")},
    # D184 — '일'은 초/86400의 유리수, 표시 2자리(0.01일 = 14분).
    **{f: "elapsed_days" for f in ("age_last_days", "authors_window_days", "debt_age_days")},
    **{f: "ratio" for f in (
        "pct", "lens_pct", "dup_extent", "active_twin_ratio", "tc", "ownership_max_share",
        "minor_contributor_share", "I", "A", "D", "RACD",
        "delta", "changed_line_coverage")},                  # gate·validate (D185)
    **{f: "lens" for f in ("H", "Dx", "F", "composite", "priority")},
    **{f: "lakos" for f in ("ACD", "CCD_balanced", "NCCD", "nccd")},   # gate의 [base, head]는 소문자 그대로 (D185)
}
SUMMARY_KEYS = ("median", "iqr", "p90", "max")
# 요약 통계 행에 이름으로 든 것 — `median_files_per_commit`은 짝수면 .5라 2자리 (D185)
SUMMARY_NAMED = {"median_files_per_commit": 2,
                 "p90_all": 2}   # evidence의 P90(age_last_days) — 경과 시간의 요약, §0-40 보정


def scale_for(path: list, parent: dict | None = None) -> int | None:
    """경로의 유리수 필드에 배정된 스케일. 표에 없으면 None."""
    leaf = str(path[-1])
    if leaf.isdigit() and len(path) >= 2:
        # 배열 원소 — 이름은 배열의 키다(`gate`의 `nccd: [base, head]`, D185).
        return scale_for(path[:-1], parent)
    if leaf in SUMMARY_NAMED:
        return SUMMARY_NAMED[leaf]
    if leaf == "value" and isinstance(parent, dict) and "measure" in parent:
        # 증거의 `value`는 그 측정의 값이다 — 스케일도 그 측정의 것(표 적용, 확장 아님).
        kind = FIELD_KIND.get(str(parent["measure"]))
        return KIND_SCALE[kind] if kind else None
    if leaf in SUMMARY_KEYS and "spread" in [str(p) for p in path]:
        # 요약 통계는 대상 측정에 따른다(D155). `cx.java`처럼 언어 접미어가 붙을 수 있다.
        measure = str(path[-2]).split(".")[0]
        kind = FIELD_KIND.get(measure)
        # 경과 시간(일)의 요약도 2자리 — 대상 자체가 2자리 유리수다(D184).
        return {"integer": 2, "ratio": 4, "lens": 1, "elapsed_days": 2}.get(kind)
    if len(path) >= 2 and str(path[-2]) == "percentiles":
        return 4
    if len(path) >= 3 and str(path[-3]) == "percentiles":
        # D168 — 두 단계 기록 `percentiles.<field>.<population>`: 리프 키가 모집단 이름이어도
        # 값은 같은 `pct`다. 표의 이름은 경로에서 찾는다(§2.5 표 D155-1 아래 문장).
        return 4
    kind = FIELD_KIND.get(leaf)
    return KIND_SCALE[kind] if kind else None


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


def prd_blocks() -> dict[str, str]:
    text = PRD.read_text(encoding="utf-8")
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


def scale_violations(text: str) -> list[dict]:
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
            scale = scale_for(path, parent)
            if scale:
                found.append({"path": "/" + "/".join(map(str, path)), "literal": node,
                              "problem": "integer_in_scaled_field", "allowed_scale": scale})
        elif type(node) is _Dec:                       # 소수 리터럴. 문자열은 보지 않는다
            where = "/" + "/".join(map(str, path))
            got = decimals(node)
            scale = scale_for(path, parent)
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
        return (FINDING_KIND_ORDER.index(item["kind"]), -_num(item.get("priority")),
                item.get("file", item.get("path", "")), item["id"])
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
        return (item.get("file", item.get("path_head", "")),)
    if name == "teams":
        return (item["team"],)
    return None


def _num(x):
    from fractions import Fraction as _F
    return _F(0) if x is None else _F(str(x))


ORDERED_ARRAYS = ("files", "findings", "duplicate_clusters", "components", "cycles", "occurrences",
                  "duplication_pairs", "hidden_couplings", "break_candidates", "items", "teams", "members")
PAIR_ARRAYS = ("duplication_pairs", "hidden_couplings")


def order_violations(document) -> list[dict]:
    out = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, path + [k])
        elif isinstance(node, list):
            name = path[-1] if path else None
            # 표의 이름이 같아도 원소가 객체가 아니면 다른 배열이다 — `gate.json`의 `components: [41, 43]`(수 둘),
            # `campaign.json`의 `scope.components`(문자열). 객체 배열만 표의 키로 본다; `members`는 문자열 배열이다.
            is_rule_array = bool(node) and (
                (name == "members" and all(isinstance(x, str) for x in node))
                or (name != "members" and all(isinstance(x, dict) for x in node)))
            if name in ORDERED_ARRAYS and is_rule_array:
                if name == "members":
                    keys = [(m,) for m in node]
                else:
                    keys = [_order_key(name, it) for it in node]
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


def run_case(inp: dict, blocks: dict[str, str], validator_cls) -> dict:
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

    text = base_text(inp["base"], blocks)
    if inp.get("text_patch"):
        text = apply_text_patch(text, inp["text_patch"])

    if check == "scale_lint":
        violations = scale_violations(text)
        out["verdict"] = "reject" if violations else "accept"
        out["violations"] = violations
        return out

    if check == "order_lint":
        document = json.loads(text)
        if inp.get("patch"):
            document = apply_patch(document, inp["patch"])
        violations = order_violations(document)
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

    blocks = prd_blocks()
    dirs = sorted(p.parent for p in CASE_DIR.glob("*/input.json"))
    if args.cases:
        dirs = [p for p in dirs if p.name in set(args.cases)]

    failures, results = 0, []
    for case_dir in dirs:
        inp = json.loads((case_dir / "input.json").read_text(encoding="utf-8"))
        result = run_case(inp, blocks, Draft202012Validator)
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
