# 상태 — 다음 세션이 이어받을 것

**지금**: S0 / G0 진행 중(§9 W1–3). CLAUDE.md §3의 1·2·3번 완료. `contract/` 13개 디렉터리 — `percentile/` 6케이스, `schema/` **45케이스**(스키마 7종 × 긍정 + 하드룰 변조, D124), `reproducibility/` 1케이스(합성 리포, 결정적 이력). `schemas/` 7종. 공유 자원 둘: `judgment-vocabulary.json`(D127), `fixture-changes/`(D129). core 측정 코드는 아직 없다.

**다음**: CLAUDE.md §3의 4–7번 — Gradle 멀티모듈 골격 + `gradle/libs.versions.toml`, 자체 ArchUnit 규칙(**측정·순위 경로에서 `double`·`float` 금지** D115 포함), `docs/preregistration/p1a.md`, `docs/battery.md`. 픽스처로는 `percentile/`의 남은 둘(언어 분리·0 팽창), `reproducibility/`의 남은 넷(파라미터 변경·reproduce만으로 id 재계산·두 머신 바이트 동일·해시 `pattern` 강제 D128), `cpd/`·`history/`·`graph/`의 G0 케이스 — G0 #2·#3·#7이 전부 요구한다.

**막힌 것**: 없음. D114–D129가 첫 구현 PR의 충돌 5건, 후속 검토 7건, PR #1 감사 4건, 레코드 자리 1건을 전부 닫았다. 남은 계약 공백 하나는 `analysis_input_id`의 **정규 인코딩**(§2.8이 입력 목록만 정하고 바이트로 펴는 방법을 정하지 않는다) — `contract/reproducibility/README.md`에 표시했고 케이스는 로컬 선언으로 유효하다.

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
