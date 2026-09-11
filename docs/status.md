# 상태 — 다음 세션이 이어받을 것

**지금**: S0 / G0. **G0 체크리스트(§9) 7항목 중 남은 것은 #1(리뷰어 2명 교차 검토) 하나이고, 그것은 사람의 자리다** — 기계가 대신할 수 없다. #2–#7은 CI가 매 PR에서 지킨다. 검토 자료는 [`g0-review-packet.md`](g0-review-packet.md)에 있다.

**있는 것**: `prd.md` v3.8.0(D1–D133). `contract/` 케이스 **75종** — percentile 6 · schema 45 · cpd 5 · history 10 · graph 8 · reproducibility 1. `schemas/` 7종. Gradle 골격(모듈 여섯, 빈 소스셋)과 자체 ArchUnit 규칙 넷 + 반례(11 tests). CI 3잡(재계산 대조 · `fixture_change` 가드 · 빌드). `docs/preregistration/p1a.md`, `docs/battery.md`(실측).

**다음 — 사람이 먼저**: G0 #1. 리뷰어 둘 중 **최소 한 명은 프로젝트 밖**에서 와야 한다(D84, Trusting Trust) — 계약을 구현한 것도, 픽스처를 쓴 것도, 검토 패킷을 쓴 것도 같은 도구다. 통과하면 계약 동결, 그 뒤 G1(§9 W4–7): core 측정·백분위·렌즈·JSON, CLI `scan`, `contract/lens`·`gate`, 자기 적용 S1(`docs/self/`에 첫 지도 보존).

**검토자가 먼저 볼 것** — 강제 장치가 없는 계약 셋(패킷 §1.4): §2.4 파일 쌍(`shared`·`tc`)과 §2.1 저자 사실 넷은 **§2.9 표에 배정 자체가 없고**, #1의 범위인 §6.3–6.6은 값 층 픽스처가 G3에 온다.

**열린 공백**: O 항목 아홉과 PRD 공백 다섯을 패킷 §5에 모았다 — "몰라서 빈 것"과 "열어둔 것"을 가르기 위해서다. 가장 위험한 하나는 `analysis_input_id`의 **정규 인코딩**(§2.8이 입력 목록만 정하고 바이트로 펴는 방법을 정하지 않는다).

---

## 이력 재작성 기록 (CLAUDE.md §5)

공개 전 신원 정리 목적의 main 이력 재작성 — **1회, 소진됨**.

| 항목 | 값 |
|---|---|
| 언제 | 2026-09-11, 첫 push **직전**(원격 생성 전) |
| 무엇 | 전체 8커밋의 author·committer를 `seongman.yang <seongman.yang@wadiz.kr>` → `scndry <scndryan@gmail.com>` |
| 왜 | 개인 리포(`scndry/jqradar`, private)에 회사 주소가 실리는 것을 막기 위해 |
| 재작성 전 main | `refs/original/refs/heads/main` = **`38b07af`** |
| 도구 | `git filter-branch --env-filter` (git-filter-repo 미설치) |

**이후 main 이력은 재작성하지 않는다.** `analysis_input_id`가 창 안 커밋 SHA 목록을 포함하고 캠페인 앵커가 SHA로 봉인되므로(§2.8·§5.4), `docs/self/` 첫 리포트(S1)와 첫 앵커(S3) 이후의 재작성은 앵커와 캐시를 깬다. PR 브랜치의 force-with-lease는 머지 전까지 정상이다.

별건으로 PR #1 브랜치에 트레일러 backfill force-push가 1회 있었다(머지 전, 트리 내용 바이트 동일). 소유자가 쓴 `docs(prd): §0-14 v3.7.5` 커밋에는 트레일러를 붙이지 않았다 — 거짓 선언이고 D48이 막는 자리다.

## 훅 (CLAUDE.md §5)

전역 `~/.config/git/hooks/commit-msg`가 `Co-Authored-By: Claude/Anthropic`를 막는다. 전역 훅은 **그대로 두고** 이 리포만 `core.hooksPath = .githooks`(빈 디렉터리)로 해제했다 — 이 리포에서는 그 트레일러가 `declared_ai_assistance`의 자료이기 때문이다(§5.1, P17).
