"""§2.7 시각의 정규 표기(D157) — history/·reproducibility/ 두 계산기가 **같은 함수**로 적는다(D274).

UTC · RFC 3339 · 초 · `Z` · 소수 초 없음(`YYYY-MM-DDTHH:MM:SSZ`), **unix 초에서** 만든다. `%cI`가 아니라
`%ct`(unix 초): git 버전에 따라 UTC를 `Z`로도 `+00:00`으로도 써서 두 머신에서 문자열이 갈리고, 이 값은
`analysis_input_id`에 **해시로 들어간다** — 같은 트리·같은 툴체인인데 id가 달라진다(PR #4에서 CI가 잡았다).
`%ct`로 바꾼 뒤에도 파이썬 `isoformat()`이 `+00:00`을 냈다 — 표기가 계약이 아니어서 계산기가 제 사정대로 적은
것이다. v3.9.0이 표기를 정했고(D157), v3.10.23이 **계약 픽스처가 인쇄하는 시각**도 같은 표기라고 못 박았다(D274):
history 계산기가 `isoformat()`을 그대로 인쇄해 `window_anchor.timestamp`가 `…+00:00`이었다(4차 S4-7).
JCS는 문자열 안을 건드리지 않으므로 여기서 한 형식으로 만들어야 한다.
"""

from __future__ import annotations

from datetime import datetime, timezone

PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"


def canonical_time(unix_seconds: int) -> str:
    """unix 초 → 정규 표기."""
    return datetime.fromtimestamp(int(unix_seconds), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical_time_of(moment: datetime | str) -> str:
    """시각대가 붙은 datetime(또는 그 ISO 문자열) → 정규 표기. 계산기 안의 표현은 그대로 두고 **인쇄하는 자리**에서 쓴다."""
    if isinstance(moment, str):
        moment = datetime.fromisoformat(moment)
    if moment.tzinfo is None:
        raise ValueError(f"시각대 없는 시각은 정규 표기로 옮길 수 없다: {moment!r}")
    return canonical_time(int(moment.timestamp()))
