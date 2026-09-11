# `history/` — 이력 계약 (§2.7) · 게이트 **G0**

## 이 계약이 고정하는 것

**시간의 기준점**과 **무엇을 커밋으로 세는가**, 그리고 **blame을 부르지 않는다는 것**을 못 박는다.

- **앵커 = `HEAD_TIME`**(HEAD 커밋의 커미터 시각). 모든 "최근"·"경과"가 이 시각 기준이다. 같은 HEAD·같은 트리를 **언제 재도 같은 값**이 나와야 한다 — `scanned_at`은 감사 메타데이터일 뿐 계산에 들어가지 않는다(D25). v3.2까지 이 기준점이 없어서 같은 HEAD를 나중에 재면 값이 달라졌다(§0-4 #2).
- **창 W** = 커미터 시각 ∈ `[HEAD_TIME − 12개월, HEAD_TIME]`인 **비머지** 커밋, 최신순 최대 2,000. 먼저 닥치는 상한을 적용하고 `window_applied.bound_hit`에 어느 쪽인지 적는다.
- **rename** = JGit `RenameDetector` 유사도 60. 후보가 여럿이면 tie-break = 유사도 → 경로 편집 거리 → 사전순, 동률은 `rename_ambiguous` 표기.
- **나이** = `HEAD_TIME − 마지막 비머지 커밋 커미터 시각`. 결정 불가면 `null`, 음수면 `null` + `reason: invalid_metadata`. **null은 0이 아니다**(D37).
- **blame 금지**(D18·D113). 유일한 예외는 캠페인 생성 1회(§5.6, D57). 강제 장치가 대상 코드보다 앞서야 하므로 이 검사는 `ledger/`(G2b)가 아니라 여기(G0)에 있다.

## 케이스 모양

이 계약은 **이력 자체가 전제**라 케이스마다 합성 리포가 필요하다: 커밋을 스크립트로 생성하고(고정된 author/committer 시각), 그 트리와 `expected.json`을 함께 커밋한다. 생성 스크립트는 결정적이어야 한다 — 같은 스크립트가 언제 돌아도 같은 SHA를 내도록 시각·저자·메시지를 전부 고정한다.

## 최소 케이스 (§2.9)

| 케이스 | 무엇을 잡나 | 상태 |
|---|---|---|
| 앵커 고정 | 같은 HEAD를 **다른 날짜에** 스캔해도 `age_last_days`·`chg_commits` 동일 | 미작성 |
| 머지 제외 | 부모 ≥ 2인 커밋은 `chg_commits`에 들어가지 않는다 | 미작성 |
| rename | 유사도 60 경계, tie-break 3단계, 동률 → `rename_ambiguous` | 미작성 |
| 상한 두 종류 | 12개월 상한이 먼저 걸리는 경우와 2,000커밋 상한이 먼저 걸리는 경우, `bound_hit` | 미작성 |
| coarse | `median_files_per_commit > 20` → `commit_granularity: coarse`, 그리고 `chg_commits` 성분의 confidence가 `low`로 내려간다(§3.7) | 미작성 |
| shallow clone | 조상 복구 실패 → `age_last_days: null`, `reason: age_unknown`, F도 null | 미작성 |
| 음수 나이 | 잘못된 메타데이터·시계 → `null`, `reason: invalid_metadata` | 미작성 |
| **blame 호출 시 실패** | `scan`·`change` 경로에서 `BlameCommand`가 불리면 픽스처가 **실패**한다(D113) | 미작성 |

마지막 케이스는 다른 것들과 성격이 다르다 — 값을 대조하는 것이 아니라 **호출되지 않았음**을 확인한다. G0 시점에는 core가 없으므로 이 케이스는 구현이 생기는 즉시(W4–7) 박아야 하고, 그 전까지는 CLAUDE.md §3.5의 ArchUnit 규칙이 같은 선을 지킨다.
