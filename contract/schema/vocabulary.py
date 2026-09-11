#!/usr/bin/env python3
"""판정 어휘 사전 -> JSON Schema `pattern` (D127).

사전은 `contract/judgment-vocabulary.json` **한 곳**에만 있다. 이 모듈이 그것을
정규식으로 바꾸고, 스키마의 `$defs.noteText.not.pattern`에 심는다. `contract/renderer/`
(G2)도 같은 사전을 읽는다 — 렌더러는 JSON의 순수 함수이므로 JSON 층에서 막지 않으면
HTML 층에서 막아도 늦다(D67·D127).

스키마에 심는 이유: 제3자가 순수 `jsonschema`로만 검증해도 걸려야 한다. 심은 값이
사전과 어긋나지 않는지는 `contract/schema/vocabulary-sync/` 케이스가 본다.

    python3 contract/schema/vocabulary.py --sync    # 스키마에 패턴 심기
    python3 contract/schema/vocabulary.py           # 패턴 인쇄
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DICT = ROOT / "contract" / "judgment-vocabulary.json"
SCHEMAS = ROOT / "schemas"

# `*_note`를 가진 스키마와 그 안에서 자유 텍스트인 경로.
NOTE_FIELDS = {
    "report.schema.json": [
        ("$defs", "population", "properties", "population_note"),
        ("$defs", "component", "properties", "zone_note"),
        ("$defs", "file", "properties", "lenses", "properties", "composite_note"),
    ],
    "validate.schema.json": [
        ("properties", "note"),
    ],
}


def load_terms() -> dict:
    return json.loads(DICT.read_text(encoding="utf-8"))["terms"]


def _ci(word: str) -> str:
    """ECMA-262 정규식에는 `(?i)` 플래그가 없다. 글자마다 문자 클래스로 편다."""
    out = []
    for ch in word:
        if ch.isalpha() and ch.isascii():
            out.append(f"[{ch.upper()}{ch.lower()}]")
        else:
            out.append(ch)
    return "".join(out)


def build_pattern(terms: dict | None = None) -> str:
    """판정 어휘를 **포함하면** 일치하는 정규식.

    라틴 문자는 단어 경계로 감싼다 — `badge`·`poorly`의 오탐을 막는다.
    한글은 어미가 붙으므로 경계 없이 부분 문자열로 잡는다(`나쁘` -> `나쁘다`).
    """
    terms = terms or load_terms()
    latin = "|".join(_ci(w) for w in sorted(terms["latin"]))
    hangul = "|".join(sorted(terms["hangul"]))
    return rf"(?:\b(?:{latin})\b|(?:{hangul}))"


def note_text_def(pattern: str) -> dict:
    return {
        "type": ["string", "null"],
        "description": (
            "사람이 읽는 자유 텍스트. **판정 어휘를 담을 수 없다**(D67·D127) — "
            "렌더러는 JSON의 순수 함수라 여기 들어간 단어는 그대로 화면에 뜬다. "
            "금지 목록은 `contract/judgment-vocabulary.json` 한 곳에만 있고 "
            "`contract/renderer/`(G2)가 같은 사전을 쓴다. 아래 `pattern`은 그 사전에서 "
            "생성된 값이며 `contract/schema/vocabulary-sync/`가 동기화를 검사한다."
        ),
        # 안쪽 스키마에 type: string이 **필수**다. JSON Schema의 `pattern`은
        # 문자열이 아닌 값에 무시되므로, 없으면 `null`에 대해 안쪽이 참이 되고
        # `not`이 그것을 뒤집어 정상적인 null을 거부한다(§7 예시가 이 버그를 잡았다).
        "not": {"type": "string", "pattern": pattern},
    }


def dig(node: dict, path: tuple):
    for key in path:
        node = node[key]
    return node


def sync() -> int:
    pattern = build_pattern()
    changed = 0
    for filename, paths in NOTE_FIELDS.items():
        p = SCHEMAS / filename
        doc = json.loads(p.read_text(encoding="utf-8"))
        doc.setdefault("$defs", {})["noteText"] = note_text_def(pattern)
        for path in paths:
            parent = dig(doc, path[:-1])
            leaf = path[-1]
            original = parent[leaf].get("description", "")
            parent[leaf] = {"$ref": "#/$defs/noteText"}
            if original:
                parent[leaf]["description"] = original
        p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        changed += 1
        print(f"synced {filename}  ({len(paths)} note 필드)")
    print(f"\npattern = {pattern[:80]}…  ({len(pattern)}자)")
    return changed


def check() -> list[str]:
    """스키마에 심긴 패턴이 사전과 맞는지. 어긋난 곳의 이름을 돌려준다."""
    expected = build_pattern()
    drift = []
    for filename in NOTE_FIELDS:
        doc = json.loads((SCHEMAS / filename).read_text(encoding="utf-8"))
        got = doc.get("$defs", {}).get("noteText", {}).get("not", {})
        if got.get("pattern") != expected or got.get("type") != "string":
            drift.append(filename)
    return drift


if __name__ == "__main__":
    if "--sync" in sys.argv:
        raise SystemExit(0 if sync() else 1)
    print(build_pattern())
