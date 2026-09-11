#!/usr/bin/env python3
"""RFC 8785 JSON Canonicalization Scheme — `analysis_input_id`의 정규 인코딩 (§2.8, D138).

**계약이 아니다** — `contract/reproducibility/`가 계약이고 여기는 그 계산기가 쓰는 코드다.

해시는 바이트에 대한 것이므로 입력을 바이트로 펴는 방법이 계약이어야 한다(§2.8).
두 구현이 같은 입력에서 다른 바이트를 만들면 "두 머신 바이트 동일"이 그 자리에서 깨진다.

파이썬의 `json.dumps(sort_keys=True, ...)`와 **갈리는 자리는 키 정렬 하나**다.
파이썬은 코드포인트로 정렬하고 JCS는 **UTF-16 코드 유닛**으로 정렬한다. BMP 밖 문자
(U+10000 이상)는 UTF-16에서 대리쌍 D800–DBFF로 표현되므로 U+E000–U+FFFF보다
**앞선다** — 코드포인트 순서와 반대다. RFC 8785 §3.2.3의 정렬 예가 그 자리다.

부동소수점은 **거부한다**. D138이 id 입력에 두지 않기로 했고, 금지를 산문이 아니라
구조로 막는다(D126). 분수 파라미터는 십진 문자열로 넣는다.
"""

from __future__ import annotations

import json


class FloatInCanonicalInput(ValueError):
    """id 입력에 이진 부동소수점이 들어왔다 — D138이 막는 자리."""


def utf16_units(name: str) -> tuple[int, ...]:
    """문자열을 UTF-16 코드 유닛 열로. JCS의 정렬 키(RFC 8785 §3.2.3).

    "Property name strings to be sorted are formatted as arrays of UTF-16 code
    units. The sorting is based on pure value comparisons, where code units are
    treated as unsigned integers" — RFC 8785 §3.2.3.
    """
    raw = name.encode("utf-16-be")
    return tuple((raw[i] << 8) | raw[i + 1] for i in range(0, len(raw), 2))


def _string(value: str) -> str:
    # JSON 최소 이스케이프. 파이썬 json이 RFC 8785 §3.2.2.2와 같은 집합을 쓴다:
    # `"` `\` 와 U+0020 미만만 이스케이프하고, \b \f \n \r \t 단축형을 쓰며
    # 나머지 제어 문자는 소문자 \u00xx. `/`는 이스케이프하지 않는다.
    return json.dumps(value, ensure_ascii=False)


def _number(value) -> str:
    if isinstance(value, float):
        raise FloatInCanonicalInput(
            f"id 입력에 이진 부동소수점 {value!r}. D138 — 분수는 십진 문자열로 넣는다.")
    return str(value)  # 파이썬 int는 정확. JCS는 정수를 그대로 인쇄한다


def dumps(obj) -> str:
    if obj is None:
        return "null"
    if isinstance(obj, bool):  # bool은 int의 하위형 — 숫자보다 먼저 거른다
        return "true" if obj else "false"
    if isinstance(obj, (int, float)):
        return _number(obj)
    if isinstance(obj, str):
        return _string(obj)
    if isinstance(obj, (list, tuple)):
        return "[" + ",".join(dumps(v) for v in obj) + "]"
    if isinstance(obj, dict):
        items = sorted(obj.items(), key=lambda kv: utf16_units(kv[0]))
        return "{" + ",".join(f"{_string(k)}:{dumps(v)}" for k, v in items) + "}"
    raise TypeError(f"JCS로 펼 수 없는 타입: {type(obj)!r}")


def encode(obj) -> bytes:
    """정규 바이트. 해시는 이것에 대해 건다(§2.8)."""
    return dumps(obj).encode("utf-8")
