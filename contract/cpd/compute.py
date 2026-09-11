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
        per_file[path] = {
            "file_tokens": total,
            "duplicated_ranges": [list(r) for r in merge_ranges(cross + selfd)],
            "union_dup_tokens": union,
            "dup_extent": Fraction(union, total) if total else None,
            "self_dup_tokens": span(selfd),
        }

    # §2.6 — `pair_dup_tokens(A,B)` = 발생 집합이 A·B를 모두 포함하는 클러스터들의
    # **A쪽** 구간 합집합(A = 경로 사전순 앞). 무순서 쌍이 한 값을 갖게 하는 규칙이다.
    pairs = []
    for i, a in enumerate(paths):
        for b in paths[i + 1:]:
            a_side = [(o["start_token"], o["end_token"])
                      for c in clusters
                      if a in c["files"] and b in c["files"]
                      for o in c["occurrences"] if o["path"] == a]
            if a_side:
                pairs.append({"a": a, "b": b, "pair_dup_tokens": span(a_side)})

    for path in paths:
        per_file[path]["twins"] = sum(
            1 for p in pairs if (p["a"] == path or p["b"] == path))

    return {
        "case": inp["case"],
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "parameters": inp["parameters"],
        "clusters": clusters,
        "rejected_clusters": rejected,
        "files": per_file,
        "duplication_pairs": pairs,
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
