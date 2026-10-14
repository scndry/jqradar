#!/usr/bin/env python3
"""계약 계산기들이 공유하는 정확 산술과 결정적 직렬화 (§2.5 산술 계약, D115·D121).

**계약이 아니다** — `contract/<계약>/`가 계약이고 여기는 그 계산기들이 쓰는 코드다.
한 곳에 두는 이유: 직렬화가 갈리면 같은 값이 다른 바이트가 되고, "두 머신 바이트 동일"
(§2.9 `reproducibility/`)이 계산기마다 다른 뜻이 된다.

두 규칙만 지킨다.

1. **부동소수점을 쓰지 않는다.** 비율·분위·비교는 `fractions.Fraction`(정확 유리수).
   IEEE-754 `double`은 계약 자신의 픽스처를 재현하지 못한다 — §2.5의 P90 예
   `[1..9,100]`은 계약이 `18.1`이라 적었는데 double로는 `18.099999999999966`이다.
2. **무리수는 크기 출력에만.** `sqrt`·`log2`처럼 유리수로 닫히지 않는 것은
   `Decimal`을 `MathContext(34, HALF_EVEN)`에 해당하는 정밀도로 쓰고, 파생은
   전정밀에서 하고 **반올림은 마지막에 한 번**만 한다(D121).
3. **인쇄는 표 `D155-1`을 따른다**(D275). 표의 이름인 필드(읽기는 스케일 린트와 같다 —
   `scaletable.py`)는 표의 스케일로 고정 인쇄(`setScale(n, HALF_EVEN)`, 후행 0 유지)하고,
   인쇄가 정확값이 아니면 정확 유리수를 옆 지도 `exact`에 둔다 — 반올림 전 값의 비교(정확 산술)를
   픽스처가 시험하는 자리가 그 지도다. 표에 없는 이름(픽스처의 중간 사실)은 표가 정하지 않는다:
   끝나는 십진수는 정확값 그대로, 아니면 12자리 + 같은 지도. 4차 S4-28이 이 규칙 전의 모양을
   잡았다 — `ownership_max_share` 19/21을 표는 `0.9048`로, 픽스처는 `0.904761904762`로 적었다.
"""

from __future__ import annotations

import json
import math
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from pathlib import Path

import scaletable

PRD = Path(__file__).resolve().parents[2] / "prd.md"

# D115 — √ 등 무리수 연산의 정밀도. `BigDecimal MathContext(34, HALF_EVEN)`에 맞춘다.
IRRATIONAL_PRECISION = 34

# 표 `D155-1`에 없는 이름 중 끝나는 십진수가 아닌 값을 인쇄할 자릿수. 이 경로를 타는 값은 `exact`에
# 정확 유리수로 함께 기록되므로 반올림이 계약을 흐리지 않는다.
NON_TERMINATING_PLACES = 12


def irrational(fn):
    """무리수 연산을 34자리 문맥에서 돌린다. `fn`은 인자 없는 호출 가능 객체."""
    with localcontext() as ctx:
        ctx.prec = IRRATIONAL_PRECISION
        return fn()


def log2(value: Decimal) -> Decimal:
    return irrational(lambda: value.ln() / Decimal(2).ln())


def sqrt(value: Decimal) -> Decimal:
    return irrational(lambda: value.sqrt())


def round_half_even(value: Decimal, places: int) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)


def scaled_text(fr: Fraction, places: int) -> str:
    """정확 유리수를 소수 `places`자리로 — HALF_EVEN, 후행 0 유지(`setScale(n, HALF_EVEN).toPlainString()`, §2.5).
    `Decimal` 나눗셈의 정밀도에 기대지 않고 유리수로 반올림한다(D115)."""
    q = fr * 10 ** places
    n = math.floor(q)
    rest = q - n
    if rest > Fraction(1, 2) or (rest == Fraction(1, 2) and n % 2 == 1):
        n += 1
    sign, n = ("-" if n < 0 else ""), abs(n)
    if places == 0:
        return f"{sign}{n}"
    digits = str(n).rjust(places + 1, "0")
    return f"{sign}{digits[:-places]}.{digits[-places:]}"


class Num:
    """JSON 수치 리터럴 하나. `text`가 파일에 그대로 들어간다 — float를 거치지 않는다."""

    __slots__ = ("text", "exact", "terminating")

    @classmethod
    def at_scale(cls, value, places: int, where: str) -> "Num":
        """표 `D155-1`의 이름인 필드 — 표의 스케일로 고정 인쇄한다(D275). 정수 행(0자리)의 이름에 정수가 아닌 값이 오면
        멈춘다 — 그 행의 뜻은 '정수여야 하는 이름'이다(D185)."""
        num = cls.__new__(cls)
        if isinstance(value, Decimal):
            # 무리수 크기(34자리, D121) — 반올림은 여기서 한 번. 정확 유리수가 없으므로 `exact`에 들지 않는다.
            num.exact, num.terminating = None, True
            num.text = format(round_half_even(value, places), "f")
            return num
        fr = Fraction(value)
        if places == 0 and fr.denominator != 1:
            raise ValueError(f"{where}: 표 D155-1의 정수 행 이름인데 값이 {fr} — 정수여야 한다(D185)")
        num.exact = fr
        num.text = scaled_text(fr, places)
        num.terminating = Fraction(num.text) == fr
        return num

    def __init__(self, value):
        if isinstance(value, Decimal):
            # 이미 반올림된 십진수. 그대로 인쇄한다.
            self.exact = None
            self.text = format(value, "f")
            self.terminating = True
        else:
            self.exact = value
            self.text, self.terminating = decimal_text(value)


def decimal_text(fr: Fraction) -> tuple[str, bool]:
    """유리수를 십진 텍스트로. 끝나는 십진수면 정확값, 아니면 반올림 + False."""
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
            return format(dec.quantize(Decimal(1).scaleb(-max(twos, fives))), "f"), True
        return format(dec.quantize(Decimal(1).scaleb(-NON_TERMINATING_PLACES),
                                   rounding=ROUND_HALF_EVEN), "f"), False


def wrap(value, table: dict | None = None, path: tuple = (), parent: dict | None = None):
    """`Fraction`·`Decimal` -> `Num`, 컨테이너는 재귀. 나머지는 그대로.

    `table`(표 `D155-1`, `scaletable.read_scale_table`)이 있으면 표의 이름인 필드는 표의 스케일로 인쇄한다(D275) —
    정수(`int`)도 스케일이 있는 행의 이름이면 후행 0을 붙여 적는다(`90`이 아니라 `90.00` — 린트의
    `integer_in_scaled_field`와 같은 규칙). `parent`는 스케일 린트와 같이 넘긴다 — 배열 원소는 배열을 담은 객체."""
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (Fraction, Decimal, int)):
        places = scaletable.scale_for(list(path), parent, table) if (table is not None and path) else None
        if places is not None and not (isinstance(value, int) and places == 0):
            return Num.at_scale(value, places, "/" + "/".join(map(str, path)))
        return Num(value) if isinstance(value, (Fraction, Decimal)) else value
    if isinstance(value, dict):
        return {k: wrap(v, table, path + (k,), value) for k, v in value.items()}
    if isinstance(value, list):
        return [wrap(v, table, path + (i,), parent) for i, v in enumerate(value)]
    return value


def collect_exact(node, path: str, out: dict[str, str]) -> None:
    """인쇄가 정확값이 아닌 모든 값의 정확 유리수 — 표의 스케일로 반올림된 것과 표 밖의 끝나지 않는 것 둘 다(D275)."""
    if isinstance(node, Num):
        if not node.terminating and node.exact is not None:
            out[path] = f"{node.exact.numerator}/{node.exact.denominator}"
    elif isinstance(node, dict):
        for k, v in node.items():
            collect_exact(v, f"{path}/{k}", out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            collect_exact(v, f"{path}/{i}", out)


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
        return "[\n" + ",\n".join(f"{pad_in}{render(v, indent + 1)}" for v in node) \
               + "\n" + pad + "]"
    raise TypeError(f"직렬화할 수 없는 타입: {type(node)!r}")


def finish(expected: dict, generated_by: str, table: dict | None = None) -> str:
    """`exact`와 `_fixture`를 붙여 최종 텍스트를 만든다. `table`이 없으면 리포의 prd.md에서 표 `D155-1`을 읽는다(D235)."""
    if table is None:
        table = scaletable.read_scale_table(PRD.read_text(encoding="utf-8"))
    wrapped = wrap(expected, table)
    exact_map: dict[str, str] = {}
    collect_exact(wrapped, "", exact_map)
    wrapped["exact"] = exact_map
    wrapped["_fixture"] = {
        "generated_by": generated_by,
        "arithmetic": "exact rational (fractions.Fraction); "
                      f"irrational magnitudes at {IRRATIONAL_PRECISION} digits HALF_EVEN",
        "serialization": (
            "표 D155-1의 이름인 필드는 표의 스케일로 고정 인쇄한다(HALF_EVEN, 후행 0 유지 — D275). "
            "표에 없는 이름은 끝나는 십진수면 정확값 그대로, 아니면 "
            f"소수점 {NON_TERMINATING_PLACES}자리 ROUND_HALF_EVEN. "
            "인쇄가 정확값이 아닌 모든 값의 정확 유리수를 exact에 함께 적는다. "
            "exact가 비어 있으면 이 파일 전체가 정확값이다."
        ),
    }
    return render(wrapped) + "\n"
