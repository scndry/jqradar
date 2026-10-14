# S4-7 — `window_anchor.timestamp`의 표기 (반례 (A) 불일치 · 게이트 G0 — `history/`)

- **인용**: §2.7 "**시각의 정규 표기**(D157): `analysis_input_id`에 들어가거나 `reproduce`에 인쇄되는 모든 시각 문자열은 **UTC · RFC 3339 · 초 정밀 · `Z` 접미 · 소수 초 없음**(`YYYY-MM-DDTHH:MM:SSZ`)" — 대상에 `window_anchor.timestamp`.
- **입력**: `contract/history/anchor-fixed/input.json` — HEAD 커미터 시각 2026-01-15T09:00:00 UTC.
- **두 값**(`run.py`가 계산한다): D157의 정규 표기(`contract/reproducibility/compute.py`의 `canonical_time` — 같은 unix 초) `2026-01-15T09:00:00Z` vs history 계산기가 인쇄하는 `2026-01-15T09:00:00+00:00`(파이썬 `isoformat()`).
- **무엇이 갈리나**: 같은 순간의 다른 바이트 — 그 문자열을 해시하는 자리(id 입력)에서 다른 해시. 같은 실수가 reproducibility 계산기에서 v3.9.0 전에 있었다(`contract/reproducibility/README.md`).
- **게이트**: 값이 `history/` 스위트(G0)의 것 → G0(D266).
