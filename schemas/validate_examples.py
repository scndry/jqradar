#!/usr/bin/env python3
"""§7의 예시 JSON을 schemas/의 스키마로 검증한다.

§7의 예시는 장식이 아니라 픽스처다(D26) — 그러니 스키마와 어긋나면 둘 중
하나가 틀린 것이고, 어느 쪽인지 말할 수 있어야 한다.

    python3 schemas/validate_examples.py            # 검증
    python3 schemas/validate_examples.py --dump DIR # 추출한 예시를 파일로

예시는 ```jsonc 블록이라 주석을 벗겨야 JSON이 된다. 문자열 안의 `//`를
지우지 않도록 문자열 상태를 추적한다.

의존: jsonschema. 없으면 안내하고 2를 돌려준다 — G0에서 CI에 붙일 때
`requirements.txt`로 고정한다.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRD = ROOT / "prd.md"
SCHEMAS = ROOT / "schemas"

# §7의 블록 순서와 그 블록을 받는 스키마.
# `anchor`는 블록 바로 앞에 오는 본문에서 블록을 식별하는 표지다.
BLOCKS = [
    ("report",   "report.schema.json",   "재계산 검증 대상"),
    ("gate",     "gate.schema.json",     "`check`의 출력 `gate.json`"),
    ("validate", "validate.schema.json", "`validate`의 출력 `validate.json`"),
    ("fixture_change", "fixture_change.schema.json", "`expected.json` 변경 커밋에 동반되는 기록"),
    ("campaign", "campaign.schema.json", "`campaign.json`(조직 소유)"),
    ("event",    "event.schema.json",    "사건 파일"),
    ("ledger_row", None,                 "원장 뷰 한 행"),
]


def strip_jsonc(text: str) -> str:
    """`//` 주석만 벗긴다. 문자열 리터럴 안은 건드리지 않는다."""
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


def extract_blocks() -> list[tuple[str, str]]:
    """§7 본문에서 ```jsonc 블록을 순서대로 꺼낸다."""
    text = PRD.read_text(encoding="utf-8")
    start = text.index("\n## 7. ")
    end = text.index("\n### 7.1 ")
    section = text[start:end]
    found = re.findall(r"```jsonc\n(.*?)\n```", section, flags=re.DOTALL)
    if len(found) != len(BLOCKS):
        sys.exit(f"§7에서 jsonc 블록 {len(found)}개를 찾았는데 "
                 f"{len(BLOCKS)}개를 기대했다 — BLOCKS 표를 맞춰야 한다.")
    return [(name, body) for (name, _, _), body in zip(BLOCKS, found)]


# 하드룰을 깨는 변조. 스키마가 **반드시 거부해야** 하는 것들이다.
# 전부 통과하는 스키마는 아무것도 지키지 않는다 — 그래서 이 표가 있다.
# (대상, 설명, 변조 함수)
def _set(path: list, value):
    def apply(doc):
        node = doc
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
    return apply


def _delete(path: list):
    def apply(doc):
        node = doc
        for key in path[:-1]:
            node = node[key]
        del node[path[-1]]
    return apply


# 변조 표. 각 행은 (대상, 스키마, kind, 기구, 근거, 설명, 변조함수).
#
# kind 판정 기준 — **계약을 모르는 사람이 §7 예시만 보고 스키마를 써도 잡혔을까?**
#   "hard_rule"  아니오. 거부하려면 특정 하드룰·D번호를 알고 스키마에 구조를
#                넣었어야 한다(additionalProperties:false / not / if-then / const,
#                또는 어휘 자체가 하드룰인 enum).
#   "structural" 예. 타입·범위·required·전사한 enum이라 계약을 몰라도 잡힌다.
#
# 구조 오류만 잔뜩이면 스키마는 문법 검사이지 계약이 아니다(§2.9, D124).
NEGATIVE = [
    ("event", "event.schema.json", "hard_rule", "additionalProperties:false", "D48·D108",
     "사건 파일에 이름·이메일·핸들을 저장할 수 없다",
     _set(["author_email"], "someone@example.com")),
    ("event", "event.schema.json", "hard_rule", "additionalProperties:false", "D55·D61",
     "사건 파일에 코드 상태(원장 상태)를 저장할 수 없다",
     _set(["status"], "closed")),
    ("event", "event.schema.json", "hard_rule", "if/then", "D89",
     "validated_tree_id 없는 passed는 passed가 아니다",
     _delete(["validation", "validated_tree_id"])),
    ("event", "event.schema.json", "hard_rule", "enum(어휘가 계약)", "D72·D99",
     "머지는 쓰는 사건이 아니라 git 파생이다",
     _set(["validation", "result"], "merged")),
    ("validate", "validate.schema.json", "hard_rule", "if/then", "§6.3 5a·D89",
     "validated는 검증 입력 정체성 넷을 요구한다",
     _delete(["validated_tree_id"])),
    ("validate", "validate.schema.json", "structural", "enum(전사)", "D31",
     "equivalence_basis는 세 값뿐(by_construction은 v3.3에서 기각된 값)",
     _set(["equivalence_basis"], "by_construction")),
    ("campaign", "campaign.schema.json", "hard_rule", "required(중재된 필드)", "D112",
     "앵커 봉인은 repository_state_id다 — 세 절이 서로 다르게 적던 자리",
     _delete(["anchor", "repository_state_id"])),
    ("campaign", "campaign.schema.json", "hard_rule", "if/then", "D78",
     "target_driven인데 목표가 없을 수 없다",
     _delete(["targets"])),
    ("gate", "gate.schema.json", "hard_rule", "if/then", "D98",
     "context_changed는 nccd_increase 전용 — 다른 규칙의 판정 탈출구가 될 수 없다",
     _set(["checks", 0, "result"], "context_changed")),
    ("gate", "gate.schema.json", "structural", "enum(전사)", "§5.3",
     "게이트 결과 어휘는 PASS·WARN·FAIL·context_changed뿐",
     _set(["checks", 0, "result"], "BAD")),
    ("report", "report.schema.json", "hard_rule", "enum(어휘가 계약)", "D67·D34",
     "interpretation에 판정 어휘를 넣을 수 없다",
     _set(["findings", 0, "interpretation"], "bad")),
    ("report", "report.schema.json", "structural", "enum(전사)", "D38",
     "percentile_population.reason은 정해진 네 값뿐",
     _set(["files", 1, "percentile_population", "chg_commits", "reason"], "dunno")),
    ("report", "report.schema.json", "structural", "range", "§2.5",
     "백분위는 0..1이다",
     _set(["files", 0, "percentiles", "cx"], 97)),
    ("report", "report.schema.json", "hard_rule", "const", "§2.2",
     "테스트 클래스는 그래프에 들어가지 않는다",
     _set(["reproduce", "bytecode_scope", "test_classes_included"], True)),
    ("report", "report.schema.json", "hard_rule", "const", "D114",
     "분위 방법은 모든 분위에 대한 단일 선언이다",
     _set(["reproduce", "percentile_method", "quantile"], "type6")),
    ("report", "report.schema.json", "hard_rule", "required", "D116·D122",
     "백분위의 분모(n_ranked)를 인쇄하지 않으면 pct를 재계산할 수 없다",
     _delete(["files", 0, "lens_percentiles", "H", "n_ranked"])),
    ("fixture_change", "fixture_change.schema.json", "hard_rule", "required(장치의 전부)", "P11·§2.9",
     "원인 분류 없는 fixture_change는 '새 정답을 손으로 승인하는 도장'이다",
     _delete(["fixture_change", "reason"])),
    ("fixture_change", "fixture_change.schema.json", "structural", "enum(전사)", "§2.9",
     "reason은 세 분류뿐",
     _set(["fixture_change", "reason"], "updated_expectation")),
]


# change.json은 §7에 예시가 없다 — §5.1은 표(질문 -> 계산)와 항목의 모양만 준다.
# 그래서 스키마를 검증할 문서가 없어, §5.1·§5.2·§5.7의 문장에서 직접 만든
# 최소 문서로 자체 점검한다. 이것은 PRD의 예시가 아니라 **스키마의 시험지**이며
# 픽스처가 아니다(contract/에 넣지 않는 이유).
CHANGE_SELFTEST = {
    "schema": "jqradar-change/1",
    "project": "sample-service",
    "base": {"ref": "origin/main", "sha": "base-sha"},
    "head": {"sha": "head-sha"},
    "items": {
        "complexity_delta": {
            "value_base": 18420, "value_head": 18512, "delta": 92,
            "evidence": [{"file": "f:order-service", "measure": "cx",
                          "value_base": 80, "value_head": 87, "delta": 7}]
        },
        "new_duplication": {
            "value_base": 0, "value_head": 1, "delta": 1,
            "evidence": [{"path_head": "…/NewCopy.java",
                          "path_base_mapped": None,
                          "cluster_id": "dup:<token_hash>:120", "tokens": 120}]
        }
    },
    "declared_ai_assistance": "unknown",
    "touched_legacy_findings": [
        {"id": "fnd:dx:dup:3f9a…:120@…/OrderService.java",
         "anchor_class": "high", "status_before": "open",
         "delta": {"union_dup_tokens": -120},
         "status_after_if_merged": "improving",
         "claimed_by_this_pr": False}
    ]
}

CHANGE_NEGATIVE = [
    ("hard_rule", "not", "§5.1·B.2", "항목에 판정 단어를 둘 수 없다",
     lambda d: d["items"]["complexity_delta"].update({"verdict": "worse"})),
    ("hard_rule", "additionalProperties:false", "D120",
     "items의 키는 여섯으로 닫힌다 — 이름 없는 항목은 계약이 아니다",
     lambda d: d["items"].update({"vibe_check": {"value_base": 1, "value_head": 2, "delta": 1}})),
    ("structural", "required", "§5.1", "항목은 value_base·value_head·delta를 갖는다",
     lambda d: d["items"]["complexity_delta"].pop("delta")),
    ("hard_rule", "enum(어휘가 계약)", "D110",
     "validated는 PR 검증 결과이지 원장 상태가 아니다",
     lambda d: d["touched_legacy_findings"][0].update({"status_before": "validated"})),
    ("hard_rule", "required", "D117",
     "claimed_by_this_pr은 필수 — 선택이면 전이 귀속과 어긋난다",
     lambda d: d["touched_legacy_findings"][0].pop("claimed_by_this_pr")),
    ("structural", "enum(전사)", "§5.5", "anchor_class는 high·medium·low뿐",
     lambda d: d["touched_legacy_findings"][0].update({"anchor_class": "critical"})),
    ("hard_rule", "enum(어휘가 계약)", "D48",
     "declared_ai_assistance는 선언된 것만 — 'probably'는 추론이다",
     lambda d: d.update({"declared_ai_assistance": "probably"})),
]


def run_change_selftest(validator_cls, tally) -> int:
    import copy
    schema = json.loads((SCHEMAS / "change.schema.json").read_text(encoding="utf-8"))
    validator = validator_cls(schema)
    problems = 0

    errors = list(validator.iter_errors(CHANGE_SELFTEST))
    if errors:
        problems += 1
        print("FAIL      change: §5.1에서 만든 최소 문서가 스키마를 통과하지 못한다")
        for err in errors:
            print(f"            /{'/'.join(str(p) for p in err.absolute_path)}: {err.message}")
    else:
        print("ok        change: §5.1 최소 문서 통과")

    for kind, mech, ref, why, mutate in CHANGE_NEGATIVE:
        document = copy.deepcopy(CHANGE_SELFTEST)
        mutate(document)
        tally.append((kind, "change", mech, ref, why))
        if list(validator.iter_errors(document)):
            print(f"ok(거부)  [{kind:10}] change  {ref:12} {why}  <- {mech}")
        else:
            problems += 1
            print(f"HOLE      [{kind:10}] change  {ref:12} {why} — 통과시켰다")
    return problems


def run_negative(blocks: dict, validator_cls) -> int:
    """변조본이 전부 거부되는지 본다. 통과해 버리면 그것이 실패다."""
    holes = 0
    tally: list[tuple] = []
    for name, schema_file, kind, mech, ref, why, mutate in NEGATIVE:
        document = json.loads(strip_jsonc(blocks[name]))
        mutate(document)
        schema = json.loads((SCHEMAS / schema_file).read_text(encoding="utf-8"))
        errors = list(validator_cls(schema).iter_errors(document))
        tally.append((kind, name, mech, ref, why))
        if errors:
            print(f"ok(거부)  [{kind:10}] {name:14} {ref:12} {why}  <- {mech}")
        else:
            holes += 1
            print(f"HOLE      [{kind:10}] {name:14} {ref:12} {why} — 통과시켰다")
    holes += run_change_selftest(validator_cls, tally)

    print()
    hard = [t for t in tally if t[0] == "hard_rule"]
    struct = [t for t in tally if t[0] == "structural"]
    print(f"변조 {len(tally)}종 = 하드룰 {len(hard)} + 구조 {len(struct)}")
    per: dict[str, list[str]] = {}
    for kind, target, mech, ref, _ in tally:
        per.setdefault(target, []).append(kind)
    print("스키마별 (하드룰/전체):")
    for target in sorted(per):
        kinds = per[target]
        mark = "" if any(k == "hard_rule" for k in kinds) else "   <- 하드룰 변조 없음(D124 미충족)"
        print(f"  {target:16} {sum(1 for k in kinds if k == 'hard_rule')}/{len(kinds)}{mark}")
    mechs: dict[str, int] = {}
    for kind, _, mech, _, _ in tally:
        if kind == "hard_rule":
            mechs[mech] = mechs.get(mech, 0) + 1
    print("하드룰을 잡은 기구:", ", ".join(f"{m} {c}" for m, c in sorted(mechs.items())))
    if holes:
        print(f"{holes}개 하드룰이 스키마에 반영되지 않았다.")
    else:
        print(f"변조 {len(NEGATIVE) + len(CHANGE_NEGATIVE)}종이 전부 거부되고 "
              "change 자체 점검도 통과했다 — 스키마에 이가 있다.")
    return holes


def main() -> int:
    ap = argparse.ArgumentParser(description="§7 예시를 schemas/로 검증")
    ap.add_argument("--dump", metavar="DIR", help="추출한 예시 JSON을 이 디렉터리에 쓴다")
    ap.add_argument("--negative", action="store_true",
                    help="하드룰 변조본이 거부되는지 확인 (스키마에 이가 있는가)")
    args = ap.parse_args()

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("jsonschema가 없다:  python3 -m pip install jsonschema", file=sys.stderr)
        return 2

    blocks = dict(extract_blocks())
    if args.negative:
        return 1 if run_negative(blocks, Draft202012Validator) else 0
    dump_dir = Path(args.dump) if args.dump else None
    if dump_dir:
        dump_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for name, schema_file, label in BLOCKS:
        raw = strip_jsonc(blocks[name])
        try:
            document = json.loads(raw)
        except json.JSONDecodeError as exc:
            failures += 1
            print(f"FAIL  {name}: §7 블록이 JSON으로 파싱되지 않는다 — {exc}")
            continue

        if dump_dir:
            (dump_dir / f"{name}.json").write_text(
                json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        if schema_file is None:
            print(f"skip  {name}: 이 예시를 받는 스키마가 없다 ({label})")
            continue

        schema = json.loads((SCHEMAS / schema_file).read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path))
        if not errors:
            print(f"ok    {name}  <- {schema_file}")
            continue
        failures += 1
        print(f"FAIL  {name}  <- {schema_file}  ({len(errors)}건)")
        for err in errors:
            where = "/" + "/".join(str(p) for p in err.absolute_path)
            print(f"        {where}: {err.message}")

    print()
    if failures:
        print(f"{failures}개 블록이 스키마를 통과하지 못했다. "
              "§7 예시는 픽스처이므로(D26) 먼저 스키마를 의심하고, "
              "어느 쪽이 틀렸는지 PR 본문에 적는다.")
        return 1
    print("§7 예시 전부가 스키마를 통과한다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
