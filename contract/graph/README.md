# `graph/` — 컴포넌트·시스템 그래프 계약 (§2.2–2.3) · 게이트 **G0**

## 이 계약이 고정하는 것

**무엇이 노드이고 무엇이 간선인가**, 그리고 그 위의 Martin·Lakos 숫자를 못 박는다. 지표는 직접 구현하지 않고 ArchUnit `ArchitectureMetrics`를 부른다(D3) — 그래서 이 계약이 고정하는 것은 공식이 아니라 **입력 그래프의 전처리**다.

- **`bytecode_scope`** = 프로젝트 자체 모듈의 main 출력 클래스만. 테스트·`@Generated`·`build/generated` 유래·서드파티·JDK는 제외. 외부 타입 간선은 `external` **의사 노드**로 접어 **기록하되** Ca/Ce/I/A/D·CCD에서는 **제외**한다. 이 전처리에 픽스처 1개 필수(§2.2가 이름까지 지정: `contract/graph/external-edges`).
- **간선** = `JavaClass.getDirectDependenciesFromSelf()`. 컴포넌트로 접을 때 자기 간선·중복 제거, `class_edge_count`는 따로 센다.
- **`component.strategy`** = `module` / `auto`(최장 공통 접두어 아래 첫 레벨, 자식 1개면 하향, 60% 초과 자식은 추가 분할, 다중 루트는 루트별) / `depth:<n>`. 결정 결과를 `reproduce`에 인쇄한다(D15).
- **순환** = Tarjan SCC.
- **Lakos** = `CCD = Σ(전이적 도달 컴포넌트 수, 자기 포함)`, `ACD = CCD/N`, `RACD = ACD/N`, `NCCD = CCD / ((N+1)·log₂(N+1) − N)`.

## 최소 케이스 (§2.9)

| 케이스 | 무엇을 잡나 | 상태 |
|---|---|---|
| **`external-edges/`** | 외부 의사 노드가 기록되되 지표에서 빠진다. §2.2가 이름을 지정한 필수 케이스 | 미작성 |
| auto 전략 4종 | 최장 공통 접두어, 자식 1개 하향, 60% 초과 분할, 다중 루트 | 미작성 |
| 순환 | Tarjan SCC 탐지와 `break_candidates` | 미작성 |
| NCCD 검산 | N=41, CCD=512 → `CCD_balanced ≈ 185.5`, `ACD ≈ 12.49`, `RACD ≈ 0.305`, `NCCD ≈ 2.76`(§2.3) | 미작성 |

NCCD 검산은 §7 예시가 쓰는 값이라 `lens/sample-service` 픽스처와 숫자가 일치해야 한다.
