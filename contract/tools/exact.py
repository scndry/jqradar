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
"""

from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction

# D115 — √ 등 무리수 연산의 정밀도. `BigDecimal MathContext(34, HALF_EVEN)`에 맞춘다.
IRRATIONAL_PRECISION = 34

# 끝나는 십진수가 아닌 값을 인쇄할 자릿수. 이 경로를 타는 값은 `non_terminating`에
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


class Num:
    """JSON 수치 리터럴 하나. `text`가 파일에 그대로 들어간다 — float를 거치지 않는다."""

    __slots__ = ("text", "exact", "terminating")

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


def wrap(value):
    """`Fraction`·`Decimal` -> `Num`, 컨테이너는 재귀. 나머지는 그대로."""
    if isinstance(value, (Fraction, Decimal)):
        return Num(value)
    if isinstance(value, dict):
        return {k: wrap(v) for k, v in value.items()}
    if isinstance(value, list):
        return [wrap(v) for v in value]
    return value


def collect_non_terminating(node, path: str, out: dict[str, str]) -> None:
    if isinstance(node, Num):
        if not node.terminating and node.exact is not None:
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
        return "[\n" + ",\n".join(f"{pad_in}{render(v, indent + 1)}" for v in node) \
               + "\n" + pad + "]"
    raise TypeError(f"직렬화할 수 없는 타입: {type(node)!r}")


def finish(expected: dict, generated_by: str) -> str:
    """`non_terminating`과 `_fixture`를 붙여 최종 텍스트를 만든다."""
    wrapped = wrap(expected)
    non_terminating: dict[str, str] = {}
    collect_non_terminating(wrapped, "", non_terminating)
    wrapped["non_terminating"] = non_terminating
    wrapped["_fixture"] = {
        "generated_by": generated_by,
        "arithmetic": "exact rational (fractions.Fraction); "
                      f"irrational magnitudes at {IRRATIONAL_PRECISION} digits HALF_EVEN",
        "serialization": (
            "끝나는 십진수는 정확값 그대로. 그렇지 않은 값만 "
            f"소수점 {NON_TERMINATING_PLACES}자리 ROUND_HALF_EVEN으로 인쇄하고 "
            "정확 유리수를 non_terminating에 함께 적는다. "
            "non_terminating이 비어 있으면 이 파일 전체가 정확값이다."
        ),
    }
    return render(wrapped) + "\n"
