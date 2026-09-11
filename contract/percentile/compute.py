#!/usr/bin/env python3
"""contract/percentile — §2.5 백분위·분위 계약과 §3.7 confidence의 기대값 계산기.

`expected.json`을 손으로 쓰지 않기 위한 스크립트다(B.4, D26). 각 케이스의
`input.json`(전제, 손으로 쓴다)에서 `expected.json`(결론, 계산으로 만든다)을 낸다.

    python3 contract/percentile/compute.py            # expected.json 재생성
    python3 contract/percentile/compute.py --check    # 커밋된 것과 같은지 (CI)

산술은 전부 `fractions.Fraction`(정확 유리수)이다. IEEE-754 double로 §2.5의
픽스처 예를 그대로 평가하면 계약이 적은 18.1이 나오지 않는다:

    h    = 1 + 0.9*9        -> 9.099999999999999644729...
    Q    = 9 + (h-9)*(100-9) -> 18.09999999999996767...

정확 유리수로는 h = 91/10, Q = 9 + (1/10)*91 = 181/10 = 18.1로 계약과 일치한다.
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parent
GENERATED_BY = "contract/percentile/compute.py"

# 끝나는 십진수가 아닌 값을 인쇄할 자릿수. 이 경로를 타는 값은 expected.json의
# `non_terminating`에 정확 유리수로 함께 기록되므로 반올림이 계약을 흐리지 않는다.
NON_TERMINATING_PLACES = 12

# §3.7 confidence 임계
CONF_LOW_N = 50
CONF_HIGH_N = 200


# --------------------------------------------------------------------------
# §2.5 — 분위(quantile), type-7 선형 보간 (Hyndman-Fan)
# --------------------------------------------------------------------------

def quantile_type7(sorted_values: list[Fraction], q: Fraction) -> dict:
    """Q(q) = x_floor(h) + (h - floor(h)) * (x_floor(h)+1 - x_floor(h)), h = 1 + q*(N-1).

    반환값에 h·floor·frac을 함께 담는다 — 사람이 손으로 검산할 수 있게(§2.5 픽스처 예).
    """
    n = len(sorted_values)
    if n == 0:
        return {"n": 0, "h": None, "floor_h": None, "frac": None, "value": None}
    if n == 1:
        return {"n": 1, "h": Fraction(1), "floor_h": 1, "frac": Fraction(0),
                "value": sorted_values[0]}

    h = 1 + q * (n - 1)
    floor_h = h.numerator // h.denominator          # floor, h > 0
    frac = h - floor_h
    lo = sorted_values[floor_h - 1]                 # 1-indexed -> 0-indexed
    if floor_h >= n:                                # h == N (q == 1)
        value = sorted_values[n - 1]
        frac = Fraction(0)
    else:
        hi = sorted_values[floor_h]
        value = lo + frac * (hi - lo)
    return {"n": n, "h": h, "floor_h": floor_h, "frac": frac, "value": value}


def spread(sorted_values: list[Fraction], n_declared: int | None = None) -> dict:
    """§2.5 표시 규칙이 요구하는 모집단 분포 — 중앙값·IQR·최대.

    §2.5는 type-7을 'F의 P90'에 대해서만 명시하지만 median·IQR도 분위이고
    방법이 따로 적혀 있지 않다. `reproduce.percentile_method.quantile =
    "type7-linear"`를 단일 방법 선언으로 읽어 여기서도 type-7을 쓴다.
    (contract/percentile/README.md '미해결' 1번)
    """
    if not sorted_values:
        return {"min": None, "q1": None, "median": None, "q3": None,
                "iqr": None, "max": None, "valid_n": 0,
                "unknown_n": (n_declared or 0)}
    q1 = quantile_type7(sorted_values, Fraction(1, 4))["value"]
    med = quantile_type7(sorted_values, Fraction(1, 2))["value"]
    q3 = quantile_type7(sorted_values, Fraction(3, 4))["value"]
    out = {
        "min": sorted_values[0],
        "q1": q1,
        "median": med,
        "q3": q3,
        "iqr": q3 - q1,
        "max": sorted_values[-1],
        # §2.5 — 분위는 유효값만으로 계산한다(`P90(age_last_days)`는 유효 나이만).
        "valid_n": len(sorted_values),
    }
    if n_declared is not None and n_declared != len(sorted_values):
        out["unknown_n"] = n_declared - len(sorted_values)
    return out


# --------------------------------------------------------------------------
# §2.5 — 성분 백분위: 경험적 CDF, 동점 평균 순위
# --------------------------------------------------------------------------

def average_ranks(values: list[Fraction]) -> dict[Fraction, Fraction]:
    """동점 평균 순위. 같은 값은 그 값이 차지한 1-based 위치들의 평균을 받는다."""
    ordered = sorted(values)
    ranks: dict[Fraction, list[int]] = {}
    for position, value in enumerate(ordered, start=1):
        ranks.setdefault(value, []).append(position)
    return {v: Fraction(sum(ps), len(ps)) for v, ps in ranks.items()}


def percentiles(values_by_file: dict[str, Fraction | None],
                reasons_by_file: dict[str, str | None],
                min_population: int) -> tuple[dict[str, dict], int, int]:
    """pct(x) = (rank_avg(x) - 1) / (N - 1).

    N = 랭킹 집합(값이 null이 아닌 파일) 크기. N = 1 -> null(0/0),
    N < min_population -> null + reason insufficient_population.
    """
    ranked = {f: v for f, v in values_by_file.items() if v is not None}
    n_ranked = len(ranked)
    n_declared = len(values_by_file)
    ranks = average_ranks(list(ranked.values()))

    too_small = n_ranked < min_population or n_ranked <= 1
    out: dict[str, dict] = {}
    for file_id, value in values_by_file.items():
        if value is None:
            # 값이 없는 파일은 랭킹에서 빠진다. 이유는 케이스가 선언한다
            # (§2.5 reason enum: not_in_active | no_twins | age_unknown |
            #  insufficient_population) — "값이 null"과 "모집단 제외"의 구분(D38).
            out[file_id] = {"value": None, "rank_avg": None, "pct": None,
                            "reason": reasons_by_file.get(file_id)}
            continue
        rank_avg = ranks[value]
        if too_small:
            out[file_id] = {"value": value, "rank_avg": rank_avg, "pct": None,
                            "reason": "insufficient_population"}
        else:
            out[file_id] = {"value": value, "rank_avg": rank_avg,
                            "pct": (rank_avg - 1) / (n_ranked - 1), "reason": None}
    return out, n_ranked, n_declared


# --------------------------------------------------------------------------
# §3.7 — confidence
# --------------------------------------------------------------------------

def confidence(n: int, sp: dict, measure: str, granularity: str) -> tuple[str, list[str]]:
    """low <=> N < 50 v IQR = 0 v (median > 0 ^ IQR < 0.25*median)
             v (coarse ^ 성분 = chg_commits)
       high <=> N >= 200 ^ low 조건 없음;  그 외 medium.
    """
    reasons: list[str] = []
    if n < CONF_LOW_N:
        reasons.append("n_below_50")
    iqr, median = sp["iqr"], sp["median"]
    if iqr is not None and iqr == 0:
        # median = 0이면 아래의 IQR < 0.25*median은 0 < 0이 되어 무분산을 놓친다.
        reasons.append("iqr_zero")
    if median is not None and iqr is not None and median > 0 and iqr < median / 4:
        reasons.append("iqr_below_quarter_median")
    if granularity == "coarse" and measure == "chg_commits":
        reasons.append("coarse_commit_granularity")

    if reasons:
        return "low", reasons
    if n >= CONF_HIGH_N:
        return "high", []
    return "medium", []


# §3.7 interpretation — 렌즈 백분위만 쓴다(D34). 절대 임계가 아니다.
def interpretation(pct: Fraction | None) -> str | None:
    if pct is None:
        return None
    if pct >= Fraction(90, 100):
        return "investigate_first"
    if pct >= Fraction(75, 100):
        return "investigate"
    return "context"


# --------------------------------------------------------------------------
# 직렬화 — 정확 유리수를 십진 텍스트로. float를 거치지 않는다.
# --------------------------------------------------------------------------

class Num:
    """JSON 수치 리터럴 하나. `text`가 파일에 그대로 들어간다."""

    __slots__ = ("text", "exact", "terminating")

    def __init__(self, fr: Fraction):
        self.exact = fr
        self.text, self.terminating = _decimal_text(fr)


def _decimal_text(fr: Fraction) -> tuple[str, bool]:
    if fr.denominator == 1:
        return str(fr.numerator), True
    d, twos, fives = fr.denominator, 0, 0
    while d % 2 == 0:
        d //= 2
        twos += 1
    while d % 5 == 0:
        d //= 5
        fives += 1
    with localcontext() as ctx:
        ctx.prec = 80
        dec = Decimal(fr.numerator) / Decimal(fr.denominator)
        if d == 1:
            places = max(twos, fives)
            return format(dec.quantize(Decimal(1).scaleb(-places)), "f"), True
        q = dec.quantize(Decimal(1).scaleb(-NON_TERMINATING_PLACES),
                         rounding=ROUND_HALF_EVEN)
        return format(q, "f"), False


def wrap(value):
    """Fraction -> Num, 컨테이너는 재귀. None/str/bool/int는 그대로."""
    if isinstance(value, Fraction):
        return Num(value)
    if isinstance(value, dict):
        return {k: wrap(v) for k, v in value.items()}
    if isinstance(value, list):
        return [wrap(v) for v in value]
    return value


def collect_non_terminating(node, path: str, out: dict[str, str]) -> None:
    if isinstance(node, Num):
        if not node.terminating:
            out[path] = f"{node.exact.numerator}/{node.exact.denominator}"
    elif isinstance(node, dict):
        for k, v in node.items():
            collect_non_terminating(v, f"{path}/{k}", out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            collect_non_terminating(v, f"{path}/{i}", out)


def render(node, indent: int = 0) -> str:
    """결정적 JSON 직렬화. 키 순서는 삽입 순서(구성이 결정적이므로 재현된다)."""
    pad, pad_in = "  " * indent, "  " * (indent + 1)
    if isinstance(node, Num):
        return node.text
    if node is None:
        return "null"
    if node is True:
        return "true"
    if node is False:
        return "false"
    if isinstance(node, int):
        return str(node)
    if isinstance(node, str):
        return json.dumps(node, ensure_ascii=False)
    if isinstance(node, dict):
        if not node:
            return "{}"
        items = [f"{pad_in}{json.dumps(k, ensure_ascii=False)}: {render(v, indent + 1)}"
                 for k, v in node.items()]
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    if isinstance(node, list):
        if not node:
            return "[]"
        items = [f"{pad_in}{render(v, indent + 1)}" for v in node]
        return "[\n" + ",\n".join(items) + "\n" + pad + "]"
    raise TypeError(f"직렬화할 수 없는 타입: {type(node)!r}")


# --------------------------------------------------------------------------
# 케이스 실행
# --------------------------------------------------------------------------

def expand_runs(runs: list[dict]) -> dict:
    """큰 모집단을 손으로 쓰지 않기 위한 압축 표기.

    {"value": 0, "count": 151}      -> 0을 151개
    {"from": 10, "to": 500, "step": 10} -> 10, 20, ..., 500
    파일 id는 f0001부터 순서대로. 201개를 손으로 나열하는 것보다 감사하기 쉽다.
    """
    out: dict[str, Fraction] = {}
    index = 0
    for run in runs:
        if "count" in run:
            for _ in range(int(run["count"])):
                index += 1
                out[f"f{index:04d}"] = run["value"]
        else:
            step = run.get("step", Fraction(1))
            value = run["from"]
            while value <= run["to"]:
                index += 1
                out[f"f{index:04d}"] = value
                value += step
    return out


def values_of(block: dict) -> dict:
    """측정값 블록에서 {file_id: value} 원본을 꺼낸다 (`values` 또는 `runs`)."""
    if "values" in block:
        return block["values"]
    return expand_runs(block["runs"])


def normalise_values(raw: dict) -> tuple[dict[str, Fraction | None], dict[str, str | None]]:
    """값은 숫자, null, 또는 {"value": null, "reason": "..."} 형태를 받는다."""
    values: dict[str, Fraction | None] = {}
    reasons: dict[str, str | None] = {}
    for file_id, entry in raw.items():
        if isinstance(entry, dict):
            values[file_id] = entry.get("value")
            reasons[file_id] = entry.get("reason")
        else:
            values[file_id] = entry
            reasons[file_id] = None
    return values, reasons


def build_expected(inp: dict) -> dict:
    params = inp.get("parameters", {})
    min_population = int(params.get("percentile.min_population", 20))

    out: dict = {
        "case": inp["case"],
        "generated_by": GENERATED_BY,
        "contract_refs": inp["contract_refs"],
        "what_this_pins": inp["what_this_pins"],
        "parameters": inp.get("parameters", {}),
    }

    # --- 성분 백분위 (§2.5) -------------------------------------------------
    populations = {}
    for pop_name, pop in inp.get("populations", {}).items():
        granularity = pop.get("commit_granularity", "fine")
        measures = {}
        for measure, block in pop["measures"].items():
            values, reasons = normalise_values(values_of(block))
            pcts, n_ranked, n_declared = percentiles(values, reasons, min_population)
            sorted_valid = sorted(v for v in values.values() if v is not None)
            sp = spread(sorted_valid, n_declared)
            conf, conf_reasons = confidence(n_ranked, sp, measure, granularity)
            # D122 — 분모 이름은 성분·렌즈 공통 `n_ranked`.
            # 모집단 크기와 다를 때만 `n_population`을 병기한다(인쇄된 분모로
            # pct를 재계산할 수 있어야 한다 — B.4).
            entry = {
                "lang": block.get("lang"),
                "n_ranked": n_ranked,
                "spread": sp,
                "confidence": conf,
                "confidence_reasons": conf_reasons,
            }
            if n_declared != n_ranked:
                entry["n_population"] = n_declared
            if block.get("emit_percentiles", True):
                entry["percentiles"] = pcts
            measures[measure] = entry
        populations[pop_name] = {"commit_granularity": granularity, "measures": measures}
    if populations:
        out["populations"] = populations

    # --- 렌즈 백분위 (§2.5, D34) --------------------------------------------
    lenses = {}
    for lens_name, block in inp.get("lenses", {}).items():
        values, reasons = normalise_values(values_of(block))
        pcts, n_ranked, n_declared = percentiles(values, reasons, min_population)
        for file_id, row in pcts.items():
            row["interpretation"] = interpretation(row["pct"])
        # D116·D122 — `n_ranked`가 공식 `(rank_avg−1)/(N−1)`의 분모이며 필수.
        # 모집단 크기와 다를 때만 `n_population`을 병기한다.
        entry = {"population": block["population"], "n_ranked": n_ranked}
        if n_declared != n_ranked:
            entry["n_population"] = n_declared
        entry["files"] = pcts
        lenses[lens_name] = entry
    if lenses:
        out["lens_percentiles"] = lenses

    # --- 분위 질의 (§2.5 type-7) --------------------------------------------
    quantiles = []
    for query in inp.get("quantiles", []):
        if "values" in query:
            values = [v for v in query["values"] if v is not None]
        else:
            pop = inp["populations"][query["population"]]
            vals, _ = normalise_values(values_of(pop["measures"][query["measure"]]))
            values = [v for v in vals.values() if v is not None]
        result = quantile_type7(sorted(values), query["q"])
        quantiles.append({
            "id": query["id"],
            "population": query.get("population"),
            "measure": query.get("measure"),
            "q": query["q"],
            "valid_n": result["n"],
            "h": result["h"],
            "floor_h": result["floor_h"],
            "frac": result["frac"],
            "value": result["value"],
        })
    if quantiles:
        out["quantiles"] = quantiles

    return out


def render_case(case_dir: Path) -> str:
    with (case_dir / "input.json").open(encoding="utf-8") as fh:
        inp = json.load(fh, parse_float=Fraction, parse_int=Fraction)
    expected = wrap(build_expected(inp))

    non_terminating: dict[str, str] = {}
    collect_non_terminating(expected, "", non_terminating)
    expected["non_terminating"] = non_terminating
    expected["_fixture"] = {
        "arithmetic": "exact rational (fractions.Fraction)",
        "serialization": (
            "끝나는 십진수는 정확값 그대로. 그렇지 않은 값만 "
            f"소수점 {NON_TERMINATING_PLACES}자리 ROUND_HALF_EVEN으로 인쇄하고 "
            "정확 유리수를 non_terminating에 함께 적는다. "
            "non_terminating이 비어 있으면 이 파일 전체가 정확값이다."
        ),
    }
    return render(expected) + "\n"


def discover(cases: list[str] | None) -> list[Path]:
    found = sorted(p.parent for p in CASE_DIR.glob("*/input.json"))
    if cases:
        wanted = set(cases)
        found = [p for p in found if p.name in wanted]
        missing = wanted - {p.name for p in found}
        if missing:
            sys.exit(f"입력이 없는 케이스: {', '.join(sorted(missing))}")
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description="§2.5 백분위 계약 기대값 계산기")
    ap.add_argument("--check", action="store_true",
                    help="재생성 결과가 커밋된 expected.json과 같은지만 확인")
    ap.add_argument("cases", nargs="*", help="케이스 디렉터리 이름(비우면 전부)")
    args = ap.parse_args()

    failures = 0
    for case_dir in discover(args.cases):
        text = render_case(case_dir)
        target = case_dir / "expected.json"
        if args.check:
            current = target.read_text(encoding="utf-8") if target.exists() else None
            if current == text:
                print(f"ok    {case_dir.name}")
            else:
                failures += 1
                state = "없음" if current is None else "다름"
                print(f"FAIL  {case_dir.name}: expected.json {state} "
                      f"— §2.5 백분위·분위 계약 / §3.7 confidence")
        else:
            target.write_text(text, encoding="utf-8")
            print(f"wrote {case_dir.name}/expected.json")

    if failures:
        print(f"\n{failures}개 케이스가 재계산과 다르다. "
              "의도한 변경이면 §2.9의 fixture_change를 같은 커밋에 넣는다.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
