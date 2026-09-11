# 상태 — 다음 세션이 이어받을 것

**지금**: S0 / G0 진행 중(§9 W1–3). CLAUDE.md §3의 1·2·3번까지. `contract/` 12개 디렉터리와 계약별 README, `contract/percentile/` 케이스 6종(전부 `compute.py`가 생성), `schemas/` 7종 + `validate_examples.py`(§7 예시 검증 + 하드룰 변조 거부). core 측정 코드는 아직 없다.

**다음**: `g0/v377-alignment`로 묶인 셋 — `contract/schema/` 신설(§2.9, D124: 스키마 7종 × 긍정 1 + 하드룰 변조 ≥ 1, `validate_examples.py`의 케이스를 그리로 이관), `reproducibility/`를 합성 리포 계약으로 재분류(D124), 성분 `n_ranked` 정합 잔여. 그 뒤 CLAUDE.md §3의 4–7번(Gradle 골격, 자체 ArchUnit 규칙 — `double`·`float` 금지 포함, `docs/preregistration/p1a.md`, `docs/battery.md`). `contract/percentile/`의 남은 두 케이스(언어 분리·0 팽창)와 `cpd/`·`history/`·`graph/`·`reproducibility/`의 G0 케이스는 G0 #2·#3·#7이 전부 요구한다.

**막힌 것**: 없음. v3.7.6·v3.7.7이 첫 구현 PR의 PRD 충돌 5건과 후속 검토 7건을 전부 닫았다(D114–D124).

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
