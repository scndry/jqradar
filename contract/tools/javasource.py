"""Java·Kotlin 소스의 주석과 문자열 리터럴을 가른다 — 계약 계산기들의 공용 구현.

`history/`의 blame 부재 검사(D113)와 `reproducibility/`의 `@Generated` 판별(D258)이 같은 함수를 쓴다.
규율은 하나다: **주석은 버리고 문자열 리터럴은 남긴다**, 코드 쪽에서는 리터럴을 `""`로 지운다 — 그래야
코드 토큰은 주석이나 문자열이 아니라 **코드**일 때만 잡힌다.

이 함수는 합성 픽스처 입력의 모양을 읽는 계약의 설명이지 파서가 아니다. 실제 구현의 증인은 PMD AST다
(소스 쪽 증인, §1 B.1). Kotlin의 중첩 블록 주석·문자열 템플릿 안의 따옴표는 다루지 않는다 — 픽스처가
그 모양을 쓰지 않는다.
"""
from __future__ import annotations


def split_java(source: str) -> tuple[str, list[str]]:
    """소스를 (주석 뺀 코드, 문자열 리터럴 목록)으로 가른다. 코드 쪽 리터럴은 `""`로 남는다."""
    out, literals = [], []
    i, n = 0, len(source)
    while i < n:
        two = source[i:i + 2]
        if two == "//":
            while i < n and source[i] != "\n":
                i += 1
            continue
        if two == "/*":
            end = source.find("*/", i + 2)
            i = n if end < 0 else end + 2
            continue
        if source[i:i + 3] == '"""':                      # 텍스트 블록(Java 15+)
            end = source.find('"""', i + 3)
            literals.append(source[i + 3:end] if end >= 0 else source[i + 3:])
            out.append('""')
            i = n if end < 0 else end + 3
            continue
        if source[i] in '"\'':
            quote, j, buf = source[i], i + 1, []
            while j < n and source[j] != quote:
                if source[j] == "\\":
                    buf.append(source[j:j + 2])
                    j += 2
                    continue
                buf.append(source[j])
                j += 1
            literals.append("".join(buf))
            out.append('""')
            i = j + 1
            continue
        out.append(source[i])
        i += 1
    return "".join(out), literals


# ── 최상위 선언과 그 어노테이션(D258) ─────────────────────────────────────────────────────────────
#
# 최상위 = 중괄호 깊이 0 · 괄호 깊이 0. 메서드·필드는 깊이 ≥ 1이고, 매개변수·레코드 성분은 괄호 안이라
# 그 어노테이션은 최상위 선언의 것이 아니다. 주석은 `split_java`가 버렸고 리터럴은 `""`로 지워져
# 주석·문자열 안의 `@Generated`는 보이지 않는다.

# §2.1·D211 — 세 `@Generated`(계약 상수; `reproduce`에 인쇄하지 않는다, D210).
GENERATED_ANNOTATIONS = ("javax.annotation.Generated", "jakarta.annotation.Generated",
                         "javax.annotation.processing.Generated")

DECLARATION_KEYWORDS = {
    "java": {"class", "interface", "enum", "record"},
    "kotlin": {"class", "interface", "object", "fun", "val", "var", "typealias"},
}
import re as _re  # noqa: E402

_TOKEN = _re.compile(r"@(?:\w+:)?[\w.]+|\w+|\S")   # 숫자·구두점도 토큰 — `= 2` 뒤의 선언이 `=` 뒤로 읽히지 않게
_IMPORT = _re.compile(r"^\s*import\s+([\w.]+(?:\.\*)?)\s*;?\s*$", _re.M)


def _depth_zero(code: str) -> str:
    """중괄호·괄호 안을 공백으로 지운 코드 — 깊이 0의 글자만 남는다."""
    out, brace, paren = [], 0, 0
    for ch in code:
        if ch == "{":
            brace += 1
        elif ch == "}":
            brace -= 1
        elif ch == "(":
            paren += 1
        elif ch == ")":
            paren -= 1
        elif brace == 0 and paren == 0:
            out.append(ch)
            continue
        out.append(" ")
    return "".join(out)


def _resolve(name: str, imports: list[str]) -> str:
    """어노테이션 이름 → 정규 이름. 정규 이름이면 그대로, 단순 이름이면 단일 import로. 요구 시 import(`pkg.*`)는
    그 패키지에 있다고 **아는** 이름(세 `@Generated`)만 푼다 — 모르는 이름을 그 패키지로 읽으면 거짓 정규 이름이다
    (`java.lang`의 `SuppressWarnings`를 `javax.annotation`으로). 풀지 못한 이름은 단순 이름 그대로 둔다."""
    if "." in name:
        return name
    for imp in imports:
        if imp.endswith("." + name):
            return imp
    for imp in imports:
        if imp.endswith(".*") and imp[:-1] + name in GENERATED_ANNOTATIONS:
            return imp[:-1] + name
    return name


def top_level_declarations(source: str, language: str) -> list[dict]:
    """최상위 선언마다 {kind, name, annotations(정규 이름)}. `@interface`는 선언 키워드 `interface`로 읽는다."""
    code, _ = split_java(source)
    imports = _IMPORT.findall(code)
    keywords = DECLARATION_KEYWORDS[language]
    decls, pending, prev = [], [], None
    tokens = [m.group(0) for m in _TOKEN.finditer(_depth_zero(code))]
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "@interface":
            tok = "interface"
        if tok.startswith("@"):
            name = tok[1:].split(":", 1)[-1]
            pending.append(_resolve(name, imports))
        elif tok in keywords and prev != "=":
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            if nxt in keywords:        # `fun interface`·`enum class` — 뒤 키워드가 선언이다(어노테이션은 넘어간다)
                prev = tok
                i += 1
                continue
            decls.append({"kind": tok, "name": nxt, "annotations": pending})
            pending = []
        prev = tok
        i += 1
    return decls
