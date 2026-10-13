# S4-5 — 창 W의 위 끝 (반례 (A) 불일치 · 게이트 G0 — `history/`)

- **인용**: §2.7 "**창 W**: 커미터 시각 ∈ `[HEAD_TIME − window.months(12), HEAD_TIME]`인 비머지 커밋" — 닫힌 구간, 위 끝은 `HEAD_TIME`.
- **입력**: `contract/history/negative-age-invalid-metadata/input.json` — HEAD(`c2`, 2026-08-02)보다 커미터 시각이 하루 늦은 조상 커밋(`c1`, 2026-08-03, `src/A.java`).
- **두 값**(`run.py`가 계산한다):
  - §2.7의 닫힌 구간으로 읽으면 `c1`은 W 밖 — `commits_in_window` 1, `src/A.java`의 `chg_commits` 0.
  - history 계산기(`contract/history/compute.py`의 창 선택 — 아래 끝만 본다)와 그 픽스처는 W 안으로 센다 — 2, 1.
- **무엇이 갈리나**: `chg_commits`·`active` 모집단·H의 입력. 나이는 어느 쪽이든 음수라 null + `invalid_metadata`로 같다.
- **게이트**: 값이 `history/` 스위트(§2.9 표 G0)의 것 → G0(D266).
