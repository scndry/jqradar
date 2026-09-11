# `validation/` — 검증 계약 (§6.3) · 게이트 **G3**

## 이 계약이 고정하는 것

**"validated"가 무엇을 뜻하고 무엇을 뜻하지 않는가**를 못 박는다. 고정 문구: **`validated ≠ 등가 증명`**(D20).

- **목표 개선 합격 함수는 지표별**(D32). 240→239가 "개선"이면 엔진은 편법을 찾는다.
  - 중복: `propose`가 명시한 **`target_pairs` 전부** `pair_dup_tokens = 0` **이고** 새 `new_duplication` 없음(D41)
  - 순환: 해당 SCC 소멸 **이고** 새 SCC 없음
  - 복잡도: 목표 메서드 CYCLO ≥ 20% 감소 **이고** 파일 내 최대 CYCLO 비증가 — 실증되지 않은 **기본 휴리스틱**이며 조직이 `check`에서 바꿀 수 있다(D98)
- **검증은 결과 + 검증 입력 정체성의 쌍**(§6.3 5a, D89). `validated_tree_id`·`validated_analysis_input_id`·`validated_head_sha`·`validation_scope`가 없는 `validated`는 `validated`가 아니다.
- **커버리지 `not_applicable`**(D105). 변경된 실행 가능 라인이 0이면 커버리지 검사는 실패가 아니라 해당 없음이고, 검증은 빌드·전체 테스트·재스캔·`equivalence_basis`로 성립한다.
- **`structural`은 증명이 아니다**(D31, §6.5). 전제조건 전부를 충족해야 하며 하나라도 어긋나면 LLM 경로로 넘기고 근거는 `tests`다.

## 최소 케이스 (§2.9)

| 케이스 | 무엇을 잡나 | 상태 |
|---|---|---|
| 합격 함수 | **`target_pairs` 전부**를 검사한다(한 쌍만 보지 않는다) | 미작성 |
| BLOCK/WARN/INFO | 신규 발견 차등 — 새 순환·새 CPD ≥100·새 P1 → `not_validated` | 미작성 |
| relocation 증거 | 플래그 + 계산 가능한 증거(FAIL 아님, §6.4) | 미작성 |
| `structural` 위반 8종 | §6.5 전제조건(구조·제어 흐름·데이터 흐름·객체·타입/예외·평가 순서) 각 위반 | 미작성 |
| 검증 입력 정체성 | `validated_tree_id` 기록, `validation_scope` pre/post | 미작성 |
| 실행 라인 0 | 커버리지 `not_applicable` + `coverage_basis: not_applicable_no_executable_lines` | 미작성 |
| **`merged_without_effect` 사유 4종** | `validator_mismatch`(검증 트리 재스캔에서도 선언 범위 open) / `partially_resolved`(선언 부분집합만 해소) / `merge_drift`(머지 트리 ≠ 검증 트리) / `superseded`(다른 커밋이 먼저 해소) 각 1건 | 미작성 |
| 해소 뒤 재악화 | → `regressed` | 미작성 |

사유 4종은 **검증 트리 재스캔부터** 시작해 가른다(D91) — 그래야 검증 계약의 실패와 머지 과정의 변화가 섞이지 않는다. `validator_mismatch`라는 이름은 그 재스캔에서도 open일 때**만** 쓴다.
