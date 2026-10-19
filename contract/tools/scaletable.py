"""§2.5 표 `D155-1`을 읽는다 — 스케일 린트(`contract/schema/`)와 픽스처 직렬화(`exact.py`)가 **같은 읽기**를 쓴다.

D235 — 린트는 표를 읽는다(사본 없음). D275 — 계약 픽스처의 `expected.json`도 이 표를 따른다: 표의 이름인 필드는 표의
스케일로 인쇄하고, 인쇄가 정확값이 아니면 정확 유리수를 옆 지도 `exact`에 둔다. 읽기가 둘이면 같은 이름이 린트와 픽스처에서
다른 스케일을 받는 날이 온다 — 그래서 한 곳에 둔다(`historywalk.py`·`javasource.py`와 같은 이유).
"""

from __future__ import annotations

import re

# D115 직렬화 스케일 — 경로 패턴 -> 허용 소수 자릿수. `*`는 한 단계 와일드카드.
# 스케일 표 `D155-1`(§2.5) — **필드 이름**으로 매긴다. 표에 없는 유리수 필드는 위반이다.
# 스케일은 고정이다: 자릿수가 많아도, 적어도(후행 0을 떼도) 위반이다 — "바이트 동일"은 파싱된
# 수가 아니라 직렬화된 텍스트에 대한 주장이라(§2.5) 0.38과 0.3800은 다른 바이트다.
# D185 — 표는 산출물 **8종 전부**의 유리수 필드를 들고 린트도 §7 블록 전부를 본다.
# 정수 행의 뜻은 "정수여야 하는 이름"이다: 정수 리터럴은 표와 무관하게 통과하되, 정수 행의 이름에
# 소수가 오면 위반이고(decimal_in_integer_field), 스케일이 있는 행의 이름에 정수 리터럴이 오면
# 후행 0을 뗀 것이라 위반이다(integer_in_scaled_field — "0.38이 아니라 0.3800").
SCALES_VERSION = "D155-1"
#
# **린트는 표를 읽는다**(D235) — 린트 안에 표의 사본을 두지 않는다. 손으로 베낀 사본은 표가 바뀔 때
# 한쪽만 바뀐다: D199·D201이 정수 행에 넣은 `a_dup_tokens`·`b_dup_tokens`·`chg_commits_a`·
# `chg_commits_b`가 사본에 없어서, 그 이름의 소수 변조가 "정수여야 한다"가 아니라 "표에 없다"로
# 거부됐다(4차 S4-29). 읽는 규칙(§2.5 표 아래 문장):
#   - 첫째 칸은 행의 뜻(종류)이다 — 정수·경과 시간·비율·렌즈·Lakos·요약 통계·파라미터. 뜻 → 종류
#     이름의 대응은 코드가 갖는다(`ROW_KIND`). 모르는 행이 생기면 조용히 건너뛰지 않고 멈춘다.
#   - 둘째 칸의 **괄호 밖 백틱 이름**이 필드 이름이고, 괄호 안은 설명이다.
#   - 셋째 칸이 스케일이다 — "정수"면 0, 아니면 `**n자리**`.
#   - 요약 통계 행은 이름이 첫째 칸의 괄호 안에 있다(`spread`의 `median`… — 그릇 이름 `spread`는
#     빼고). 그 이름들의 스케일은 대상 측정에 따르므로(규칙이지 목록이 아니다) 아래
#     `SUMMARY_SCALE_BY_TARGET`·`SUMMARY_NAMED_TARGET`이 정한다. 표에 없는 규칙 이름이 있으면 멈춘다.
SCALE_TABLE_HEADER = "| 종류 | 필드 | 스케일 |"
ROW_KIND = (("정수", "integer"), ("경과 시간", "elapsed_days"), ("비율", "ratio"), ("렌즈", "lens"),
            ("Lakos", "lakos"), ("요약 통계", "summary"), ("파라미터", None))
# 요약 통계의 스케일은 대상 측정의 종류에 따른다(D155·D185) — 정수 측정 2자리(type-7 보간의 .25·.75),
# 비율 4자리, 렌즈 1자리; 경과 시간(일)의 요약도 2자리 — 대상 자체가 2자리 유리수다(D184, §0-40 보정).
SUMMARY_SCALE_BY_TARGET = {"integer": 2, "ratio": 4, "lens": 1, "elapsed_days": 2}
# 요약 통계 행에 이름으로 든 것의 대상 — `median_files_per_commit`은 커밋당 파일 수(정수 측정)의
# 중앙값이라 짝수면 .5(D185), `p90_all`은 evidence의 P90(age_last_days) — 경과 시간의 요약.
SUMMARY_NAMED_TARGET = {"median_files_per_commit": "integer", "p90_all": "elapsed_days"}
# §2.5 모집단 셋(D168의 둘째 단계 이름) — `percentiles.<field>.<population>`의 리프.
POPULATIONS = ("active", "dx", "all")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _names_outside_parens(cell: str) -> list[str]:
    """칸의 괄호 밖 백틱 이름. 백틱 안의 괄호는 깊이를 바꾸지 않는다."""
    names, depth, i = [], 0, 0
    while i < len(cell):
        ch = cell[i]
        if ch == "`":
            j = cell.index("`", i + 1)
            if depth == 0:
                names.append(cell[i + 1:j])
            i = j + 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth == 0:
                raise ValueError(f"표 {SCALES_VERSION}: 닫는 괄호가 남는다 — {cell!r}")
            depth -= 1
        i += 1
    if depth:
        raise ValueError(f"표 {SCALES_VERSION}: 괄호가 닫히지 않았다 — {cell!r}")
    return names


def read_scale_table(prd_text: str) -> dict:
    """§2.5 표 `D155-1`을 읽어 린트의 표를 만든다(D235). 읽을 수 없으면 멈춘다 — 빈 표는 모든 유리수를
    '표에 없다'로 만들어 린트를 조용히 바꾼다."""
    lines = prd_text.split("\n")
    heads = [i for i, l in enumerate(lines) if l.strip() == SCALE_TABLE_HEADER]
    if len(heads) != 1:
        raise ValueError(f"표 {SCALES_VERSION}의 머리 `{SCALE_TABLE_HEADER}`가 {len(heads)}개 — 하나를 기대했다")
    field_kind: dict[str, str] = {}
    kind_scale: dict[str, int] = {}
    summary_names: set[str] = set()
    seen_kinds = []
    for line in lines[heads[0] + 2:]:
        row = line.strip()
        if not row.startswith("|"):
            break
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) != 3:
            raise ValueError(f"표 {SCALES_VERSION}: 칸이 셋이 아닌 행 — {row[:80]!r}")
        label, fields, scale_text = cells
        kinds = [k for prefix, k in ROW_KIND if label.startswith(prefix)]
        if len(kinds) != 1:
            raise ValueError(f"표 {SCALES_VERSION}: 모르는 행 `{label[:40]}` — 행을 더했으면 ROW_KIND에 뜻을 더한다")
        kind = kinds[0]
        seen_kinds.append(kind)
        if kind is None:
            continue
        if kind == "summary":
            summary_names |= set(re.findall(r"`([^`]+)`", label)) - {"spread"}
            continue
        if scale_text.startswith("정수"):
            kind_scale[kind] = 0
        else:
            m = re.search(r"\*\*(\d+)자리\*\*", scale_text)
            if not m:
                raise ValueError(f"표 {SCALES_VERSION}: `{label}` 행의 스케일을 읽지 못했다 — {scale_text[:40]!r}")
            kind_scale[kind] = int(m.group(1))
        for name in _names_outside_parens(fields):
            if not _IDENT.fullmatch(name):
                raise ValueError(f"표 {SCALES_VERSION}: `{label}` 행의 괄호 밖 백틱 `{name}`은 필드 이름이 아니다 — 설명은 괄호 안에")
            if name in field_kind:
                raise ValueError(f"표 {SCALES_VERSION}: `{name}`이 두 행에 있다({field_kind[name]}·{kind})")
            field_kind[name] = kind
    missing = {k for _, k in ROW_KIND if k} - set(seen_kinds)
    if missing:
        raise ValueError(f"표 {SCALES_VERSION}: 행이 없다 — {sorted(missing)}")
    stale = set(SUMMARY_NAMED_TARGET) - summary_names
    if stale:
        raise ValueError(f"표 {SCALES_VERSION}: 요약 통계 규칙의 이름이 표에 없다 — {sorted(stale)}")
    return {"field_kind": field_kind, "kind_scale": kind_scale,
            "summary_keys": summary_names - set(SUMMARY_NAMED_TARGET)}


def scale_for(path: list, parent: dict | None, table: dict) -> int | None:
    """경로의 유리수 필드에 배정된 스케일. 표에 없으면 None. `table`은 `read_scale_table`이 읽은 것."""
    leaf = str(path[-1])
    if leaf.isdigit() and len(path) >= 2:
        # 배열 원소 — 이름은 배열의 키다(`gate`의 `nccd: [base, head]`, D185).
        return scale_for(path[:-1], parent, table)
    if leaf in SUMMARY_NAMED_TARGET:
        return SUMMARY_SCALE_BY_TARGET[SUMMARY_NAMED_TARGET[leaf]]
    if leaf == "value" and isinstance(parent, dict) and "measure" in parent:
        # 증거의 `value`는 그 측정의 값이다 — 스케일도 그 측정의 것(표 적용, 확장 아님).
        kind = table["field_kind"].get(str(parent["measure"]))
        return table["kind_scale"][kind] if kind else None
    if leaf in table["summary_keys"] and "spread" in [str(p) for p in path]:
        # 요약 통계는 대상 측정에 따른다(D155). `cx.java`처럼 언어 접미어가 붙을 수 있다. 대상은 `spread` 옆의 이름이다 —
        # 산출물은 `spread.<측정>.<통계>`, 계약 픽스처는 `<측정>.spread.<통계>`(D275 — 픽스처도 같은 읽기).
        measure = str(path[-3] if str(path[-2]) == "spread" and len(path) >= 3 else path[-2]).split(".")[0]
        kind = table["field_kind"].get(measure)
        return SUMMARY_SCALE_BY_TARGET.get(kind)
    if len(path) >= 2 and str(path[-2]) == "percentiles":
        return 4
    if len(path) >= 3 and str(path[-3]) == "percentiles" and leaf in POPULATIONS:
        # D168 — 두 단계 기록 `percentiles.<field>.<population>`: 리프 키가 모집단 이름이어도
        # 값은 같은 `pct`다. 표의 이름은 경로에서 찾는다(§2.5 표 D155-1 아래 문장). 리프가 모집단 이름일 때만 —
        # 계약 픽스처의 `percentiles.<파일>.value`·`rank_avg`는 그 기록이 아니다(D275, 같은 읽기를 픽스처에 쓰며 드러났다).
        return 4
    kind = table["field_kind"].get(leaf)
    return table["kind_scale"][kind] if kind else None
