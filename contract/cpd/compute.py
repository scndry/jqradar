#!/usr/bin/env python3
"""contract/cpd — §2.6 CPD 집계 계약의 기대값 계산기 (G0).

    python3 contract/cpd/compute.py            # expected.json 재생성
    python3 contract/cpd/compute.py --check    # CI

**순수 수치·구조 계약**이라 `input.json` 하나로 전제가 완결된다(§2.9). git 이력도
소스 트리도 결과에 영향을 주지 않는다 — CPD가 낸 클러스터를 어떻게 파일·쌍으로
투영하는가가 계약의 전부다.

입력은 **CPD가 낸 것**(정규화 토큰 열의 발생 집합)이고, 출력은 §2.1이 쓰는 값들이다:
`union_dup_tokens`·`dup_extent`·`self_dup_tokens`·`twins`·`pair_dup_tokens`.
토큰 구간은 반개구간 `[start, end)`이며 길이는 `end − start`다(§2.6의 150 예가 그렇다).
"""

from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CASE_DIR.parent / "tools"))
import exact  # noqa: E402

GENERATED_BY = "contract/cpd/compute.py"


def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """겹치는 반개구간을 합친다. §2.6의 `[100,200) ∪ [150,250)` = 150이 이 규칙이다."""
    merged: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def span(ranges: list[tuple[int, int]]) -> int:
    return sum(end - start for start, end in merge_ranges(ranges))


def build_expected(inp: dict) -> dict:
    minimum_tokens = int(inp["parameters"]["cpd.minimum_tokens"])
    file_tokens = {k: int(v) for k, v in inp["file_tokens"].items()}

    clusters, rejected = [], []
    for raw in inp["clusters"]:
        tokens = int(raw["tokens"])
        occurrences = raw["occurrences"]
        entry = {
            "id": f"dup:{raw['token_hash']}:{tokens}",
            "tokens": tokens,
            "occurrences": [
                {"path": o["path"], "start_token": int(o["start_token"]),
                 "end_token": int(o["end_token"])}
                for o in occurrences
            ],
            "occurrence_count": len(occurrences),
            "files": sorted({o["path"] for o in occurrences}),
        }
        # §2.6 — `minimumTokens` 미만은 클러스터가 아니다. 거부도 기록한다:
        # "왜 이것이 중복이 아닌가"가 계약의 일부다.
        if tokens < minimum_tokens:
            entry["rejected_reason"] = "below_minimum_tokens"
            rejected.append(entry)
        else:
            # 발생이 한 파일에만 있으면 자기 중복 — twin이 아니다(§2.6).
            entry["self_duplication"] = len(entry["files"]) == 1
            clusters.append(entry)

    paths = sorted(file_tokens)
    per_file: dict[str, dict] = {}
    for path in paths:
        cross = [(o["start_token"], o["end_token"])
                 for c in clusters if not c["self_duplication"]
                 for o in c["occurrences"] if o["path"] == path]
        selfd = [(o["start_token"], o["end_token"])
                 for c in clusters if c["self_duplication"]
                 for o in c["occurrences"] if o["path"] == path]
        # `duplicated_ranges`는 그 파일의 **모든** 발생 구간 합집합이다(§2.6).
        union = span(cross + selfd)
        total = file_tokens[path]
        # D187 — 토큰을 세는 모든 수는 정규화 후 스트림의 것이라 분자(union)와 분모(file_tokens)가 같은
        # 스트림이고 `dup_extent ≤ 1`이 불변식이다. 입력이 그것을 어기면(union > file_tokens) 분모가 다른
        # 스트림이라는 뜻이므로 조용히 1을 넘기지 않고 멈춘다.
        if total and union > total:
            raise SystemExit(f"{inp['case']}: {path} union_dup_tokens {union} > file_tokens {total} — "
                             f"분자·분모가 같은 스트림이 아니다(§2.6, D187)")
        per_file[path] = {
            "file_tokens": total,
            "duplicated_ranges": [list(r) for r in merge_ranges(cross + selfd)],
            "union_dup_tokens": union,
            "dup_extent": Fraction(union, total) if total else None,
            "self_dup_tokens": span(selfd),
        }

    # §2.6·D199 — 쌍 측정은 **두 수**: `a_dup_tokens` = A·B를 모두 포함하는 클러스터들의 A쪽 구간 합집합,
    # `b_dup_tokens` = 같은 클러스터들의 B쪽 합집합(a < b는 경로 비교 — 코드 포인트 순 = UTF-8 바이트 순, D202).
    # 하나로 접지 않는다 — 혼합 클러스터에서 A쪽 200·B쪽 100처럼 두 수가 다르고, 사전순 앞쪽 하나만 내면
    # 개명이 수를 바꾼다(v3.10.4까지 이 계산기가 그랬다 — `pair_dup_tokens` = A쪽).
    pairs = []
    for i, a in enumerate(paths):
        for b in paths[i + 1:]:
            both = [c for c in clusters if a in c["files"] and b in c["files"]]
            a_side = [(o["start_token"], o["end_token"]) for c in both for o in c["occurrences"] if o["path"] == a]
            b_side = [(o["start_token"], o["end_token"]) for c in both for o in c["occurrences"] if o["path"] == b]
            if not both:
                continue
            a_tokens, b_tokens = span(a_side), span(b_side)
            # D200 — 쌍의 원소가 되는 클러스터는 양쪽에 ≥ minimum_tokens인 발생을 가지므로 한쪽이 0이면 다른 쪽도 0이다.
            # 입력이 그것을 어기면(길이 0 발생 등) 정의 밖이라 조용히 한쪽 0을 내지 않고 멈춘다.
            if (a_tokens == 0) != (b_tokens == 0):
                raise SystemExit(f"{inp['case']}: ({a}, {b}) 한쪽만 0 — a {a_tokens} · b {b_tokens}: "
                                 f"클러스터는 양쪽에 ≥ minimum_tokens인 발생을 갖는다(§2.6, D200)")
            pairs.append({"a": a, "b": b, "a_dup_tokens": a_tokens, "b_dup_tokens": b_tokens})

    # D200 — `twins(A)` = 쌍 측정이 0이 아닌 상대 파일 수, 어느 쪽 수든 같다.
    for path in paths:
        per_file[path]["twins"] = sum(
            1 for p in pairs if (p["a"] == path or p["b"] == path) and p["a_dup_tokens"] > 0)

    bite = None
    if inp.get("bite_one_sided"):
        # D200의 검사가 무는지 — 한쪽 발생의 길이를 0으로 만든 입력에서 멈춰야 한다(공집합의 통과는 증거가 아니다, D131).
        mutated = json.loads(json.dumps(inp)); mutated.pop("bite_one_sided")
        mutated["clusters"][0]["occurrences"][-1]["end_token"] = mutated["clusters"][0]["occurrences"][-1]["start_token"]
        try:
            build_expected(mutated); bite = {"one_sided_input_rejected": False}
        except SystemExit:
            bite = {"one_sided_input_rejected": True}

    return {
        "case": inp["case"],
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "parameters": inp["parameters"],
        "clusters": clusters,
        "rejected_clusters": rejected,
        "files": per_file,
        "duplication_pairs": pairs,
        # D187 — 분자·분모가 같은 정규화 후 스트림이라 dup_extent ≤ 1. 모든 케이스가 인쇄한다.
        "invariants": {
            "dup_extent_at_most_one": all(
                f["dup_extent"] is None or f["dup_extent"] <= 1 for f in per_file.values()),
            # D200 — 두 불변식: 한쪽 > 0 ⇔ 다른 쪽 > 0, 그래서 twins는 대칭이다.
            "pair_sides_both_positive_or_both_zero": all(
                (p["a_dup_tokens"] > 0) == (p["b_dup_tokens"] > 0) for p in pairs),
            "twins_symmetric": all(
                (p["a"] in {q["a"] for q in pairs if q["b"] == p["b"]} | {q["b"] for q in pairs if q["a"] == p["b"]})
                for p in pairs),
            **(bite or {}),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="§2.6 CPD 집계 계약")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("cases", nargs="*")
    args = ap.parse_args()

    dirs = sorted(p.parent for p in CASE_DIR.glob("*/input.json"))
    if args.cases:
        dirs = [p for p in dirs if p.name in set(args.cases)]

    failures = 0
    for case_dir in dirs:
        inp = json.loads((case_dir / "input.json").read_text(encoding="utf-8"))
        text = exact.finish(build_expected(inp), GENERATED_BY)
        target = case_dir / "expected.json"
        if args.check:
            current = target.read_text(encoding="utf-8") if target.exists() else None
            if current == text:
                print(f"ok    {case_dir.name}")
            else:
                failures += 1
                print(f"FAIL  {case_dir.name}: expected.json "
                      f"{'없음' if current is None else '다름'} — §2.6 CPD 집계 계약")
        else:
            target.write_text(text, encoding="utf-8")
            print(f"wrote {case_dir.name}/expected.json")

    if failures:
        print(f"\n{failures}개 실패. 의도한 변경이면 fixture_change를 같은 커밋에(§2.9·D129).")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
