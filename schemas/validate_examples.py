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
    ("fixture_change", None,             "`expected.json` 변경 커밋에 동반되는 기록"),
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


NEGATIVE = [
    ("event", "event.schema.json",
     "D48·D108 — 사건 파일에 이름·이메일·핸들을 저장할 수 없다",
     _set(["author_email"], "someone@example.com")),
    ("event", "event.schema.json",
     "D55 — 사건 파일에 코드 상태(원장 상태)를 저장할 수 없다",
     _set(["status"], "closed")),
    ("event", "event.schema.json",
     "D89 — validated_tree_id 없는 passed는 passed가 아니다",
     _delete(["validation", "validated_tree_id"])),
    ("event", "event.schema.json",
     "§5.5 — 쓰는 사건은 claimed·validation_passed·validation_failed뿐",
     _set(["validation", "result"], "merged")),
    ("validate", "validate.schema.json",
     "§6.3 5a·D89 — validated는 검증 입력 정체성을 요구한다",
     _delete(["validated_tree_id"])),
    ("validate", "validate.schema.json",
     "§6.3.5·D31 — equivalence_basis는 세 값뿐",
     _set(["equivalence_basis"], "by_construction")),
    ("campaign", "campaign.schema.json",
     "D112 — 앵커 봉인은 repository_state_id다",
     _delete(["anchor", "repository_state_id"])),
    ("campaign", "campaign.schema.json",
     "D78 — target_driven인데 목표가 없을 수 없다",
     _delete(["targets"])),
    ("gate", "gate.schema.json",
     "§5.3 — 게이트 결과 어휘는 PASS·WARN·FAIL·context_changed뿐",
     _set(["checks", 0, "result"], "BAD")),
    ("report", "report.schema.json",
     "§3.7·D34 — interpretation은 세 값뿐(판정 어휘 아님)",
     _set(["findings", 0, "interpretation"], "bad")),
    ("report", "report.schema.json",
     "§2.5·D38 — percentile_population.reason은 정해진 네 값뿐",
     _set(["files", 1, "percentile_population", "chg_commits", "reason"], "dunno")),
    ("report", "report.schema.json",
     "§2.5 — 백분위는 0..1이다",
     _set(["files", 0, "percentiles", "cx"], 97)),
    ("report", "report.schema.json",
     "§2.2 — 테스트 클래스는 그래프에 들어가지 않는다",
     _set(["reproduce", "bytecode_scope", "test_classes_included"], True)),
    ("report", "report.schema.json",
     "§2.5 — 분위 방법은 type-7 하나로 선언되어 있다",
     _set(["reproduce", "percentile_method", "quantile"], "type6")),
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
        "complexity": {
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
    ("§5.1 — 항목에 판정 단어를 둘 수 없다",
     lambda d: d["items"]["complexity"].update({"verdict": "worse"})),
    ("§5.1 — 항목은 value_base·value_head·delta를 갖는다",
     lambda d: d["items"]["complexity"].pop("delta")),
    ("§5.5 정본 어휘·D110 — validated는 원장 상태가 아니다",
     lambda d: d["touched_legacy_findings"][0].update({"status_before": "validated"})),
    ("§5.5 — anchor_class는 high·medium·low뿐",
     lambda d: d["touched_legacy_findings"][0].update({"anchor_class": "critical"})),
    ("§5.1·D48 — declared_ai_assistance는 true·false·unknown뿐(추론 없음)",
     lambda d: d.update({"declared_ai_assistance": "probably"})),
]


def run_change_selftest(validator_cls) -> int:
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

    for why, mutate in CHANGE_NEGATIVE:
        document = copy.deepcopy(CHANGE_SELFTEST)
        mutate(document)
        if list(validator.iter_errors(document)):
            print(f"ok(거부)  change: {why}")
        else:
            problems += 1
            print(f"HOLE      change: {why} — 스키마가 이 변조를 통과시켰다")
    return problems


def run_negative(blocks: dict, validator_cls) -> int:
    """변조본이 전부 거부되는지 본다. 통과해 버리면 그것이 실패다."""
    holes = 0
    for name, schema_file, why, mutate in NEGATIVE:
        document = json.loads(strip_jsonc(blocks[name]))
        mutate(document)
        schema = json.loads((SCHEMAS / schema_file).read_text(encoding="utf-8"))
        errors = list(validator_cls(schema).iter_errors(document))
        if errors:
            print(f"ok(거부)  {name}: {why}")
        else:
            holes += 1
            print(f"HOLE      {name}: {why} — 스키마가 이 변조를 통과시켰다")
    holes += run_change_selftest(validator_cls)
    print()
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
