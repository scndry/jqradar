# `ledger/` — 부채 원장 계약 (§5.4–5.5) · 게이트 **G2b**

## 이 계약이 고정하는 것

**상태를 저장하지 않고 파생한다는 것**, **같은 finding이 무엇인가**, 그리고 **누가 해소의 성과를 갖는가**를 못 박는다.

- **파생 층 ⊕ 사건 층**(D55). 코드 상태는 저장하지 않고 앵커 스캔과 HEAD 스캔에서 파생한다 — 저장은 틀리면 남고 계산은 틀려도 다음 실행에서 고쳐진다(B.4). 저장하는 것은 코드에서 파생되지 않는 **행위의 사건**(claim·validation)뿐이다.
- **전이 모델**(D99–D103). 상태는 "현재 파생 × 마지막 머지 사건"이 아니라 **전이 이력**이다. 후보 커밋 C마다 `derived(F, parent(C)) → derived(F, C)`를 국소 재스캔해 전이를 판정하고, **전이가 일어난 커밋이 귀속을 소유한다**(D100). 시간 순서는 인과가 아니다.
- **정본 어휘는 §5.5 한 곳에만 있다**(D110). `validated`·`rejected`는 PR의 검증 결과이지 원장 상태가 아니다.
- **멱등성**(D94) — `(campaign, finding, pr)`당 파일 하나, `pr<n>.json`. 재시도는 같은 파일을 덮어쓴다.
- **`.jqradar/`에 쓰는 것은 캠페인 관리와 수정 PR뿐**(D61). 일반 PR과 `scan`·`change`·`check`는 아무것도 쓰지 않는다 — 그 성질이 깨지는 순간 `.jqradar/`는 Terraform state가 되고 리포를 떠나야 한다(§12).

## 최소 케이스 (§2.9)

정체성·후속 판정:
- 앵커 등록과 `anchor_class` 얼림 — 툴체인이 바뀌어 앵커를 재스캔해도 저장된 `anchor_class`는 **불변**(D56·D88)
- **후속 판정 6종**(same / moved / split / merged / removed / unknown) — A→B 이동 + 분할 + 일부 C 이동 예제 포함, 해소는 **후속 집합 전체**에 합격 함수(D71)
- 인터페이스 추출로 **재작성된** 분할 → 토큰 계보가 실패하고 **메서드 시그니처 계보**가 `split`을 낸다(D107)
- 순환 finding의 과거 커밋 전이 → `transition_basis: source_imports` 표기(D106)

전이와 귀속:
- **전이 모델 전 조합** — 전이 종류 × 전이 커밋의 사건
- **오귀속 5종을 실패 사례로**:
  1. 효과 없는 claim 머지 뒤 무관 PR이 해소 → `closed_unclaimed` + claim은 `merged_without_effect`
  2. 먼저 해소한 무관 PR 뒤 오래된 claim 머지 → `superseded`
  3. 검증 실패 claim 머지 뒤 무관 PR이 해소 → `closed_unclaimed`(**`closed_unverified` 아님**)
  4. claim 없이 해소 뒤 회귀 → `regressed`
  5. `target_pairs` 부분 선언 해소 → `partially_resolved`(**`validator_mismatch` 아님**)

scope·계보·뷰:
- scope 탈출 → `relocated_out_of_scope`(개수 목표에서 open으로 계속 센다), split 혼합(≥50% 밖 / 미만), scope 목표와 전역 가드레일(D75)
- `reanchor` → `supersedes` 계보, 옛 캠페인 **불변**(D92)
- 같은 finding 중복 claim → git 충돌이 아니라 `in_progress (PR 2개)`(D63)
- **`(campaign, finding, pr)` 멱등 재시도 → 파일 1개**(D94)
- `--live`의 `stale_claim`(D74)
- **재구성 결정성** — 같은 커밋 → **바이트 동일** 뷰, 아카이브 후 `--at` = 아카이브 전(D79). **출시 조건**이다(S5)
- `first_observed_estimate` 3방법(pickaxe / region_blame / file_first_commit)
- **매 스캔·매 change 경로에서 `.jqradar/` 쓰기 시 실패**(D61). blame 호출 검사는 `history/`(G0)로 옮겼다(D113)

전부 미작성 — G2b 전에 **픽스처를 먼저 박고 구현한다**(D79).
