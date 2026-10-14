# O4-13 — `commit_granularity`는 행마다인가 리포에 하나인가 (반례 (A) 불일치 · 게이트 G0 — `schema/`·`history/`)

- **인용**: §3.5 "각 행에 `shared`·**`chg_commits_a`·`chg_commits_b`**·정적 의존 유무·`commit_granularity` 경고" · §2.4 "`commit_granularity: coarse` 경고 병기" · §7 report — 숨은 결합 행은 `{a, b, shared, chg_commits_a, chg_commits_b, tc, static_dependency}`이고 `commit_granularity`는 `population`에 하나; `schemas/report.schema.json`의 `hiddenCoupling`은 `additionalProperties: false`.
- **입력**: `contract/history/hidden-coupling-sort-order/input.json` — history 계산기가 내는 쌍 행은 행마다 `commit_granularity`를 싣는다(`run.py`가 확인한다); 그 모양을 §7 report의 첫 숨은 결합 행에 싣는다.
- **두 값**(`run.py`가 계산한다): §3.5대로 행마다 실으면 스키마가 **거부**(`/hidden_couplings/0`), §7대로 리포에 하나면 **허용**.
- **무엇이 갈리나**: §3.5를 따른 구현의 산출물은 스키마를 통과하지 못한다; history 픽스처의 행 모양은 §3.5 쪽이다. 거칠기는 창의 속성이라 리포에 하나가 맞아 보이지만(리뷰어 의견) 결정이다.
- **게이트**: 값(스키마 판정)이 `schema/`(그리고 행 모양은 `history/`) 스위트(G0)의 것 → G0(D266).
