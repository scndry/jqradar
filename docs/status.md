# 상태 — 다음 세션이 이어받을 것

**지금**: S0 / G0 진행 중(§9 W1–3). CLAUDE.md §3의 1·2·3번까지 왔다. `contract/` 11개 디렉터리와 계약별 README, `contract/percentile/` 케이스 6종(전부 `compute.py`가 생성), `schemas/` 6종 + `validate_examples.py`(§7 예시 검증 + 변조 거부). core 측정 코드는 아직 없다.

**다음**: CLAUDE.md §3의 4번(Gradle 멀티모듈 골격 + `gradle/libs.versions.toml`), 5번(자체 ArchUnit 규칙), 6번(`docs/preregistration/p1a.md`), 7번(`docs/battery.md`). 그리고 `contract/percentile/`의 남은 두 케이스(언어 분리·0 팽창)와 `reproducibility/`·`cpd/`·`history/`·`graph/`의 G0 케이스 — G0 #2·#3·#7이 전부 픽스처를 요구한다.

**막힌 것**: 소유자 결정 대기 5건이 PR 본문 "PRD 충돌"에 있다 — 그중 `median`·`IQR`의 분위 방법(§2.5)과 `lens_percentiles.n`의 의미(§7)는 `contract/percentile/`이 이미 한쪽으로 계산하고 있어 결정이 바뀌면 `fixture_change`가 필요하다.
