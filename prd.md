# 📡 jQRadar (Java Quality Radar) — PRD v3.7.4

작성 2026-09-07 · **브라운필드 판.** "기준선을 잠그면 기존 부채는 어떻게 되나"라는 소유자의 질문에 답하면서 "지키는 것" 셋(B.2·B.3·B.6)을 고쳤다 — 철학은 헌법이 아니라 결정이다. 셋째 표면 **부채 원장**(파생 층 ⊕ 사건 층, 저장은 리포 안 `.jqradar/`), 조직이 등록하는 **캠페인 앵커**, **앵커에 얼린 분류**, **한정 blame**을 넣었고 일정을 17주로 늘렸다. **v3.6.1**(2026-09-08)은 기능 추가 없이 원장의 판정 의미를 닫았다 — finding 정체성·후속 판정, 사건 × 파생 상태표, scope 회계, 필드 개명(§0-8). **v3.7**(2026-09-08)은 **자기 적용(self-application) 계약** — jQRadar는 jQRadar로 만든다. 도구가 자기 리포의 첫 대상이고, 자기 PR의 게이트이며, 첫 캠페인이고, 첫 파일럿이다(§9 자기 적용, B.7). **v3.7.1**(2026-09-09)은 기능 추가 없이 **증거 사슬 identity → validation → merge → ledger**를 닫는다 — 재현성 정체성 셋, 검증의 트리 결속, `validated_not_resolved` 4분기, reanchor 계보, 멱등성, P1a 코호트(§0-10). 다음 단계는 본문이 아니라 픽스처다. **v3.7.2**(2026-09-09)는 철학 수정 — **저작 무관의 사회적 논거를 철회**한다. 저작 여부는 도구가 소유할 수 없는 조직의 정책이고(B.6), 금지는 효과도 없었다(`git blame`은 어디에나 있다). 금지 → 기본 꺼짐 + 조직 정책, 하드룰은 셋만 남긴다(§0-11). **v3.7.3**(2026-09-10)은 원장 상태를 스냅샷 × 최종 사건이 아니라 **전이 이력**으로 계산해 오귀속을 없앴고(§0-12), **v3.7.4**(2026-09-10)는 경계 조건 — 내용 주소 캐시, 순환 finding 전이의 바이트코드 한계, 실행 라인 0 커버리지, 계보 분모·시그니처 보조, S4 정직한 완주 — 를 닫았다(§0-13).

---

## 0. 변경 이력

> **§1(철학)과 충돌하는 제안은 결정을 요구한다 — 제안을 버리거나, 철학을 고친다. 어느 쪽이든 기록한다.** (v3.5의 "받지 않는다"는 틀렸다: 철학은 헌법이 아니라 결정이고, v3.6이 그 첫 사례다.) 감사자는 계약을 감사하고 목적은 감사하지 않는다 — 목적은 소유자가 지킨다.


### 0-1. v2.1 → v3.0
차원 불일치 점수 → 백분위 렌즈; Martin/Lakos 스코프 정정; 핫스팟 = 조사 우선순위; 아키텍처 수정은 제안만; 검증 게이트; 회귀 기준 게이트; 재현 블록; 검증 계획.

### 0-2. v3.0 → v3.1 (Gemini 감사)
원값·분포 표시; F = P90 ∧ 180일; `component.strategy=auto`; 라인 커버리지(일시 jacoco); JGit 기본·네이티브 옵트인.

### 0-3. v3.1 → v3.2 (ChatGPT 심층 감사 1차)
백분위·CPD·이력·검증·보안 여섯 계약 신설; NCCD 검산; BASE 자격 고정; blame 제거; `validated`; BLOCK/WARN/INFO; 샌드박스; 16주.

### 0-4. v3.2 → v3.3 (ChatGPT 심층 감사 2차, 2026-09-07)
진단: "각 계약은 좋아졌는데 계약끼리 충돌한다." 동의.

| # | 지적 | 판단 | v3.3 처치 |
|---|---|---|---|
| 1 | F의 모집단(W 안 변경 ≥ 1)이 F가 찾는 파일을 제외 | **P0, 내가 만든 모순** | 모집단을 `active`(H·Dx)와 `all`(F)로 분리, 필드별 모집단 기록 — §2.5, §3.3 |
| 2 | "최근"·"경과 일"의 기준 시점 부재 → 같은 HEAD를 나중에 재면 값이 달라짐 | **P0** | 앵커 = **HEAD 커미터 시각**. `scanned_at`은 감사용 — §2.7 |
| 3 | 샘플 composite 81.5는 71.5여야 함(두 판 연속 산술 오류) | **P0** | 예시를 **실행 가능한 픽스처**로, CI가 measures→lenses→composite→NCCD 재계산 검증 — §2.9, §7 |
| 4 | confidence 집계 미정의, 샘플 불일치(n=194인데 high) | P1 | 렌즈 confidence = 기여 성분의 **최소** — §3.7 |
| 5 | 상위 10% 멤버십·동점 규칙 | P1 | `pct ≥ 0.90`, tie-break `priority desc, path asc, id asc` — §3.7 |
| 6 | O9(H 변경 단위)는 열어둘 것이 아니라 계약 | P1 | `chg_commits`로 **잠금**. `chg_days`는 P2 비교 실험만 — §3.1 |
| 7 | tree_id: 미추적 파일 blob-id 없음; 분석 무관 파일 포함 | 절반 — blob 해시는 오브젝트 없이도 계산 가능 | 전 파일 **blob 공식**으로 통일. `repository_state_id`와 `analysis_input_id`로 분리 — §2.8 |
| 8 | `classes_id` 미정의, 환경 버전 부정확 | P1 | 정의 + major.minor.patch — §2.8 |
| 9 | `pair_dup_tokens` 투영 공식 | P1 | 정규 일치 기준 공식 + 겹침 예시 — §2.6 |
| 10 | Dx 질량 선택은 옳음 | 유지 | "비율이 아니라 질량"을 명시 — §3.2 |
| 11 | `active_twin_ratio` twins=0 | P2, **B 선택** | twins=0 → `null`, Dx 모집단 = 중복 있는 활성 파일 — §3.2 |
| 12 | `tc` 분모 명명 | P1 | `chg_commits` 명시 — §2.4 |
| 14 | `by_construction` 과함 | P2, 받음 | `equivalence_basis ∈ {structural, tests, none}` — §6.5 |
| 16 | 목표 개선 합격 함수 부재 | P1 | 지표별 합격 함수 — §6.3 |
| 18 | P9 벡터 편중, 허용 목록 저장소 손상 | 받음 | 의존성 캐시 사전 적재 + 락파일, 벡터 확장 — §6.6, P9 |
| 19 | 프롬프트 방어가 프롬프트 수준 | 받음 | 구조적 방어: LLM은 옵션 ID·소스 루트 내 편집만 — §6.6 |
| 20·21·23 | P10 시나리오, P7 성능 예산, P1a 제외 규칙 | 받음 | §9 |
| 26 | 적합성 스위트 | **가장 값진 제안** | `contract/` 합성 리포 + 기대 JSON, G0/G1/G3에 분배 — §2.9, §9 |

### 0-5. v3.3 → v3.4 (ChatGPT 재감사, 2026-09-07) — 기능 추가 없음
| # | 지적 | 판단 | v3.4 처치 |
|---|---|---|---|
| 1 | `interpretation`이 쓰는 "렌즈 값의 백분위"가 어디서도 정의되지 않음 | **P0** | 렌즈 백분위 계약(모집단 매핑·0 포함·null 제외), `lens_percentiles` 기록 — §2.5, §3.7 |
| 2 | `P90(age_last_days)`의 분위 계산법 미정의 | **P0** | type-7 선형 보간, 유효 나이만, `percentile_method` 블록 — §2.5 |
| 3 | `IQR < 0.25·median`은 median=0에서 무분산을 놓침 | P1 | `IQR = 0 → low` 추가 — §3.7 |
| 4 | `age_last_days = null` 처리 없음 | P1 | F = **null**(0 아님), `reason: age_unknown`, `valid_n` — §2.1, §3.3 |
| 5 | "값 null"과 "모집단 제외" 구분 | P1 | `percentile_population.reason` — §2.5 |
| 6 | 정규 일치 ID = 토큰 해시의 용어 충돌 | P1, 위험이 아니라 CPD의 원래 모델 | `duplicate_cluster`로 명명, ID = 해시+토큰 수 — §2.6 |
| 7 | `new_cpd_match` 정체성 | P1, 클러스터 수준으론 부족 | **발생 수준** + rename 매핑 — §5 |
| 8 | 중복 합격이 한 쌍만 검사 | P1 | `target_pairs` 전부 — §6.3 |
| 9 | P1a가 H를 검증하지 못함(H가 `chg`를 성분으로 가짐) | **가장 중요** | 구성타당도로 재설계: 기준선 넷, 증분 리프트 — §9 |
| 10 | 효과 크기·CI | P1 | 부트스트랩 95% CI, 수치는 휴리스틱 — §9 |
| 11 | P8 참조 경계 신뢰도 | P1 | 아키텍트 2명, inter-rater κ — §9 |
| 12 | P11 원인 분류 | P1 | `fixture_change` 필수 — §2.9 |
| 13 | `analysis_input_id`는 내용 해시여야 | P1 | 명시 — §2.8 |
| 14 | `classes_id` 화살표 의미 | P1 | `classes_reproduction_inputs`로 명명 — §2.8 |
| 15 | L2가 사실상 Gradle 전제 | 받음 | 1차 = Gradle 명시, Maven은 O12 — §6.6 |
| 16·17·18 | composite null·P7·16주 유지 | 유지 | — |

### 0-6. v3.4 → v3.5 (철학 복원, 2026-09-07)
| 변경 | 내용 | 어디 |
|---|---|---|
| §1 재작성 | 소유자의 철학 7항(A. 믿는 것 — 왜 지금·무엇을 보는가) + 규율 6항(B. 지키는 것) + 설계 요구(C) + 원칙→계약 매핑(D) | §1 |
| 변경 리포트 1차 표면 | `jqradar change --base`가 매일 쓰는 산출물, `check`는 그 위의 정책 소비자. 새 측정 없음 — 델타 출력의 재구성 | §5 |
| 저작 무관 가드 | "변경의 흔적은 재되 출처(AI/사람)는 재지 않는다"를 철학 문장에 박음 | §1 A.6 |
| 백로그 | 이력 저장소·finding→규칙 승격은 v3.6. 그때까지 "진화 관찰"은 약속이고 기능이 아니다 | §9, §12 |

### 0-7. v3.5 → v3.6 (브라운필드 — 소유자 질문 + ChatGPT 답변 재검토, 2026-09-07)
질문: "베이스라인이 이미 엉망인 브라운필드에서 BASE를 잠그면 jQRadar는 그 이후 문제만 돕는 것 아닌가?" 답: 찾기(지도)와 고치기(수정 워크플로)는 첫날부터 되고, **추적**("나아지고 있나")이 안 됐다. 그리고 소유자의 지적대로 나는 "지키는 것"을 결정이 아니라 제약으로 다뤄 ChatGPT의 제안 넷을 반사적으로 기각했다. 다시 보니 넷 다 받을 수 있었고, 받으려면 규율 셋을 고쳐야 했다.

| 항목 | 처치 |
|---|---|
| A.1 "핵심 단위는 변경" | **두 방향**으로 — 보호(변경 단위, BASE 대비)와 개선(원장 단위). A.8 신설: 브라운필드가 기본 상태, 변경이 닿는 부채부터 |
| B.2 현장≠판결 | 수정: 부채 캠페인은 **앵커에 얼린 분류**로 진전을 잰다 — 판결이 아니라 착수 순서. 얼리는 이유: 상대 백분위는 최악을 고쳐도 다음 10%가 올라와 개선이 라벨에서 보이지 않는다 |
| B.3 자기 기준선 | 수정: 기준선은 **둘** — 움직이는 보호 기준선(merge-base)과 고정된 캠페인 앵커(조직 등록). 리포 간 비교 금지는 유지 |
| B.6 정책은 한 자리 | 수정: **이름 붙은 자리들** — `check` 프로필과 캠페인 정의 |
| 둘째 기준선(ChatGPT) | 받음 — 이름·타입이 있으면 혼란이 없다. 캠페인 앵커 — §5.4 |
| `absolute_risk`(ChatGPT) | 받음 — 앵커 시점 렌즈 백분위로 얼린 `anchor_class` — §5.5 |
| `target_value`(ChatGPT) | 받음 — 조직이 캠페인에 적고 도구는 담고 추적 — §5.4 |
| `debt_age`(ChatGPT) | 받음 — **한정 blame**: 캠페인 생성 1회, 원장 finding 영역만, 방법 기록(v3.6.1에서 `first_observed_estimate`로 개명) — §5.6 |
| 부채 원장 | 백로그(v3.6)에서 **범위 안으로**, 셋째 표면 — §5.5, §7 |
| 일정 | 16 → **17주** |

**v3.6 개정(원장의 정체)** — 처음 안은 코드 상태를 append-only 파일에 저장하는 모듈이었다. 두 번 고쳤다. (1) B.4에 비추면 **코드의 상태는 저장하지 않고 앵커·HEAD 두 스캔에서 파생**해야 한다 — 저장은 틀리면 남고 계산은 틀려도 다음 실행에서 고쳐진다. (2) 그러나 감사가 요구한 생명주기(`in_progress`·`validated`·`rejected`·`closed`)는 **행위의 사건**이라 코드에서 파생되지 않으므로 저장해야 한다. 원장 = 파생 층 ⊕ 사건 층. 저장 위치는 별도 서버가 아니라 **리포 안 `.jqradar/`**(수정 PR이 자기 사건 파일을 싣는다, 캠페인 종료 시 트리에서 아카이브). 선례: Changesets/Towncrier(PR당 파일, 릴리스 때 소비), RuboCop `.rubocop_todo`/Detekt baseline(브라운필드 등록), Betterer(래칫), ADR, DVC. 부품은 전부 흔하고 조합은 새것이라 P15(파일럿)로 검증한다 — §5.5.

**v3.6 개정(구조 복원)** — §4(시스템 구조)와 §6.1–6.2·6.4·§11·§12가 v3.3 재작성에서 "v3.2와 같음" 스텁으로 남아 있던 것을 본문으로 복원. 본문에 판 이력 메모를 남기지 않는다는 규칙은 아래 0-11 뒤에.

**v3.6 개정(인터랙티브 시각화)** — CodeScene의 시각화(시스템 맵·Combined Aspects·변경 결합 오버레이·X-Ray·Goals·Lost Notes)를 조사해 HTML 렌더러 스펙을 §7.1에 적었다. 정적 리포트가 아니라 **인터랙티브 자립형 HTML**이다. 가져온 것: 원 패킹 맵 + aspect 토글(우리 렌즈와 1:1), 결합선 hover/고정, 메서드 표·의존성 휠, lost findings. 가져오지 않은 것: 저자·팀 필터, Jira 오버레이, ML 우선순위, 절대 점수 색, 추세 차트(이력 저장소 전까지 두 점만).

### 0-8. v3.6 → v3.6.1 (ChatGPT 재감사, 2026-09-08) — 계약 보정, 기능 추가 없음
판정 "철학은 해결됐고 원장의 판정 의미를 완결해야 한다"에 동의. 픽스처를 먼저 박고 계약 문장은 그 설명으로(v3.3에서 배운 순서).

| # | 지적 | 판단 | 처치 |
|---|---|---|---|
| P0-1 | finding 종류별 canonical identity와 이동·분할·병합 규칙 부재 — A→B 이동+분할+일부 C 이동 예제에 답이 없음 | 맞음 | 종류별 정체성 표 + **후속 판정 `succession`**(토큰 출처로 same/moved/split/merged/removed/unknown). 해소는 후속 집합 전체에 합격 함수 — §5.5 |
| P0-2 | `validated`(PR 시점) ≠ `closed`(앵커 대비), 결합·순서·동시성 미정의 | 맞음. 단 `merged`·`superseded`는 쓰는 사건이 아니라 git 파생 | 파생 × 최종 머지 사건 → 유효 상태표, 머지 순서는 main first-parent, `regressed`는 **세 스캔**(앵커·머지 커밋·HEAD) — §5.5 |
| — | (감사가 못 짚은 결과) `in_progress`는 main에서 보이지 않음 | 새 발견 | 뷰 둘: `--at`(머지분만, 결정적) / `--live`(claim 브랜치 포함, 시점 의존), `stale_claim` — §5.5 |
| P1 | scope 밖 이동이 `resolved`로 보임 | 맞음 | `relocated_out_of_scope`; 질량 목표는 리포 전체 회계, 개수 목표는 scope + relocated는 open 유지; scope 변경 = 새 캠페인 — §5.4 |
| P1 | `first_seen_estimate`가 "최초 발생"으로 읽힘 | 맞음 | `first_observed_estimate`로 개명, UI 문구 고정 — §5.6 |
| P1 | `anchor_class`와 현재 우선순위 혼용 | 맞음 | `current_priority` 분리, 역할 표기 — §5.5 |
| P1 | 재구성 결정성 테스트 | 맞음 | `contract/ledger` + P15 — §2.9, §9 |
| P2 | 목표 없는 캠페인 | 맞음 | `campaign_mode: tracking_only \| target_driven`, `goal_status` — §5.4 |
| P2 | "첫날부터 보인다" 문구, F 이름, `fan_in` 범위 | 맞음 | 문구 정정 — §1, §3.3, §2.1 |
| — | 감사 표의 "아키텍처 위반 — 규칙 ID" | 받지 않음 | 규칙은 ArchRules의 층. 우리에겐 순환만 |

### 0-9. v3.6.1 → v3.7 (자기 적용, 2026-09-08)
소유자: "jQRadar는 jQRadar로 진행해야 한다." 도구가 자기 자신의 첫 대상이어야 한다 — 사용(도그푸딩)이면서, 그 결과가 자기 진화의 게이트가 된다는 점에서 **자기 적용(self-application)**. 철학에서 바로 나온다: A.3(구현자가 AI 에이전트인데 그 PR을 jQRadar가 심사하지 않으면 자기 주장을 자기 프로젝트에서 믿지 않는 것), A.6("진화는 측정 가능하게"라고 쓴 도구가 자기 진화를 재지 않으면 슬로건), P15(우리가 첫 파일럿), A.5(지표를 만든 사람이 게이밍 유혹을 가장 잘 안다). 처치: B.7 신설, §9 자기 적용 계약(stage 부트스트랩 표·한계·용어), 각 게이트에 자기 적용 항목, §8 복원(v3.3 이후 스텁이었다) + Thompson·Wheeler, §12에 Trusting Trust 위험. 기존 백로그의 "v3.7" 참조는 v3.8로 이동.

### 0-10. v3.7 → v3.7.1 (심층 감사, 2026-09-09) — 계약 보정, 기능 추가 없음
감사의 축: "재현 가능하다·검증됐다·같은 finding이다" 셋 중 **검증 재현성이 비어 있었다.** 소유자가 잠근 전제 셋 — (1) 캠페인 앵커(트리)와 분석 캐시(툴체인 포함)는 분리하고 `anchor_class`는 결정 산출물로 저장, (2) `merge_drift`는 실패가 아니라 구분자, (3) `validated_not_resolved`의 원인 판정은 **검증된 트리**에서 시작하며 `validator_mismatch`는 그 재스캔에서도 open일 때만.

| # | 지적 | 처치 |
|---|---|---|
| P0-1 | `analysis_input_id`에 툴체인·계약 버전 없음 → 버전 달라도 캐시 적중 | 재정의 + 원칙 "포함되지 않은 입력은 결과에 영향을 주어서는 안 된다" — §2.8 |
| P0-2 | 검증이 트리에 결속되지 않음 | `validated_tree_id`·`validated_analysis_input_id`·`validation_scope` — §5.5, §6.3 |
| P0-3 | `validated_not_resolved`에 원인 4종이 뭉침 | 검증 트리 재스캔부터 시작하는 4분기표 — §5.5 |
| P0-4 | P1a 6개월 관찰창 검열 부재 | 코호트 컷오프 계약 — §9 |
| P0-5 | `reanchor` 의미 미정 | 새 캠페인 계보(`supersedes`) — §5.4 |
| P1 | kind별 succession, split+scope 혼합, scope 목표/전역 가드레일, `goal_status` 경계, reproduce/provenance 분리, actor 의미, 가변 초안/불변 사건, 멱등성, L1′, 감사 로그 위치, S4 표본, NCCD 컨텍스트 | 전부 반영 — §2.8·§5.4·§5.5·§6.6·§9 |
| P2 | rename tie-break, 음수 나이, `first_observed` 증거 필드, 20% 휴리스틱 격하 | 반영 — §2.1·§2.7·§5.6·§6.3 |
| — | 감사가 못 짚은 결과: 앵커 봉인은 트리(`repository_state_id`)여야 하고, 툴체인이 바뀌면 앵커 트리를 현재 툴체인으로 재스캔하며, 그래서 `anchor_class`는 저장해야 한다 | §5.4 — 소유자 전제 (1)과 일치 |

### 0-11. v3.7.1 → v3.7.2 (철학 수정 — 저작, 2026-09-09)
소유자: "사회적 논거는 해당 조직의 도덕성에 맡겨야 하는 것 아닌가. 어차피 문제가 있는 조직은 `git blame`을 볼 텐데." 맞다. 내 논거는 둘이 틀렸다. (1) **효과가 없다** — 우리가 저자를 숨겨도 감시는 줄지 않고 선의의 조직이 소유권 분산 신호를 잃을 뿐이다. (2) **B.6과 모순이다** — 정책은 조직의 것이라면서 저작 여부라는 정책을 도구가 하드코딩했다. "감시 장치가 된다"는 문장은 조직을 후견하는 말이었다.
남는 이유는 도덕이 아니라 다른 종류다: **경험적 제품 위험**(개인 지표는 게이밍·저항 — DORA·SPACE가 팀 수준 집계를 권함 → 금지가 아니라 *기본 꺼짐*의 근거), **데이터 최소화**(개인정보의 처리 근거는 조직의 책임 → 기본 최소, 켜면 조직이 책임; `.jqradar/`에는 정체를 저장하지 않음), **추론 금지**(AI/사람 추론은 틀리면 사람을 오분류). 하드룰 하나 추가: **개인 순위·리더보드 표면을 우리가 만들지 않는다**(B.2를 사람에 적용 — 사실은 계산하고 판결 표면은 만들지 않는다).

| 항목 | 이전 | 이후 |
|---|---|---|
| A.6 | "출처는 재지 않는다 — 감시 시스템이 된다" | "출처는 조직이 정한 범위에서 잰다. 기본은 분산(익명 집계)과 선언된 도구 관여" |
| B.3 | 사회적 논거 | 경험적 논거 + 데이터 최소화. 리포 간 비교·팀 순위 **표면** 금지는 유지 |
| 정책 자리 | `check` 프로필, 캠페인 정의 | + `jqradar.yml`의 `people` 절(`attribution: off \| team \| individual`, 기본 off). `scan`은 이 절만 읽는다 |
| 새 사실 | — | `distinct_authors_90d`, `ownership_max_share`, `minor_contributor_share`(익명 집계, 기본 켜짐); `declared_ai_assistance`(선언된 트레일러만) |
| D11·D48 | 팀 렌즈 옵트인 / 저작 무관 | 세 층 + 하드룰 셋(리포 저장 금지·추론 금지·순위 표면 금지) |
| 검증 | — | P17(선언된 AI 관여 변경이 finding을 더 여는가 — A.3의 자기 검증), P18(분산 사실의 증분 예측력), P15에 `individual` 켠 조직의 도입·게이밍 관찰 |
| 복원 | — | §10의 D1–D23 목록, §6.5 `structural` 전제조건 전문, §9의 P3–P6·P7 워크로드 매트릭스·배터리 리포 목록, §7의 `gate.json`·`validate.json` 예시 — 전부 v3.3 재작성에서 "이전 판과 같음"으로 줄였다가 사라졌던 것. 본문의 판 이력 메모(§4·§8·§10·§2.6·§6.5·§5.4·§5.6·§6.4의 "vX에서…" 문장)와 제목의 "(vX)" 꼬리를 제거하고, §1은 판 태그 없이 읽히게 |

### 0-12. v3.7.2 → v3.7.3 (상태 모델 정정, 2026-09-10)
소유자 질문: "원장 상태 결합에 잘못된 사건을 해소 원인으로 귀속하는 결함이 있지 않은가." 있었다. "가장 최근 머지된 사건이 상태를 소유" × "현재 파생 상태"라는 결합은 인과를 시간 순서로 대신했고, 다섯 경로로 오귀속했다 — 효과 없는 claim이 뒤에 머지되면 남의 성과를 가져감, 먼저 해소한 무관 PR 뒤에 머지된 오래된 claim이 성과를 가져감, 검증 실패 PR이 남의 해소에 `closed_unverified`로 기소됨, claim 없이 닫힌 부채의 회귀가 `open`으로 보임, `target_pairs` 부분 선언 해소가 `validator_mismatch`로 오판됨. 처치: **전이 모델** — 상태는 스냅샷 × 최종 사건이 아니라 후보 커밋마다 `derived(parent)→derived(C)`의 전이 이력으로 계산하고, **전이가 일어난 커밋이 귀속을 소유**한다. 새 상태 `merged_without_effect`·`partially_resolved`·`superseded`. `closed_unverified`는 해소 전이를 만든 커밋이 실패 사건을 실은 경우에만. 픽스처에 오귀속 5종을 실패 사례로. 기능 추가 없음 — §5.5, §2.9, §7, P14, D99–D103.

### 0-13. v3.7.3 → v3.7.4 (Gemini 감사, 2026-09-10) — 경계 조건, 기능 추가 없음
| 지적 | 판단 | 처치 |
|---|---|---|
| 전이 스캔 연산량 | 우려 맞음. 제안된 필터("내용이 바뀐 커밋만")는 후보 정의에 이미 있었다 | 진짜 해법 명시: **내용 주소 측정 캐시**(키 = 파일 내용 + 엔진 버전)와 전이 캐시 — §4.5. **감사가 못 짚은 결함**: 전이 스캔의 국소성은 Dx·H·F에만 참이고 **순환 finding은 바이트코드가 필요**해 과거 커밋에 없다 → 리포트가 있는 커밋에서만 정확, 사이는 import 기반 근사 + 표기 — §5.5, P14 |
| 실행 라인 0 변경이 커버리지에서 무조건 거부됨 | 맞음 | `not_applicable`(실패 아님) — §6.3. 인터페이스 추출은 D6에 의해 `apply` 대상이 아님 |
| 토큰 계보가 추상화 분할에서 `unknown`을 냄 | 계약 오독(분모는 후속 파일이 아니라 앵커 토큰) — 그러나 **재작성된** 코드는 실제로 못 따라간다 | 분모 명시 + **메서드 시그니처 계보**(소스 수준, 과거 커밋에서도 국소) 보조. 호출 그래프는 바이트코드라 과거 커밋에 쓸 수 없어 미채택 — §5.5, P14 |
| PR 번호로 정체 역추적 가능 | 관찰 맞음, **처방 거부** | 같은 리포의 `git log`가 저자를 직접 노출하므로 사건 파일은 아무것도 더하지 않고, PR 번호 해시는 뒤집히는 연극이며 `--live`를 망친다. D48의 "정체"를 이름·이메일·핸들로 명시하고 PR 번호·SHA는 산출물 참조로 — D48 |
| S4 교착(상위 3건이 검증 불능이면 G3 영구 차단) | 맞음, 조건 재정의 | S4 = 성공이 아니라 **정직한 완주**. 전부 `not_validated`면 사유 기록 + 최대 3건 확장 후 멈춤. 예외 승인 워크플로는 두지 않음(검증 예외는 `check`의 자리) — §9 S4, D82 |

**문서 규칙(v3.7.2)** — 본문(§1–§12)에는 계약·근거·결정만 쓴다. "언제 뭘 고쳤다"는 판 이력은 §0에만 남긴다 — 본문의 편집 메모는 읽는 사람이 아니라 쓰는 사람을 위한 것이었다. 문장 단위 "(vX.Y)" 태그는 본문(§1–§9, §11–§12)에서 제거했다 — 변경점은 §0와 git diff가 갖는다. §10 결정 기록의 판 표기는 기록의 일부(언제 결정·개정됐나)라 유지한다.

**문서 규칙 2 — 본문은 언제나 자기 완결이어야 한다.** "이전 판과 같음"·"vX §n 그대로"·"나머지는 vY"라는 참조를 본문에 쓰지 않는다. 그것은 다음 재작성에서 내용이 사라지는 가장 확실한 경로였다 — §4·§8·§10 D1–D23·§6.5 전제조건·§9 P3–P6와 매트릭스·§7 예시가 그렇게 사라졌고, 참조가 가리키던 판은 이미 없었다. 줄이려면 본문을 줄이고, 옮기려면 옮긴 자리를 §n으로 가리킨다. 이전 판을 가리키는 문장이 본문에 있으면 리뷰에서 반려한다.

---

## 1. 철학과 제품 정의

> **생성은 자유롭게, 진화는 측정 가능하게.**

이 절은 장식이 아니라 **결정 규칙**이다 — 어떤 제안이든 여기에 비추어 판정한다. 예: 절대 하한(`cx < 15`)은 B.3 위반이라 `check`로 보내고, 네이티브 git 우선은 B.4 위반이라 옵트인으로, 아키텍처 자동 수정은 A.4·B.5 위반이라 제안만으로, composite 헤드라인은 A.5·B.3 위반이라 둘째 줄로. 이 절 자체도 **결정**이다 — 충돌은 제안을 버리거나 철학을 고치기를 요구하고, 고칠 때는 여기와 §0에 기록한다.

### A. 믿는 것 — 왜 지금, 무엇을 보는가
1. **코드는 결과물이 아니라 계속 변하는 시스템의 상태다.** 일반 품질 도구는 현재 코드를 평가한다 — 복잡한가, 중복인가, 규칙을 위반했는가. jQRadar는 두 방향으로 묻는다: *이번 변경이 시스템을 이전보다 더 나쁘게 만들었는가*(보호 — 변경 단위, BASE 대비), 그리고 *우리가 안고 있던 부채가 실제로 줄고 있는가*(개선 — 원장 단위, 앵커 대비). **소프트웨어의 진화는 악화를 막는 것과 누적된 구조적 부채를 줄이는 두 방향으로 관리된다.** BASE는 보호 기준이지 품질의 면죄부가 아니다.
2. **품질은 미학이 아니라 변경 비용의 문제다.** 나쁜 코드란 못생긴 코드가 아니라 다음 변경을 어렵게 하는 코드다 — 이해하기 어렵고, 작은 요구가 여러 곳으로 전파되고, 같은 로직이 복제되어 함께 고쳐야 하고, 변경이 한 곳에 과도하게 집중되고, 시간이 갈수록 구조를 이해하는 사람이 없어진다. 좋은 구조란 현재 실행되는 구조가 아니라 **미래의 변경을 낮은 비용과 낮은 위험으로 수용하는 구조**다. 복잡도·결합도·중복·변경 이력은 독립 지표가 아니라 미래 변경 비용을 설명하는 증거다.
3. **AI 시대의 병목은 생성이 아니라 검증이다.** AI는 만드는 비용을 낮추지만 다음은 답하지 않는다 — 기존 구조에 맞는가, 왜 이 설계였는가, 비슷한 코드가 이미 있지 않은가, 암묵적 계약을 깨지 않는가, 테스트가 통과해도 구조적 문제가 남지 않는가. jQRadar는 AI를 대체하지 않는다. **AI가 빠르게 만든 코드를 시스템의 장기적 맥락 안에서 심사하는 장치**다.
4. **정답을 아는 도구가 아니라 판단을 더 잘하게 하는 도구다.** 복잡한 클래스, 높은 결합도, 중복, 큰 모듈, 변경이 집중된 파일은 무조건 나쁘지 않다 — 도메인 복잡성이거나 의도된 격리일 수 있다. 그래서 자동 판결이 아니라 **설명 가능한 근거**를 낸다: "이 변경으로 이 모듈의 복잡도가 기준선보다 증가했고, 과거 변경 집중 영역과 겹치며, 유사 로직이 다른 두 위치에도 존재한다. 따라서 향후 수정 비용과 회귀 위험이 증가할 가능성이 있다."
5. **측정값보다 변화의 방향이다.** 단일 점수는 게임화된다 — 복잡도를 낮추려 억지로 분할하고, 중복 탐지를 피하려 과잉 추상화하고, 결합도를 낮추려 의미 없는 인터페이스를 추가하고, 게이트를 통과하려 지표만 최적화한다. BASE와 델타를 강조하는 이유가 여기 있다. 좋은 리팩터링은 지표를 예쁘게 만드는 것이 아니라 **실제 finding이 사라지고, 새 문제가 생기지 않고, 이후 변경이 쉬워지고, 원래 의도가 보존되는 변경**이다.
6. **코드 분석기가 아니라 소프트웨어 진화의 관찰 시스템이다.** 실행 중인 시스템의 observability가 상태를 보듯, jQRadar는 구조가 시간에 따라 어떻게 변질되는지를 본다 — 구조적 복잡성의 변화, 의존성 그래프의 변화, 중복의 생성과 소멸, 변경 집중도의 변화, 리팩터링의 효과, 특정 영역의 지속적 악화. **변경이 남긴 구조적 흔적을 재고, 출처는 조직이 정한 범위에서 잰다**. 기본은 출처의 *분산*(익명 집계 — 몇 개의 손을 거쳤나)과 *선언된 도구 관여*(트레일러)이며, 개인 귀속은 조직의 정책(`people.attribution`)이다. 도구는 사람에 대한 순위 표면을 만들지 않고, AI/사람을 추론하지 않고, 리포에 정체를 저장하지 않는다.
7. **AI가 코드를 많이 만들어도 망가지지 않게 하는 피드백 루프다.** AI를 금지하지도 그 생산성을 부정하지도 않는다. 대신 요구한다 — 변경은 측정되어야 하고, 위험은 설명되어야 하고, 개선안은 검증되어야 하고, 기준선보다 악화되면 감지되어야 하고, 반복되는 문제는 정책과 규칙으로 승격되어야 하고, **최종 책임은 사람과 팀에 남아야 한다.**
8. **브라운필드가 기본 상태다.** 대부분의 리포는 이미 부채를 안고 시작한다. 그린필드에서 jQRadar는 악화 방지이지만, 브라운필드에서는 "어디부터 고치나"가 더 어렵고 더 값지다. 전부 고치지 않는다 — 초기 스캔의 수백 finding을 다 겨누면 팀은 무시하고 AI는 지표만 낮춘다. **변경이 닿는 부채부터, 작고 검증 가능한 단위로.** 그리고 고쳤다는 사실을 잃지 않는다: 앵커 시점의 값은 절대 덮어쓰지 않는다.

**한 문장 정의** — jQRadar는 코드의 현재 품질을 평가하는 도구가 아니라, 사람과 AI가 소프트웨어를 계속 변경하더라도 그 시스템의 이해 가능성·변경 가능성·구조적 건전성이 무너지지 않도록 **관찰하고, 검증된 제안과 사람의 머지를 통해 교정하는** 진화 통제 시스템이다.

### B. 지키는 것 — 어떻게 행동하는가
이름이 절반을 말한다. **레이더는 어디에 무엇이 있는지 보여주고, 무엇을 할지는 정하지 않는다.** 범죄 현장 조사는 용의자를 지목하기 전에 현장을 보는 일이다 — jQRadar는 현장(어디)을 찍고, 범인(누구)은 묻지 않고, 판결(어떻게 할 것인가)은 사람에게 남긴다.
1. **코드는 증거고, 이력은 행동이다.** 증인이 셋이다 — PMD(무엇인가), ArchUnit(어떻게 짜였나), JGit(어떻게 행동했나). 한 증인의 말로 판결하지 않는다.
2. **현장은 조사할 곳이지 판결이 아니다.** 산출물은 점수가 아니라 `priority · evidence · confidence`이고, 아키텍처는 제안만 한다. *단, 부채 캠페인은 앵커 시점에 얼린 분류(`anchor_class`)로 진전을 잰다.* 분류는 리포 상대이고 증거를 가지며, "나쁨"의 판결이 아니라 **착수 순서**다. 얼리는 이유는 개선이 보이게 하기 위해서다 — 움직이는 백분위로는 이길 수 없다.
3. **모든 리포는 자기 자신의 기준선이다 — 그리고 기준선은 둘이다.** 움직이는 **보호 기준선**(PR의 merge-base: "더 나빠졌나")과 조직이 등록하는 고정된 **캠페인 앵커**("얼마나 좋아졌나"). 둘 다 리포 내부다. 백분위, 절대 임계 없음, **리포 간 비교 없음**은 그대로다. 이유: 통계가 아니라 **경험적**이다 — 개인·팀 단위 절대 점수는 게이밍되고 저항받는다는 것이 DORA·SPACE가 팀 수준 집계를 권하는 이유이고, LOC·커밋 수 지표의 역사가 그 증거다. 이것은 도구가 조직의 도덕을 대신 판단하는 논거가 아니라(그건 조직의 것이다) **jQRadar 자신의 도입과 지표 유효성**에 대한 논거다. 그래서 결론은 금지가 아니라 *기본값*이다: 리포 간 비교 표면과 사람 순위 표면은 만들지 않고, 저자 사실은 조직 정책으로 켠다(A.6, D48).
4. **다시 계산할 수 없는 숫자는 의견이다.** 숫자는 측정에서, 측정은 계약에서, 계약은 픽스처에서. 예시조차 픽스처다. §2의 계약은 관료주의가 아니라 이 원칙의 비용이다. **재현성은 셋이다** — 측정(`analysis_input_id`), 검증(`validated_tree_id`), 원장(앵커 + HEAD + 사건 이력). 두 원칙: *`analysis_input_id`에 포함되지 않은 입력은 분석 결과에 영향을 주어서는 안 된다.* *검증된 코드는 검증된 입력과 동일하다는 증거가 없는 한 검증된 것으로 간주하지 않는다.*
5. **고칠 수 있지만, 겸손하게.** 브랜치에서만, 샌드박스에서만, 검증과 함께. 기계적인 것은 기계적으로, 결정은 사람에게. "validated"는 증명이 아니고, 도구는 모르는 것(의미 등가)을 안다고 말하지 않는다. 속을 수 있음을 전제로 짓는다 — LLM이 속아도 피해 경로가 없게.
6. **정책은 조직의 것이다.** 붙일 때 아무것도 묻지 않고, 판단이 필요한 **이름 붙은 자리들** — `check` 프로필과 캠페인 정의(앵커·범위·목표) — 에서만 조직이 자기 이름과 해시로 적는다. 도구가 소유할 수 없는 임계·목표를 도구가 갖지 않는다.
7. **먼저 우리에게.** jQRadar의 첫 대상은 jQRadar다. 자기 리포를 스캔하고, 자기 PR을 게이트하고, 자기 부채로 첫 캠페인을 열고, 자기 finding을 자기 수정 경로로 고친다. 우리가 남에게 요구하는 비용("변경은 측정되어야 한다")을 우리가 먼저 낸다. 그리고 자기 적용은 필요하지만 충분하지 않다 — 자기 맹점은 자기 적용으로 드러나지 않으므로 외부 배터리·외부 파일럿·사람 검증자를 대체하지 못한다(§9, §12 Trusting Trust).

### C. 이 철학이 설계에 요구하는 것
| 요구 | 상태 | 어디 |
|---|---|---|
| **변경 리포트가 1차 표면**(A.1·A.5) — "이 변경이 무엇을 바꿨나"가 매일 쓰는 산출물, `scan`은 그 아래의 지도 | 반영 — 기존 델타 계산의 출력 재구성, 새 측정 없음 | §5 |
| **저작 정책**(A.6·B.3) — 흔적은 재고, 출처는 조직이 정한 범위에서. 기본 분산·선언된 도구 관여, 개인 귀속은 정책 | 반영 | §1 A.6, §2.1, §2.7, §4.3, §6.6, D48 |
| **부채 원장**(A.1 개선 방향·A.6·A.8) — 캠페인 앵커, 얼린 분류, finding 생명주기(사건), `first_observed_estimate` | 반영 — 셋째 표면 = 파생(스캔) ⊕ 사건(`.jqradar/`). 전체 리포트 이력은 백로그 | §5.4–5.7, §7 |
| **finding → 규칙 승격**(A.7) — 원장에서 반복되는 finding을 `check` 규칙·ArchRules 규칙 초안으로 사람에게 제안 | 백로그, 원장 위에 +1주 | §9 |

### D. 원칙 → 계약
| 원칙 | 구현 |
|---|---|
| A.1 두 방향(보호/개선) | §5.1 변경 리포트(BASE 델타) / §5.5 부채 원장(앵커 대비) |
| A.2 변경 비용의 증거 | §2 측정, §3 렌즈 |
| A.3 검증이 병목 | §6 수정 워크플로, `validate` |
| A.4 설명 가능성 | §3.7 `priority·evidence·confidence`, `explain`, §5 설명 조립 |
| A.5 방향 > 값 | §5 델타, §6.4 재배치 증거 |
| A.6 진화 관찰 | §2.7 시간 앵커; §5.5 원장(append-only); 전체 이력은 백로그 |
| A.7 피드백 루프·책임 | §6.1 브랜치·PR; §5.5 상태 전이는 머지 시점; 규칙 승격 |
| A.8 브라운필드 기본 | §5.4 scope, §5.5 정렬(변경이 닿는 부채부터), §5.7 `touched_legacy_findings` |
| B.1 증인 셋 | §2, 세 엔진 고정 |
| B.2 현장≠판결(+얼린 분류) | §3.7, §6.1 아키텍처 제안만; §5.5 `anchor_class`는 착수 순서 |
| B.3 기준선 둘 | §2.5 백분위; §5 merge-base / §5.4 캠페인 앵커; 비목표(리포 간 비교) |
| B.4 재계산 가능성 | §2.8 식별자, §2.9 적합성 스위트 |
| B.5 겸손한 수정 | §6.3–6.6 |
| B.6 정책은 이름 붙은 자리들 | §5.3 `check` 프로필, §5.4 캠페인 정의 |
| B.7 먼저 우리에게 | §9 자기 적용 계약, 게이트별 S1–S5 |

### 제품 정의
**jQRadar**는 설정 없이 붙는 Java(부분 Kotlin) **소프트웨어 진화 관찰 도구**다. 표면이 셋이다: **지도**(§3 — 지금 어디를 먼저 조사할 가치가 있는가; 기존 부채를 **첫날부터 발견할 수 있고**, 캠페인을 등록하면 **추적할 수 있다**), **변경 리포트**(§5.1 — 이 변경이 시스템을 BASE보다 어떻게 바꿨나), **부채 원장**(§5.5 — 조직이 앵커를 찍은 캠페인에서 우리가 실제로 나아지고 있나). 그 위의 Claude 연동 수정은 브랜치에서만, 샌드박스에서 검증되어, 증거와 함께 PR로 사람 앞에 놓인다(§6).

**세 엔진**: PMD(메트릭 + 참조 룰셋 + CPD), ArchUnit(`ClassFileImporter` + `ArchitectureMetrics`), JGit(log/diff; blame은 매 스캔 금지, 캠페인 생성 시 한정 1회만 — §5.6). OpenRewrite는 §6.5의 수정기.
---

## 2. 측정 계약 (G0 동결 대상)

### 2.1 파일 단위
| 기호 | 정의 | 엔진 | 비고 |
|---|---|---|---|
| `cx` | 파일 내 메서드 CYCLO 합 | PMD | Kotlin은 들여쓰기 복잡도(`cx_method="indent"`), 백분위는 언어별 |
| `loc` | NCSS | PMD | |
| `smells` | quickstart 룰셋 발견 `{p1,p2,p3,total}` | PMD | 점수 밖, 가중 없음 |
| `chg_commits` | W 안 파일을 만진 비머지 커밋 수 | JGit | **H·tc의 변경 단위(잠금)** |
| `chg_days` | W 안 변경된 서로 다른 UTC 날짜 수 | JGit | 기록·비교 실험용(P2) |
| `churn` | W 안 추가+삭제 라인 | JGit | |
| `union_dup_tokens` | CPD 발생 구간 합집합 토큰 수 | CPD | §2.6 |
| `dup_extent` | `union_dup_tokens / file_tokens` | CPD | 사실만 |
| `self_dup_tokens` | 같은 파일 안 반복 일치 토큰 | CPD | twin 아님 |
| `twins` | ≥1 일치를 공유하는 다른 파일 수 | CPD | |
| `active_twins` | `chg_commits ≥ 1`인 쌍둥이 수 | CPD+JGit | |
| `active_twin_ratio` | `active_twins / twins`; **`twins = 0`이면 `null`** | CPD+JGit | null이면 Dx 모집단 밖(§2.5) |
| `fan_in` | 이 파일 클래스들에 **정적 클래스 그래프에서 직접** 의존하는 프로젝트 내부 클래스 수 | ArchUnit | 테스트 클래스·리플렉션·DI 이름 기반 연결·외부 시스템 호출은 세지 않는다(§2.2 범위). F의 설명에 이 한계를 병기 |
| `age_last_days` | `HEAD_TIME − 마지막 비머지 커밋 커미터 시각` (일). 결정 불가(shallow clone·미커밋 신규 파일·rename 조상 복구 실패)면 **`null`**. 음수(잘못된 메타데이터·시계)도 `null`, `reason: invalid_metadata` | JGit | 앵커 §2.7. null이면 F도 null(§3.3) |
| `file_tokens` | CPD 토크나이저 전체 토큰 수 | CPD | |
| `distinct_authors_90d` | 최근 90일 이 파일을 만진 서로 다른 저자 수 | JGit | **익명 집계**. 저자는 메모리에서 해시로 세고 정체·해시 모두 저장하지 않음. 조정 비용·지식 집중의 지표(Bird 등 2011). `people.attribution=off`에서도 계산 |
| `ownership_max_share` | 최다 기여자의 커밋 비중(W 안) | JGit | 익명 집계. 낮으면 소유권 분산 |
| `minor_contributor_share` | W 안 커밋 비중 < 5%인 기여자들의 커밋 합 비중 | JGit | 익명 집계. Bird 등의 마이너 기여자 신호 |
| `team_count` | 이 파일을 만진 팀 수 | JGit + 조직 팀 매핑 | `people.attribution ∈ {team, individual}`일 때만 |

### 2.2 컴포넌트 단위 (Martin) — 그래프 계약
**`bytecode_scope`**: 프로젝트 자체 모듈의 main 출력 클래스만. 테스트·`@Generated`·`build/generated` 유래·서드파티·JDK 제외. 외부 타입 간선은 `external` 의사 노드로 접어 기록하되 Ca/Ce/I/A/D·CCD에서 제외. 이 전처리에 **적합성 픽스처 1개 필수**(`contract/graph/external-edges`).
**간선**: `JavaClass.getDirectDependenciesFromSelf()`, 컴포넌트로 접을 때 자기 간선·중복 제거(`class_edge_count` 별도).
**`component.strategy`**: `module`(멀티모듈 기본) / `auto`(최장 공통 접두어 아래 첫 레벨, 자식 1개면 하향, 60% 초과 자식은 추가 분할, 다중 루트는 루트별) / `depth:<n>`. 결과를 `reproduce`에 인쇄.
**지표**: `ArchitectureMetrics.componentDependencyMetrics` — `Ca, Ce, I, A, D`. `zone` 표기는 설명, 예외 병기. 순환은 Tarjan SCC.

### 2.3 시스템 단위 (Lakos)
`ArchitectureMetrics.lakosMetrics`. `CCD` = Σ(전이적 도달 컴포넌트 수, 자기 포함), `ACD = CCD/N`, `RACD = ACD/N`, `NCCD = CCD / ((N+1)·log₂(N+1) − N)`. 예: N=41, CCD=512 → `CCD_balanced ≈ 185.5`, `ACD ≈ 12.49`, `RACD ≈ 0.305`, `NCCD ≈ 2.76`. 시스템 숫자 하나, 추세용.

### 2.4 파일 쌍 단위
`shared` = 두 파일을 함께 만진 비머지 커밋 수. `tc = shared / min(chg_commits_a, chg_commits_b)`. 보고: `shared ≥ 5 ∧ tc ≥ 0.5`. 정적 의존 없으면 숨은 결합. `commit_granularity: coarse` 경고 병기.

### 2.5 백분위·분위 계약
**성분 백분위**
- 모집단 셋: `active`(W 안 `chg_commits ≥ 1`) — H; `dx`(`active` ∩ `twins ≥ 1`) — Dx; `all`(모든 적격 main 소스) — F. `cx`는 각 모집단 안에서 언어별.
- 방법: 경험적 CDF, 동점 평균 순위, `pct(x) = (rank_avg(x) − 1)/(N − 1)`. N = 1 → null; N < `percentile.min_population`(20) → null.
- 기록: 파일마다 `percentile_population.<field> = {population, lang?, n, reason?}`. `reason ∈ {not_in_active, no_twins, age_unknown, insufficient_population}` — **"값이 null"과 "모집단에서 제외"를 구분**한다.
- 표시: 원값·모집단 분포(중앙값·IQR·최대)와 함께. IQR < 중앙값의 25% → `population_note`.

**렌즈 백분위 — `interpretation`의 유일한 근거**
- 렌즈 값 자체의 백분위를 그 렌즈의 모집단에서 다시 계산한다: H는 `active`, Dx는 `dx`, F는 `all`. null인 렌즈 값은 제외, **0은 포함**. F는 대부분 0이므로 `investigate_first`는 사실상 "F > 0인 파일 중 cx×fan_in 상위" — 의도된 동작.
- 순위·동점·작은 N 규칙은 성분 백분위와 동일. 파일마다 `lens_percentiles.<lens>` 기록. §3.7의 `interpretation`은 이 값만 쓴다 — `H ≥ 90` 같은 절대 임계가 아니다.

**분위(quantile) 계약 — F의 P90**
- 방법: **type-7 선형 보간**(Hyndman–Fan). 정렬된 유효값 `x₁…x_N`, 위치 `h = 1 + q·(N − 1)`, `Q(q) = x_⌊h⌋ + (h − ⌊h⌋)·(x_⌊h⌋₊₁ − x_⌊h⌋)`. `(rank−1)/(N−1)`의 역함수와 일관.
- 픽스처 예: `[1,2,3,4,5,6,7,8,9,100]`, q = 0.9 → h = 9.1 → `9 + 0.1×91 = 18.1`.
- `P90(age_last_days)`는 **유효 나이만**(`≠ null`)으로. `population.all.age_last_days.valid_n` 기록.
- `reproduce.percentile_method = {rank: "average", formula: "(rank_avg-1)/(N-1)", quantile: "type7-linear"}`.
- **게이트는 원값**(§5).

### 2.6 CPD 집계 계약
- 스캔당 1회, main 소스, `minimumTokens=100`, identifier·literal 무시.
- **중복 클러스터(duplicate cluster)** = 같은 정규화 토큰 열의 **모든** 발생 {(파일, 시작, 끝 토큰)}. ID = `dup:<정규화 토큰 해시>:<토큰 수>`. 이것은 CPD `Match`의 원래 의미다 — A↔B와 C↔D가 같은 열이면 CPD가 이미 한 객체로 낸다.
- **파일별** `duplicated_ranges` = 그 파일의 모든 발생 구간 합집합(겹침 병합) → `union_dup_tokens`.
- **쌍별** `pair_dup_tokens(A,B)` = 발생 집합이 A·B를 모두 포함하는 클러스터들의 A쪽 구간 합집합 토큰 수(A = 경로 사전순 앞). 예: `[100,200)∪[150,250)` = **150**.
- **자기 중복**: 발생이 한 파일에만 있는 클러스터 → `self_dup_tokens`, twin 아님.
- `twins(A)` = `pair_dup_tokens(A,·) > 0`인 파일 수.

### 2.7 이력 계약
- **앵커**: `HEAD_TIME` = HEAD 커밋의 커미터 시각. 모든 "최근"·"경과"는 이 시각 기준. 같은 HEAD·같은 트리를 언제 재도 같은 값. `reproduce.window_anchor = {type: "head_committer_time", timestamp}`. `scanned_at`은 감사 메타데이터.
- **창 W**: 커미터 시각 ∈ `[HEAD_TIME − window.months(12), HEAD_TIME]`인 비머지 커밋, 최신순 최대 `window.max_commits`(2,000). 먼저 닥치는 상한 적용, `window_applied.bound_hit` 기록.
- 머지 커밋(부모 ≥ 2) 제외. rename: JGit `RenameDetector` 유사도 60; 후보가 여럿이면 tie-break = 유사도 → 경로 편집 거리 → 사전순, 동률은 `rename_ambiguous` 표기(픽스처). 거칠기: `median_files_per_commit > 20` → `coarse`.
- 저자 필드: **읽되 정체는 프로세스 밖으로 내지 않는다.** 기본(`people.attribution=off`)은 메모리에서 해시로 세어 익명 집계(§2.1의 `distinct_authors_90d` 등)만 낸다 — 해시도 저장하지 않는다(재식별 가능). `team`은 조직 제공 팀 매핑으로 ≥3인 집계, `individual`은 저자 사실을 실행 산출물 JSON에 낸다. 어떤 모드에서도 `.jqradar/`(커밋 대상)에는 정체를 저장하지 않는다. `declared_ai_assistance`는 커밋 트레일러(`Co-authored-by:` 봇, `Generated-by:`)에서 **선언된 것만** 읽고 추론하지 않는다. blame: **매 스캔에서는 사용하지 않는다.** 유일한 예외는 §5.6 — 캠페인 생성 시 원장 finding 영역에 한정해 1회. 매 스캔 경로에서 blame이 호출되면 픽스처가 실패한다.
- `check`: BASE·HEAD를 각자 앵커로 재지만 게이트 조건은 cx·중복·순환의 원값 델타라 앵커 차이에 영향받지 않는다.

### 2.8 식별자·환경 계약
- **파일 내용 ID**: 추적/미추적 무관 git blob 공식 `sha1("blob <size>\0" + bytes)`(JGit `ObjectInserter.Formatter.idFor`). 심링크 미추적, 모드·줄바꿈 정규화 없음.
- **세 가지 재현성 정체성**
  | 정체성 | 의미 | 불변성 |
  |---|---|---|
  | `repository_state_id` | 특정 git 트리의 정체성 | 트리가 같으면 동일. **캠페인 앵커의 봉인은 이것**(§5.4) |
  | `analysis_input_id` | 특정 툴체인·계약·입력으로 수행한 **분석**의 정체성 | 입력이 같으면 분석 결과 동일. **캐시 키** |
  | `validated_tree_id` | 실제 **검증된** 코드 트리의 정체성 | 검증 대상이 무엇이었는지 고정(§5.5, §6.3) |
- **`repository_state_id`** = 정렬된 `(path, content_id)` 전체의 sha256.
- **`analysis_input_id`** = sha256(`schema_version`, `contract_version`, `core_tool_version`, 엔진 버전(pmd·archunit·jgit), `history_backend`, 컴포넌트 전략과 그 알고리즘 버전, 측정 알고리즘 버전, 소스 파일 `(path, content_id)`, 클래스 파일 `(path, sha256(bytes))`, `window_anchor`, 창 안 커밋 SHA 목록, 모든 분석 파라미터). **원칙: 여기 포함되지 않은 입력은 분석 결과에 영향을 주어서는 안 된다** — 캐시 키와 `reproduce` 블록의 동일성을 계약으로 선언한다. 툴체인 버전이 빠지면 PMD 7.16과 7.17이 같은 키를 만들어 잘못된 캐시 적중이 생긴다 — 그래서 포함한다.
- **`validated_tree_id`** = 검증이 실행된 트리의 `repository_state_id`; 함께 `validated_analysis_input_id`를 기록. 검증은 결과와 **검증 입력 정체성**의 쌍이다.
- **`classes_id`** = `bytecode_scope` 안 `.class` 파일의 정렬된 `(상대 경로, bytes)` sha256. 실제 바이트 해시라 **지표 재현에는 이 값만으로 충분**하다.
- **`classes_reproduction_inputs`**("원인"이 아니라 "다시 만들려면 필요한 것"): jdk, 빌드 도구, kotlin 컴파일러, 컴파일 인자, 어노테이션 프로세서, 의존성 락. major.minor.patch.
- **`environment`**: 분석 도구 버전(pmd·archunit·jgit·git). major.minor.patch.

### 2.9 적합성 스위트
`contract/<계약>/<케이스>/` = 합성 리포(트리 + 스크립트 생성 git 이력) + `expected.json`. 모든 예시 JSON은 이 스위트의 픽스처이며 CI가 measures로부터 재계산해 대조한다(손으로 쓴 숫자 금지).
| 디렉터리 | 케이스(최소) | 게이트 |
|---|---|---|
| `percentile/` | 동점, N=1, N<20, 언어 분리, 0 팽창, **렌즈 백분위(H/Dx/F 각 모집단, 0 포함)**, **P90 type-7 예시(18.1)**, **IQR=0 → low** | G0 |
| `reproducibility/` | 같은 트리·다른 PMD 버전 → `analysis_input_id` 다름·`repository_state_id` 같음; 파라미터 하나 변경 → id 변경; `reproduce`에 없는 환경 변수를 바꿔도 결과 불변(원칙 검사); 두 머신 바이트 동일 | G0 |
| `cpd/` | 겹침 합집합(150), 무순서 쌍, 자기 중복, 임계 경계, **같은 열 4발생 = 클러스터 1개** | G0 |
| `history/` | 앵커 고정(같은 HEAD 다른 날짜), 머지 제외, rename, 상한 두 종류, coarse, **shallow clone → `age_unknown`** | G0 |
| `graph/` | 외부 의사 노드, auto 전략 4종, 순환, NCCD 검산 | G0 |
| `lens/` | H/Dx/F 각 모집단, composite null, confidence 최소 집계, tie-break, **F null(나이 미상)** | G1 |
| `gate/` | BASE 자격 고정, 모집단 드리프트 무영향, **발생 수준 새 중복(A↔B→A↔C는 잡고, B→C rename은 무시)** | G1 |
| `validation/` | 합격 함수(**`target_pairs` 전부**), BLOCK/WARN/INFO, relocation 증거, `structural` 위반 8종, **`validated_tree_id` 기록·`validation_scope` pre/post**, **실행 가능 라인 0 변경 → 커버리지 `not_applicable`**, **`validated_not_resolved` 4분기 각 1건**(검증 트리 재스캔 open / 머지 트리 다름 / 같음+이후 변경 / succession unknown) | G3 |
| `security/` | P9 벡터 | G3 |
| `ledger/` | 앵커 등록·`anchor_class` 얼림; **후속 판정 6종**(same/moved/split/merged/removed/unknown — A→B 이동+분할+C 예제 포함, 후속 집합에 합격 함수); **전이 모델 전 조합**(전이 종류 × 전이 커밋의 사건); **오귀속 5종 실패 사례**: ① 효과 없는 claim 머지 뒤 무관 PR이 해소 → `closed_unclaimed` + claim은 `merged_without_effect`, ② 먼저 해소한 무관 PR 뒤 오래된 claim 머지 → `superseded`, ③ 검증 실패 claim 머지 뒤 무관 PR이 해소 → `closed_unclaimed`(`closed_unverified` 아님), ④ claim 없이 해소 뒤 회귀 → `regressed`, ⑤ `target_pairs` 부분 선언 해소 → `partially_resolved`(`validator_mismatch` 아님); **인터페이스 추출로 재작성된 분할 → 시그니처 계보로 `split`**; **순환 finding의 과거 커밋 전이 → `transition_basis: source_imports` 표기**; "validated 뒤 머지 전 다른 PR 먼저 머지", "validated 머지 후 재악화 → regressed", "validated 머지 후 여전히 open → validated_not_resolved"; **scope 탈출 → `relocated_out_of_scope`**, **split 혼합(≥50% 밖 / 미만)**, scope 목표와 전역 가드레일; **reanchor → `supersedes` 계보, 옛 캠페인 불변**; 같은 finding 중복 claim; **(campaign, finding, pr) 멱등 재시도 → 파일 1개**; **툴체인 변경 시 앵커 재스캔 + 저장된 `anchor_class` 불변**; `--live`의 `stale_claim`; **재구성 결정성**(같은 커밋 → 바이트 동일 뷰, 아카이브 후 `--at` = 아카이브 전); `first_observed_estimate` 3방법; **매 스캔·매 change 경로에서 `.jqradar/` 쓰기 또는 blame 호출 시 실패** | G2b |
| `renderer/` | HTML에서 추출한 모든 숫자가 JSON에 존재(순수 함수), 판정 어휘 사전 검사(bad/poor/나쁨/위험/불량 …) 통과, aspect 토글 상태가 URL 해시에서 복원, 네트워크 요청 0건(자립형), 파일 5,000개 픽스처 렌더 시간 | G2 |

**`expected.json` 변경 규칙**: 기대값을 바꾸는 커밋은 `fixture_change {reason ∈ {library_behavior_change, contract_change, bug_fix}, library?, old?, new?, measure, note}`를 반드시 동반한다. 원인 분류 없이는 머지 불가 — 회귀 테스트가 "새 정답을 손으로 승인하는 테스트"로 변질되는 것을 막는 장치(P11).
---

## 3. 렌즈 — 지도(`scan`)

§3은 지도의 렌즈다. 철학 A.1이 1차 표면으로 정한 변경 리포트는 §5. 모든 성분은 §2.5 백분위. 표시는 소수 1자리, 계산은 반올림 전 값.

### 3.1 Hotspot — Tornhill-derived (헤드라인)
`H = 100 × sqrt( pct_active,lang(cx) × pct_active(chg_commits) )`
Tornhill 핫스팟에서 복잡도 프록시를 파일 CYCLO 합으로 바꾼 변형. 변경 단위는 **`chg_commits`로 잠금**. `chg_days`는 P2 비교 실험만이며, 압도적 결과가 있을 때만 다음 계약 개정에서 바꾼다.

### 3.2 Duplication Exposure
`Dx = 100 × sqrt( pct_dx(union_dup_tokens) × pct_dx(active_twin_ratio) )`, 모집단 `dx`(활성 ∧ twins ≥ 1).
**비율이 아니라 질량을 우선한다** — 200토큰 보일러플레이트가 전부 중복인 것보다 10,000토큰 서비스의 5,000토큰 중복이 보통 더 중요하다. `dup_extent`는 사실로만. twins=0인 파일은 Dx `null`(경쟁에 없다). 깨끗한 리포에서 `dx` N < 20이면 Dx 전체 `null` — "순위 매길 중복 노출이 없다"가 정직한 출력.

### 3.3 Frozen Core
`F = 100 × sqrt( pct_all,lang(cx) × pct_all(fan_in) ) × 𝟙[ age_last_days > P90_all(age_last_days) ∧ age_last_days ≥ 180 ]`
모집단 **`all`**(W 활동 없는 파일이 바로 F의 후보다). 시간 기준은 `HEAD_TIME`. `P90`은 §2.5의 type-7 분위, 유효 나이만. **이름보다 약하게 읽어야 한다**: F는 "복잡하고 정적 fan-in이 높고 오래 안 바뀐 코드"의 대리 지표 — **변경 위험 후보**이지 부채 판정이 아니다. 안정된 도메인 코어, 의도적으로 고정한 API, 테스트가 두터운 옛 코드가 다 여기 걸린다. 부채가 되는 것은 조직이 캠페인에 등록할 때다. **`age_last_days = null`이면 F = null** — "오래되지 않았다"와 "나이를 모른다"는 다른 상태이므로 0을 주지 않는다.

### 3.4 Architecture Context — 파일 점수가 아니라 맥락
파일마다 소속 컴포넌트의 `I, A, D, zone, cycle_id`를 **붙인다**. 곱하거나 더하지 않는다. 리포트에서는 컴포넌트 단위로 따로 보인다: D 상위 컴포넌트, 순환 목록(끊기 후보 간선 포함), NCCD(시스템 숫자 하나, 스캔 간 추세로만 — 이력 저장소 전까지는 두 점). `zone` 표기는 위치 설명이며 정당한 예외(유틸리티·도메인 코어)를 항상 병기한다(§2.2).

### 3.5 Hidden Coupling — 점수가 아니라 목록
`shared ≥ 5 ∧ tc ≥ 0.5`인 파일 쌍을 `tc` 내림차순으로, **정적 의존이 없는 쌍 우선**. 각 행에 `shared`·`chg_commits_a/b`·정적 의존 유무·`commit_granularity` 경고. 테스트-대상 쌍은 "test pair"로 표시하고 긍정 해석을 병기한다 — 파일이 진화하며 테스트도 갱신되고 있다는 신호일 수 있다. 판정하지 않는다(§2.4, §7.1 A5).

### 3.6 복합 점수(선택)
`--profile` 가중합, 기본 `H 0.5, Dx 0.3, F 0.2`. **세 렌즈가 모두 non-null일 때만 계산**, 아니면 `null` + `composite_note`(재정규화는 부풀리고 0 대입은 깎으므로 둘 다 하지 않는다). 헤드라인은 H.

### 3.7 priority · interpretation · confidence
- `priority` = 렌즈 값. 정렬 tie-break: `priority desc, path asc, id asc`.
- `interpretation`: **`lens_percentiles.<lens>`**(§2.5 렌즈 백분위) `≥ 0.90` → `investigate_first`, `≥ 0.75` → `investigate`, 그 외 `context`. 렌즈 값이 null이면 null. 백분위 임계이며 개수 자르기가 아니다.
- `confidence`(성분별): `low` ⇔ N < 50 **또는 IQR = 0** **또는** (중앙값 > 0 ∧ IQR < 0.25·중앙값) **또는** (`coarse` ∧ 성분이 `chg_commits`); `high` ⇔ N ≥ 200 ∧ 위 조건 없음; 그 외 `medium`. **렌즈 confidence = 기여 성분의 최소.** (`IQR = 0`을 따로 두는 이유: median = 0이면 `IQR < 0.25·median`은 0 < 0이 되어 완전 무분산을 놓친다.)
- `evidence`: 성분마다 `{measure, value, pct, population, n}` + 렌즈 `lens_pct`.
---

## 4. 시스템 구조

```
+---------------------------------------------------------------------------------------+
|                                     jqradar-core                                      |
|  PMD (metrics · quickstart rules · CPD)   ArchUnit (ClassFileImporter + ArchitectureMetrics)|
|  JGit (log · diff · co-change — 매 스캔 blame 없음)   Percentile/Quantile engine (§2.5)     |
|  Lenses H·Dx·F·Arch·Hidden (§3)          Change delta (§5.1)      Report model + JSON       |
|  HTML renderer (JSON의 순수 함수)          Contract fixture runner (§2.9)                    |
+---------------------------------------------------------------------------------------+
         |                     |                       |                        |
   jqradar-cli        jqradar-gradle-plugin      jqradar-ledger          jqradar-mcp (Claude 플러그인)
   scan · change      jqradarScan              campaign create|close      scan · get_hotspots · explain
   check · report     jqradarChange            |reanchor                  propose · apply · validate
   campaign · ledger  jqradarCheck             ledger view                open_pr
                      jqradarReport            한정 blame (생성 시 1회)          |
                      jqradarCampaign/Ledger                          jqradar-remediation
                                                                      (L2 샌드박스 안에서만)
                                                                      OpenRewrite 레시피 + LLM + 검증기
```

### 4.1 모듈과 책임
| 모듈 | 책임 | 의존 | 산출물 |
|---|---|---|---|
| **jqradar-core** | 측정(§2)·백분위(§2.5)·렌즈(§3)·변경 델타(§5.1)·재현 블록(§2.8)·JSON 직렬화·**인터랙티브 HTML 렌더러**(§7.1, d3 인라인 번들, 자립형 단일 파일, JSON의 순수 함수)·적합성 픽스처 실행. 빌드 도구·IDE·LLM 무지. `analysis_input_id`를 캐시 키로 쓴다 | pmd-java, pmd-kotlin(CPD), pmd-cpd, archunit(+metrics), org.eclipse.jgit, d3(인라인) | `report.json`, `change.json`, `*.html` |
| **jqradar-cli** | `.git` 상향 탐색; 소스·클래스 루트 자동 발견(Gradle `build/classes/{java,kotlin}/main`, Maven `target/classes`, `src/*/{java,kotlin}`); 못 찾으면 경로 플래그(파일 아님). `scan [--format json,html] [--profile]` · `change --base <ref>` · `check --base <ref> [--policy <file>]` · `report` · `campaign` · `ledger` | core, ledger | 위 + `gate.json`. exit: scan/change 0/2, check 0/1/2 |
| **jqradar-gradle-plugin** | `jqradarScan`(모든 main sourceSet classes에 의존, 멀티모듈은 루트에서 컴포넌트=모듈), `jqradarChange`, `jqradarCheck`(**유일하게 빌드를 깰 수 있음**), `jqradarReport`, `jqradarCampaign`, `jqradarLedger`. 확장 블록 없음 — 태스크 옵션만. configuration cache: 입력을 선언된 프로퍼티로, 실행 시 공유 상태는 Build Service(P10) | core, ledger | 위 |
| **jqradar-ledger** | 얇은 모듈: `campaign create|close|reanchor`(정의 파일 + 태그), `claim`(자기 브랜치에 사건 파일), 원장 **뷰** = 파생(앵커·HEAD 스캔) ⊕ 사건(`.jqradar/events/`), 한정 blame 1회(§5.6). **코드 상태는 저장하지 않는다.** 저장 위치는 리포 안 `.jqradar/`(D60) | core, org.eclipse.jgit | `campaigns/<name>.json`, `<name>.estimates.json`, `events/**/*.json`, 뷰 출력 |
| **jqradar-mcp** | MCP 서버 = Claude 플러그인. 툴 7종(§6.2). LLM에는 발견 관련 소스 **조각**·지표·컴포넌트 맥락만; 리포 전체·빌드 로그 원문은 전달 안 함. 저자 데이터는 `people.attribution=individual`일 때만, 그것도 익명 집계가 아니라 조직이 켠 범위에서. LLM 출력은 타입 제약 스키마(§6.6)를 통과해야만 `apply`에 도달. PR 토큰은 이 서버가 보유(브랜치 생성 + PR 생성만). 매니페스트 형식은 배포 시점 Claude 플러그인 문서에 맞춤 | core, ledger, remediation | 툴 응답, PR |
| **jqradar-remediation** | `propose`(옵션 + 재계산 가능한 예측 효과), `apply`(자체 OpenRewrite 레시피 `ReplaceRegionWithCall` + 전제조건 검사기, 나머지 LLM), `validate`(§6.3: 빌드·테스트·일시 jacoco·재스캔·재배치·등가 근거), 원장 예고 전이. **L2 샌드박스 안에서만 실행**(§6.6) | core, rewrite-java, jacoco(일시), 컨테이너 런타임 | `validate.json`, `jqradar/<finding-id>` 브랜치 |

### 4.2 데이터 흐름
```
소스 + 클래스 + .git ──► core.scan ──► report.json ──► HTML(지도) ──► 사람 / MCP get_hotspots·explain
BASE·HEAD 두 스캔 ──► core.change ──► change.json ──► check(조직 정책) ──► gate.json · exit code
                                           └─► touched_legacy_findings ──► ledger 예고 전이
campaign create ──► 태그 + campaigns/<name>.json(앵커 SHA·analysis_input_id 봉인) + 한정 blame(1회) ──► <name>.estimates.json
수정 PR(MCP 또는 `jqradar claim`) ──► 브랜치에 events/<campaign>/<finding>/<at>-pr<n>.json(claimed → validation 결과 갱신) ──► 머지되면 사건도 main에
jqradar ledger ──► 파생(앵커 스캔 ⊕ HEAD 스캔) ⊕ 그 커밋의 사건 파일 ──► 뷰(open / in_progress / validated / rejected / closed / regressed / removed)
campaign close ──► events/<campaign>/ 트리에서 제거 + <name>.summary.json — 과거는 git 이력, `ledger --at <commit>`으로 재구성
MCP propose → apply(브랜치) ──► sandbox.validate ──► validate.json ──► open_pr ──► 사람이 머지
```
- 모든 JSON은 `reproduce`(§2.8)를 갖고, HTML은 그 JSON의 순수 함수다(D28).
- `check`는 `change.json`만 읽는 정책 소비자. `ledger`는 `report.json`·`change.json`을 읽고 자기 파일만 쓴다.
- core는 코드를 수정하지 않는다. 수정은 remediation만, 그것도 샌드박스와 브랜치 안에서만. 기본 브랜치는 어떤 모듈도 건드리지 않는다.

### 4.3 제로 설정과 조직이 적는 자리
- `scan` · `change` · `ledger`: 설정 파일 없음. 파라미터는 코드 기본값이고 `reproduce.parameters`에 전부 인쇄된다.
- `check`: `jqradar.yml`(선택, 정책). `campaign create`: 인자로 조직이 적는 정의(앵커·범위·목표). **`people` 절**(`jqradar.yml` 안): `attribution: off(기본) | team | individual`, 팀 매핑 경로. **이 셋이 조직이 적는 자리다**(B.6). 전부 이름·소유자·해시가 산출물에 인쇄된다. `scan`은 `jqradar.yml`의 `people` 절만 읽는다 — 파라미터가 아니라 정책이므로 "scan은 무설정"의 유일한 예외로 명시한다.
- 신뢰 수준(§6.6): **L1** = `scan`·`change`·`check`·`ledger` — 정적, 코드 실행 없음, 자기 CI에서. **L2** = `apply`·`validate`·`open_pr` — LLM이 쓴 코드를 실행하므로 샌드박스 필수, 1차 빌드 시스템 Gradle(O12에 Maven).

### 4.4 언어·빌드 범위
- **Java**: 전 렌즈. **Kotlin**: CPD·ArchUnit·JGit 렌즈 포함, `cx`는 들여쓰기 복잡도이며 백분위는 Kotlin 모집단, `smells`는 `null`(0이 아님).
- **빌드 시스템**: 스캔·변경·원장은 Gradle·Maven 모두(클래스 루트만 있으면 됨). L2 검증은 Gradle 1차.

### 4.5 이력 백엔드 (P7이 참조)
- 기본은 **JGit 단독**. blame이 매 스캔 경로에서 빠진 뒤(D18) 남는 비용은 커밋 워크와 diff다. 순서대로: 창 상한(12개월 ∧ 2,000커밋) → `RevWalk.setRetainBody(false)` → 커밋별 변경 경로 집합을 `build/jqradar/history-cache`에 캐시(증분, 키 = 커밋 SHA) → rename 탐지는 창 안 커밋에만.
- **내용 주소 측정 캐시**: 국소 측정(파일 CYCLO·NCSS, 두 파일 간 `pair_dup_tokens`, 메서드 시그니처 목록)은 커밋이 아니라 **파일 내용**에만 의존하므로 캐시 키는 `(content_id[, twin content_id], 엔진 버전)`. 전이 스캔(§5.5)이 커밋을 100개 거슬러도 바뀐 파일만 다시 재고 나머지는 적중한다 — 전이 모델이 싼 이유.
- **전이 캐시**: finding별 전이 목록을 `(finding_id, commit, analysis_input_id)`로 캐시해 `--at`을 증분으로. 툴체인이 바뀌면(`analysis_input_id` 변경) 전체 재계산 — P7의 캐시 무효화 시나리오.
- 그래도 P7 예산을 넘으면 `--history-backend=native`(옵트인)로 `git log --name-status`·`git blame --porcelain`을 ProcessBuilder로 부른다. 옵트인인 이유: rename 추적·공백·blame 휴리스틱이 두 구현 사이에 달라 **같은 트리에서 다른 숫자**가 나올 수 있다. 조건: (a) 배터리 리포 적합성 테스트(O8) 통과, (b) `reproduce.history_backend{name, git_version}` 인쇄, (c) 백엔드가 다른 두 실행 사이의 델타·원장 전이는 거부.
- 한정 blame(§5.6)은 이 백엔드 위에서 캠페인 생성 시에만 돈다. 매 스캔 경로에서 blame이 호출되면 `contract/ledger` 픽스처가 실패한다.
---

## 5. 변경 리포트 · 부채 원장 · 게이트 — 보호와 개선

두 방향(A.1): **보호**는 `jqradar change --base <ref>` — 이 변경이 merge-base 대비 무엇을 바꿨나. **개선**은 부채 원장 — 조직이 앵커를 찍은 캠페인에서 부채가 실제로 줄고 있나(§5.4–5.7). `check`는 둘 위에 조직 정책을 얹는 소비자다. `scan`·`change`·`ledger`는 무설정, `check`와 캠페인 정의만 조직이 적는다(B.6).

### 5.1 `change.json` — A.1의 질문 그대로
| 질문 | 계산 |
|---|---|
| 복잡도가 얼마나 늘었나 | 변경 파일별 `cx` 원값 델타, 리포 총 `cx` 델타, 변경 파일의 최대 메서드 CYCLO 델타 |
| 변경이 어디에 집중되나 | 변경 파일 ∩ BASE H top-decile(자격 고정), 변경 파일의 컴포넌트 분포, BASE Dx·F 상위 파일과의 겹침 |
| 중복이 새로 생겼나 | `new_duplication`(발생 수준, rename 매핑 — §5.2) |
| 의존성이 어느 방향으로 확장됐나 | 컴포넌트 간선 집합 델타(추가·삭제 간선), 새 SCC, `external` 간선 수 변화 |
| 과거 취약 영역이 더 취약해졐나 | BASE Dx·F 상위 파일 중 변경된 것의 `union_dup_tokens`·`fan_in` 델타 |
| 리팩터링이 위험을 줄였나 | 수정 브랜치라면 `validate.json` 연결 |
| 이 변경이 닿은 기존 부채 | 변경 파일 안의 원장 finding과 각각의 델타·상태 전이 예고(§5.7) |
| 이 변경에 도구 관여가 선언됐나 | `declared_ai_assistance ∈ {true, false, unknown}` — 커밋 트레일러에서 선언된 것만, 추론 없음. 렌즈·원장·점수에 안 들어가며 사람 단위로 안 나온다. 조직이 `check`에서 정책(예: 선언된 AI 관여 변경에 post-merge 검증 요구)을 적을 수 있게, 그리고 A.3을 배터리에서 검증할 수 있게(P17). 선언이라 하한선이고 생략으로 우회 가능함을 표기 |
각 항목은 `{value_base, value_head, delta, evidence[]}`를 갖고 **판정 단어는 없다** — 판정은 `check`(정책)와 사람이 한다. A.4의 설명 문장("이 변경으로 … 증가했고, … 겹치며, … 두 위치에도 존재한다")은 렌더러가 이 구조에서 조립한다. 앵커는 각 스냅샷의 HEAD 시각이며 델타 조건은 시간 무관(§2.7).

### 5.2 새 중복의 정체성
클러스터 해시만으로는 부족하다: `BASE: A↔B`, `HEAD: A↔C`는 같은 클러스터 해시라 "기존"으로 보여 새 사본 C를 놓친다. **발생 수준**으로 정의한다:
> `new_duplication` = HEAD의 발생 ≥ 2인 클러스터에 속한 발생 중, `(rename 매핑 후 경로, 클러스터 ID)`가 BASE의 어떤 클러스터 발생에도 없는 것. 단순 rename(B→C, 내용 동일)은 매핑이 흡수한다.

### 5.3 게이트 — `check`, 조직의 정책
**BASE 자격 고정 + 원값 델타**(백분위 드리프트 무영향). `change.json`을 입력으로 받는다.

**기본 프로필 `jqradar-default-gate`**
| 조건 | 대상 | 기본값 |
|---|---|---|
| `new_duplication`이 변경 파일에 존재 | 변경 파일 | 클러스터 토큰 ≥ 100 → FAIL |
| 새 컴포넌트 SCC | 컴포넌트 그래프 | 1개라도 → FAIL |
| BASE H top-decile ∩ 변경 파일의 `cx` 원값 증가 | `eligible = topdecile_H(BASE)` | > 15% → WARN |
| 시스템 NCCD 증가 | 시스템 | > 5% → WARN. Δcomponents·ΔCCD·ΔNCCD를 함께 표시하고, **컴포넌트 집합이 바뀌면 WARN 대신 `context_changed`**(N 변화와 의존 악화를 섞지 않는다) |
| 새 P1 smell | 변경 파일 | → WARN |
| 절대 점수 임계 | — | 없음 |
exit 0/1/2. `jqradar.yml` 선택, `check`만. 정책 이름·해시·출처를 `gate.json`에.

### 5.4 캠페인 정의 — 조직이 등록하는 고정 기준선
보호 기준선(merge-base)은 PR마다 움직여 "캠페인 시작 이후 총 중복이 30% 줄었다"를 잴 고정점이 없다. 그래서 조직이 **캠페인**을 등록한다: `jqradar campaign create --name debt-2026Q4 --anchor <ref> [--scope <components|paths>] [--target <metric><op><value>]…`
- `anchor`: 불변 트리 — **`repository_state_id`와 커밋 SHA로 봉인**(생성 시 쓴 `analysis_input_id`는 재현용으로 함께 기록). 툴체인이 바뀌면 파생 층은 **앵커 트리를 현재 툴체인으로 재스캔**해 HEAD와 같은 도구로 비교한다(앵커는 리포트가 아니라 트리라 언제나 가능). 여러 캠페인이 공존할 수 있다.
- **`anchor_class`는 결정 산출물**: 캠페인 생성 시 계산해 `campaigns/<name>.anchor-classes.json`에 저장한다. 코드 상태가 아니라 조직의 얼린 착수 순서이므로 저장이 정당하고, 재스캔이 백분위를 흔들어도 변하지 않는다.
- **`reanchor`** = 앵커를 바꾸는 명령이 아니라 **기존 캠페인을 종료하고 `supersedes` 계보를 가진 새 캠페인을 만드는 명령**(`debt-2026Q4` → `debt-2026Q4.r2`). 옛 캠페인 파일·태그는 불변.
- `scope`: 선택이지만 권장 — 전부 고치지 않는다(A.8). scope 없는 캠페인 생성에는 경고.
- `targets`: 선택. 조직이 적는 목표(예: `union_dup_tokens_total <= 6000`, `ledger.high.open <= 20`). **도구는 정하지 않고 담고 추적한다.**
- **`campaign_mode`**: 목표가 있으면 `target_driven`, 없으면 `tracking_only`. 목표 없는 원장은 **부채 추적기이지 개선 관리가 아니다** — CLI·UI가 모드를 항상 표기하고, `goal_status ∈ {achieved, on_track, off_track, no_progress, moving_away, insufficient_history}`를 낸다(두 점 선형 외삽 대비 목표; `current == anchor`는 `no_progress`, 목표 반대 방향은 `moving_away`, 앵커 후 커밋 없으면 `insufficient_history`). `tracking_only`는 `not_defined`만.
- **scope 회계** — scope는 *finding을 고르는 것*이고 *회계 경계*가 아니다. 안 그러면 문제를 scope 밖으로 옮기는 것이 달성이 된다.
  - **`targets`는 scope 안**(`scope.union_dup_tokens_total <= 6000`, `ledger.high.open <= 20`) — 캠페인의 실제 개선 목표.
  - **`guardrails`는 리포 전체**(기본: `repo.union_dup_tokens_total <= anchor`, `repo.cx_total <= anchor`) — scope 밖으로 부채를 밀어내지 않았는지. 질량 목표를 리포 전체로만 두면 재배치는 막지만 *주의 분산*(scope 밖의 쉬운 중복 10개로 전역 총량 달성)이 생긴다 — 그래서 목표와 가드레일을 나눈다.
  - `relocated_out_of_scope`(§5.5) finding은 개수 목표에서 **open으로 계속 센다**.
  - scope 변경은 `reanchor`(= 새 계보)다. 과거 캠페인 파일은 불변이고 과거 성과는 소급 변경되지 않는다.
- 정의는 이름·소유자·해시·`campaign_mode`와 함께 `campaign.json`에 인쇄된다(B.6).

### 5.5 부채 원장 — 셋째 표면
원장은 **파생 층 ⊕ 사건 층**이다. 이 구분이 원장의 정체다.

**파생 층 — 저장하지 않는다.** 앵커 스캔(불변 태그, 언제 재도 같다)과 HEAD 스캔에서 계산한다: `origin ∈ {baseline, introduced}`(앵커에 있었나), 파생 상태 `open / improving / resolved / removed`(집합 차 + 값 델타, rename 매핑), `anchor_class`, `anchor_values`·`current_values`, `change_exposure_90d`(git log), `debt_age`(§5.6). 실질은 **`jqradar change --base <앵커>`** — 보호 기준선 대신 캠페인 앵커를 BASE로 준 변경 리포트다. 저장하지 않는 이유(B.4): 저장은 틀리면 남고, 계산은 틀려도 다음 실행에서 고쳐진다. RuboCop `.rubocop_todo`·Detekt baseline이 부패하는 이유가 목록을 저장하기 때문이다.

**사건 층 — 저장한다.** 코드에서 파생되지 않는 것: *어떤 경로가 이 finding을 겨눴고, 무엇을 검증했고, 결과가 어땠나.* 레코드:
`{schema, provenance: {repository_sha, created_by}, campaign, finding_id, claim_id, pr, branch, claim_base_sha, claimed_at, actor_type ∈ {mcp, cli}, validation: {result ∈ {passed, failed, none}, scope ∈ {pre_merge, post_merge}, validated_head_sha, validated_tree_id, validated_analysis_input_id, validate_hash, at}}` — 코드 상태 필드는 없다.
- **`actor_type`은 경로이지 사람이 아니다.** principal은 없다 — 행위 추적이지 개발자 지표가 아니다(A.6·B.3).
- **멱등성**: `claim_id = hash(campaign, finding_id, pr)`, 파일은 **`(campaign, finding, pr)당 하나**(`.jqradar/events/<campaign>/<finding-id>/pr<n>.json`). `open_pr` 재실행·CI·MCP 재시도는 브랜치 안의 같은 파일을 덮어쓴다.
- **머지 전 = 가변 초안, 머지 후 = 불변 사건.** "append-only"는 main에 대한 말이다. `open_pr`(MCP)이나 `jqradar claim <finding-id>`(사람)가 쓴다.
- **검증은 결과 + 검증 입력 정체성이다.** `validated_tree_id`가 없는 `passed`는 `none`으로 취급한다(B.4 둘째 원칙).

**`anchor_class ∈ {high, medium, low}`**: finding의 렌즈 백분위를 **앵커 시점에 얼린다**(`≥ 0.90` high, `≥ 0.75` medium, 그 외 low). finding당 불변. 이유: 지도의 `interpretation`은 항상 상위 10%를 만들어 최악을 고쳐도 다음 10%가 `investigate_first`로 올라온다 — 개선이 라벨에서 보이지 않고, 이길 수 없는 게임처럼 느껴져 팀이 도구를 버린다. 얼린 분류는 고치면 `high` 개수가 줄고 다시 늘지 않는다. 리포 내부 기준이라 B.3의 사회적 근거는 그대로다.

**finding 정체성 계약.** "같은 finding"은 종류별로 정의한다:
| finding | 정체성 |
|---|---|
| Hotspot(H) / Frozen(F) | rename 매핑 후 파일 경로 + 렌즈 |
| 중복(Dx) | 클러스터 ID(정규화 해시 + 토큰 수) + 발생 파일 |
| 순환 | SCC 멤버 컴포넌트 집합의 정렬 해시 |
| Hidden Coupling | 정렬된 파일 쌍 |

**후속 판정 `succession` — kind별 알고리즘.** 상위 어휘는 같되 알고리즘은 종류별이다: **H/F = 파일 계보**(rename 매핑; 분할·병합은 토큰 출처로 보조), **Dx = 토큰 계보**(앵커 파일의 메서드 몸체 토큰이 HEAD 어느 파일에 있는가 — 기존 CPD 토큰 기계로 두 트리 대조; 토큰 출처가 실패하면 **메서드 시그니처 계보**(이름 + 파라미터 타입, PMD AST — 소스 수준이라 과거 커밋에서도 국소)를 보조로 — 인터페이스 구현으로 옮기며 코드를 다시 쓰면 Type-2 정규화가 못 따라가기 때문), **순환 = SCC 계보**(멤버 집합 same/shrunk/grown/dissolved/merged), **Hidden = 쌍 계보**(양쪽 파일의 rename 매핑). 캠페인 finding(수백)에만 돌린다. `unknown`은 해당 kind의 알고리즘이 판정하지 못한 경우로 한정 — 토큰 모델을 SCC에 억지로 적용해 `unknown`을 넓히지 않는다.
| `succession` | 규칙 | 해소 판정 |
|---|---|---|
| `same` | 경로 동일 또는 rename 매핑 | 해당 파일에 합격 함수 |
| `moved` | **앵커 finding 토큰**의 ≥ 80%가 다른 한 파일로 | 후속 파일에 합격 함수 |
| `split` | **앵커 finding 토큰**이 둘 이상 파일로(각 ≥ 20% — 분모는 앵커 토큰이므로 후속 파일의 보일러플레이트가 비율을 희석하지 않는다) | **후속 집합 전체**에 합격 함수 — 예: cx 합이 앵커 대비 ≥ 20% 감소 ∧ 최대 메서드 CYCLO 비증가. "문제를 옮긴 것"을 개선으로 표시하지 않는 규칙 |
| `merged` | 여러 앵커 파일의 토큰이 한 HEAD 파일로 | 병합 파일에 합격 함수, 관련 앵커 finding을 묶어 표시 |
| `removed` | 토큰이 어디에도 없음 | `removed`(해소로 세지 않음 — 삭제와 해소는 다르다) |
| `unknown` | 위 어느 것도 아님 | `id_drift`로 표시. P14가 이 비율을 잰다 |
예: A.java가 B.java로 이동하며 메서드가 분할되고 일부가 C.java로 갔다면 `split → {B, C}`이고, 해소는 B·C 합으로 판정한다. **scope 혼합**: 앵커 토큰의 ≥ 50%가 scope 밖 후속으로 갔으면 `relocated_out_of_scope`; 미만이면 후속 집합 **전체**(scope 밖 부분 포함)에 합격 함수; 후속이 전부 사라졌으면 `removed`.

**뷰 = 파생 ⊕ 사건 — 전이 모델.** `validated`는 *PR 시점의 검증*이고 `closed`는 *앵커 대비 해소*다. 둘을 결합할 때 **인과를 시간 순서로 대신하지 않는다** — "지금 resolved인가 × 마지막으로 머지된 claim은 무엇인가"로 상태를 정하면 마지막에 머지된 claim이 남의 성과를 가져가고(효과 없는 claim이 뒤에 머지된 경우), 검증 실패 PR이 남의 해소에 기소되고(`closed_unverified` 오귀속), claim 없이 닫힌 부채의 회귀가 보이지 않는다. 그래서 상태는 **전이 이력**으로 계산한다.

- **쓰는 사건**은 `claimed`·`validation_passed`·`validation_failed`뿐. 머지 여부는 git에서 파생한다 — 사건 파일이 main first-parent 이력에 처음 나타난 커밋이 그 사건의 머지 커밋. `superseded`·`merged_without_effect`는 파생이지 저장되는 사건이 아니다.
- **파생 상태** `derived ∈ {open, improving, resolved, removed, introduced}` + `succession`. 해소·회귀 판정은 합격 함수의 **원값**(`pair_dup_tokens`, 메서드 CYCLO, SCC 존재)이라 백분위가 필요 없고, finding의 후속 집합 파일(+쌍둥이)만 재면 되므로 **국소 재스캔**으로 어느 커밋에서든 계산할 수 있다.

**전이 계산.** 캠페인 finding F마다:
1. **후보 커밋** = main first-parent 이력에서 F의 후속 집합 파일을 건드린 커밋 ∪ F의 사건 파일을 실은 커밋.
2. 각 후보 C에서 `derived(F, parent(C))`와 `derived(F, C)`를 국소 재스캔해 **전이**를 판정: `open→resolved`(해소), `resolved→open`(회귀), `open→improving`, `→removed`, succession 변화.
3. **귀속 = 전이가 일어난 커밋.** 해소 전이 커밋이 F의 사건을 실었으면 그 claim의 성과, 아니면 커밋 SHA에 귀속되고 어떤 claim에도 귀속되지 않는다.
4. 전이를 만들지 못한 머지 사건은 **`merged_without_effect`**이며 원인은 그 사건의 **검증 트리**(`validated_tree_id`) 재스캔에서 시작해 가른다(아래 표).
5. **현재 상태 = 마지막 전이.** 해소 뒤 회귀가 있으면 claim 유무와 무관하게 `regressed`.

**상태표 — 전이 × 그 커밋의 사건**
| 마지막 전이 | 전이 커밋의 사건 | 유효 상태 | 비고 |
|---|---|---|---|
| open→resolved | `validation_passed` | **closed** | 그 claim의 성과. 검증 트리 ≠ 머지 트리면 `merge_drift: true` 병기 |
| open→resolved | 없음 | **closed_unclaimed** | 커밋 SHA에 귀속. 어떤 claim도 성과를 갖지 않는다 |
| open→resolved | `validation_failed` | **closed_unverified** | **해소를 만든 그 커밋이** 검증 실패 사건을 실은 경우에만. 다른 커밋의 실패 사건은 이 판정에 닿지 않는다 |
| resolved→open (해소 이후) | 무관 | **regressed** | claim 없이 닫혔던 부채의 회귀도 잡힌다. `regressed_from`에 해소 커밋 |
| 전이 없음, 앵커 이후 사건 없음 | — | **open** / **improving** | improving은 원값 ≥ 20% 감소 ∧ 합격 미달 |
| 전이 없음, 열린 claim 브랜치 | — | **in_progress** | `--live`에서만(아래) |
| →removed | 무관 | **removed** | 삭제는 해소가 아니다 |
| 앵커 이후 신규 | — | **introduced** | 보호 게이트의 영역 |
| succession = unknown | 무관 | **id_drift** | 숨기지 않는다 |

**`merged_without_effect`의 원인 판정.** 검증 트리 재스캔부터 시작한다 — 그래야 검증 계약의 실패와 머지 과정의 변화가 섞이지 않는다.
| 검증 트리 재스캔 | 부가 조건 | 판정 | 뜻 |
|---|---|---|---|
| 선언한 `target_pairs`가 **open** | 무관 | **validator_mismatch** | 검증이 통과했다고 한 트리에서도 선언 범위가 해소되지 않았다 — 검증과 합격 함수의 계약 실패. **이 이름은 이 경우에만** |
| 선언 부분집합은 resolved, finding 전체는 open/improving | 선언이 부분집합 | **partially_resolved** | 선언된 부분 해소. 검증기는 옳았다. 원장에 "k/n 쌍" 표기 |
| resolved | 머지 트리 ≠ 검증 트리 | **merge_drift** | 리베이스·충돌 해결·main 전진으로 머지된 코드가 검증된 코드와 다르다. **실패가 아니라 구분자** |
| resolved | 이 사건의 머지 전에 다른 커밋이 이미 해소 전이를 만들었음 | **superseded** | 성과는 그 커밋(또는 그 claim)의 것 |
| succession unknown | 무관 | **id_drift** | 정체성 추적 실패 |
`closed`에는 `merge_drift`와 `validation_scope`를 함께 표기한다 — 머지는 새 트리를 만들므로 tree equality 자체를 요구하지 않는다. 머지 트리에서의 검증(post-merge validate 잡)을 요구할지는 조직이 `check` 정책에 적는다(B.6).

**비용.** finding의 파일을 건드린 머지 수만큼의 **국소** 재스캔이며 내용 주소 측정 캐시와 전이 캐시(§4.5)로 대부분 적중한다. P7 매트릭스의 "전이 스캔 대상" 행이 이것을 잰다.

**국소성의 한계 — 순환 finding.** 전이 스캔이 국소인 것은 Dx·H·F(소스 원값)에만 참이다. **순환(SCC) finding의 해소·회귀는 컴포넌트 그래프, 즉 바이트코드가 필요**하고 과거 커밋에는 클래스가 없다(§0의 스냅샷 한계). 처치: (a) `report.json`이 남아 있는 커밋(자기 CI 아티팩트·`docs/self/`)에서는 정확히, (b) 그 사이 커밋에서는 PMD AST의 **import 기반 소스 의존 그래프**로 근사하고 `transition_basis: source_imports`를 표기, (c) 근사와 바이트코드 그래프의 불일치율은 P14가 잰다. 뷰는 근사 구간을 숨기지 않는다.

- **`in_progress`는 main에서 보이지 않는다.** claim 파일은 머지 전엔 브랜치에만 있다. 그래서 뷰가 둘이다: **`ledger --at <commit>`** — 머지된 사건만, 결정적, 재구성 테스트의 대상; **`ledger --live`** — `refs/heads/jqradar/*`와 원격 동일 refs의 claim을 더한 시점 의존 뷰. `--live`에서 N일(기본 30) 넘게 미머지인 claim은 `stale_claim`.

**`anchor_class`와 `current_priority`는 다른 질문에 답한다.** `anchor_class`(불변)는 *캠페인 진척*("high 20개 중 몇 개를 닫았나")용이고, `current_priority`(HEAD 렌즈 값과 `interpretation`)는 *지금 무엇을 볼 것인가*용이다. 앵커에서 high였던 파일이 지금 H 40이면 진척으로는 성과이고 조사 우선순위로는 낮다 — 한 화면에 둘을 나란히 두고 역할을 표기한다. 원장 정렬 기본은 `anchor_class`(진척), "다음에 고칠 것"은 `current_priority`.

**기본 정렬**(점수가 아니라 인쇄되는 키): `anchor_class desc, change_exposure_90d desc, debt_age desc` — **변경이 닿는 부채부터**(A.8). 뷰 기본 top 20. `business_criticality`는 조직이 캠페인 `scope`로 표현한다.

**원장 뷰** `jqradar ledger [--campaign] [--at <commit>]`: 캠페인별 상태 카운트, `anchor_class`별 추이, 목표 대비 진전, 최근 변경이 닿은 부채, **앵커 값과 현재 값 나란히**(앵커의 노화를 숨기지 않기 위해). 어느 커밋을 체크아웃해도 그 시점 원장이 결정적으로 재구성된다. 리포 간 비교 없음.

**저장 — 별도 서버 없음, 리포 안 `.jqradar/`, 커밋 대상(D60).**
```
.jqradar/
  README.md                        # 무엇인지, 손으로 편집하지 않는다
  campaigns/
    debt-2026Q4.json               # anchor {tag, sha, analysis_input_id, window_anchor}, scope, targets, owner, created_at, definition_hash
    debt-2026Q4.estimates.json     # first_observed_estimate (§5.6). 파생이지만 비싸고 결정적 — 모두가 blame을 다시 돌리지 않게 커밋. `--recompute`로 재생성
    debt-2026Q4.anchor-classes.json # anchor_class 결정 산출물 — 생성 시 1회, 불변
    debt-2026Q4.summary.json       # campaign close 시: 최종 카운트, 종료 커밋
  events/
    debt-2026Q4/
      fnd-dx-dup-3f9a…@order-OrderService/
        pr482.json                   # (campaign, finding, pr)당 하나 — 멱등
```
- **무한증식이 아니다.** 일반 PR(`scan`·`change`·`check`)은 아무것도 쓰지 않는다. 쓰는 것은 캠페인 관리와 finding을 겨눈 수정 PR뿐이고, 수정 PR당 파일 하나다. `campaign close`가 `events/<campaign>/`을 트리에서 제거하고 `summary.json`을 남긴다 — 과거는 git 이력이 갖고 `ledger --at`으로 재구성된다. 트리 크기는 **활성 캠페인 × 그 범위의 수정 PR 수**로 묶인다(캠페인 1개·주 5 PR·분기 종료 → 최대 ~65파일, ~20KB). 6개월 넘은 활성 캠페인에는 종료를 권고한다.
- **충돌이 없다.** 파일 경로에 finding ID와 PR 번호가 들어가 두 사람이 다른 finding을 고치면 경로가 다르고, **같은 finding**을 고치면 파일이 둘 생기고 뷰가 `in_progress (PR 2개)`를 보인다 — git 충돌이 아니라 조정 신호. `jqradar claim`은 main에 열린 claim이 있으면 경고한다. 캠페인 정의 편집은 정책 파일의 정상적 충돌(드물고 사람이 푼다). 스쿼시·리베이스에서 파일은 살아남는다. jQRadar를 안 쓰는 팀원에게는 아무 영향이 없다 — 훅도 자동 실행도 없다.
- `.gitattributes`에 `.jqradar/events/** linguist-generated=true` — 포지가 diff를 기본 접는다. 그래도 그 파일은 잡음이 아니라 "이 PR이 부채 X를 겨눴다"는 선언이다.
- `.jqradar/`는 설정이 아니다. `scan`·`change`는 이 디렉터리 없이 완전히 동작하고, 캠페인을 만드는 순간 처음 생긴다. 조직이 적는 것은 여전히 `check` 프로필과 캠페인 정의 둘뿐이다(B.6).
- 서버가 필요해지는 때는 여러 리포를 한 화면에 모으는 조직 대시보드(O6)뿐이고, 그때도 리포가 시스템 오브 레코드이며 서버는 읽는 소비자다. 포지 PR 코멘트에 `validate.json` 요약을 남기는 것은 좋은 UX지만 미러이지 기록이 아니다. 리포에 파일을 넣기 싫은 조직은 동반 리포(`--ledger-repo <url>`)를 쓸 수 있으나 "PR이 자기 사건을 싣는다"를 잃으므로 기본이 아니다.

**선례와 다른 점 — 이 조합은 새것이다.**
| 요소 | 선례 |
|---|---|
| PR당 파일 하나, 릴리스(종료) 때 소비·삭제 | Changesets(`.changeset/`), Towncrier, reno, Changie |
| 기존 위반을 등록해 점진적으로 갚음 | RuboCop `.rubocop_todo.yml`, Detekt/Android Lint/PHPStan/Psalm baseline, ESLint bulk suppressions |
| 개선만 허용하는 기준선 | Betterer, 커버리지 래칫 |
| append-only 기록 | ADR |
| 작은 포인터 + 외부 산출물 해시 | DVC, Git LFS |
| 기준 시점 | SonarQube New Code Period(서버 설정 — 우리는 리포 태그) |
의도적 차이 둘: (1) baseline 파일들은 **목록**을 저장해 부패하지만 우리는 목록을 파생하고 **사건**만 저장한다. (2) Betterer류 래칫은 좋아지면 기준 파일을 덮어써 "원래 95였다"를 잃지만 우리는 앵커를 불변 태그로 두고 개선을 그 대비로 잰다. 반대 선례: Terraform state는 크고 가변이며 동시 쓰기가 있어 리포에 두지 않는다 — 우리 사건 파일이 리포에 있어도 되는 이유는 정확히 그 반대 성질(작고, 머지 뒤 불변, PR당 하나)이고, 그 성질이 깨지는 순간(매 스캔이 무언가를 쓰기 시작하면) 같은 이유로 리포를 떠나야 한다. 부품은 검증됐지만 조합은 검증되지 않았다 → **P15(파일럿)**. 온보딩 문서는 새 용어 대신 "`rubocop_todo`처럼, 단 목록 대신 사건을 저장하고 `changesets`처럼 종료 때 접는다"로 설명한다.

### 5.6 한정 blame 계약 — `first_observed_estimate`
원장의 `first_seen`(캠페인 등록 시각)만으로는 브라운필드 첫날 모든 부채가 "나이 미상"이 된다 — 브라운필드가 가장 알고 싶은 것이 바로 그 나이다. blame을 **한정 재도입**한다. 매 스캔 리포 전체 blame(병목)과는 비용 구조가 다르다.
- **언제**: 캠페인 생성 시 1회. 매 스캔·매 `change`에서는 절대 돌리지 않는다(픽스처로 강제).
- **무엇에**: 원장에 등록된 finding의 영역만(수백 건). 리포 전체 아님.
- **방법**: 중복 finding은 `git log -S`(pickaxe, 정규화 전 원문 첫 줄) 또는 영역 blame 중 저렴한 쪽; 핫스팟·Frozen finding은 파일의 최초 커밋(rename 추적) — blame 불필요. 레코드에 기록: `first_observed_estimate {value, method ∈ {pickaxe, region_blame, file_first_commit, unknown}, confidence}`.
- **의미**: 이것은 부채의 *최초 발생 시점*이 아니다. 파일 최초 커밋은 현재 복잡도가 생긴 시점이 아니고, pickaxe는 정규화 토큰 정체성과 어긋날 수 있고, rename 뒤 같은 코드가 여러 번 재작성됐을 수 있다. 그래서 이름이 `first_observed`이고, UI 고정 문구는 **"이 finding과 관련된 이력 흔적을 이 방법으로 처음 확인한 시점"**이다. `debt_age`는 그 추정에 대한 나이다.
- **저장**: `.jqradar/campaigns/<name>.estimates.json`에 커밋한다(파생이지만 비싸고 결정적 — 모든 개발자가 blame을 다시 돌리지 않게). `--recompute`로 재생성 가능. 같은 이력·같은 방법이면 결정적이라 B.4를 지킨다.
- **비용 상한**: 캠페인 생성 P95 ≤ 10분(P13). 초과 시 `method: unknown`으로 남기고 진행한다.
- 레코드에 **증거**를 붙인다: `evidence: {commit, path, range}` — "왜 이 날짜인가"를 사람이 확인할 수 있게.
- `debt_age = HEAD_TIME − coalesce(first_observed_estimate.value, first_seen)`.

### 5.7 변경 리포트와 원장의 연결
`change.json`에 **`touched_legacy_findings[]`**: 변경 파일 안의 캠페인 finding(파생) 각각에 대해 `{id, anchor_class, status_before, delta, status_after_if_merged, claimed_by_this_pr}`. "이 PR은 부채 3개를 건드렸고 1개 개선, 2개 그대로." 브라운필드에서 가장 센 문장이다 — **당신이 만지는 곳의 부채부터 줄인다.** 판정 단어는 없다.
---

## 6. 수정 워크플로

### 6.1 원칙
- 도구는 기본 브랜치를 절대 건드리지 않는다. 모든 적용은 `jqradar/<finding-id>` 브랜치.
- 검증하지 못한 변경은 PR 제목·본문에 **not_validated**와 사유를 쓴다. 조용히 통과시키지 않는다.
- 아키텍처(인터페이스 추출, 컴포넌트 분리, 순환 끊기)는 **제안만** 한다. 테스트로 검증되지 않는 설계 결정이고, v2.1의 D 오스코프가 보여준 대로 잘못된 자동 제안이 가장 쉽게 나오는 자리다.
- 모든 빌드·테스트·재스캔 실행은 §6.6 샌드박스 안에서만.
- 수정 PR은 자기 사건 파일을 자기 diff에 싣는다(§5.5). 원장 상태는 저장되지 않고 머지 뒤 파생 ⊕ 사건으로 계산된다.

### 6.2 MCP 툴
| 툴 | 입력 | 출력 |
|---|---|---|
| `scan` | 경로, 창 | 리포트 ID, 요약 |
| `get_hotspots` | `lens ∈ {H, Dx, F, hidden, arch}`, `n` | 렌즈별 top-n — `priority · interpretation · confidence · evidence`(§3.7) |
| `explain` | 파일 또는 finding ID | 성분 원값·백분위·모집단 n·`lens_percentiles`, 쌍둥이 위치, 공변경 파트너, 컴포넌트 맥락, 캠페인 상태(있으면) |
| `propose` | finding ID | 수정 **옵션들**과 각 옵션의 예측 효과(재계산 가능한 것만: 중복 토큰 감소량, 순환 해소 여부, 컴포넌트 D 변화), 옵션별 `equivalence_basis` 예상, `target_pairs`. **순위 없음**. 아키텍처 옵션은 제안까지 |
| `apply` | finding ID, option ID | 새 브랜치에 적용. 기계적 부분은 OpenRewrite(§6.5), 나머지는 LLM. 아키텍처 옵션은 거부하고 `propose` 결과를 반환. 사건 파일 `claimed` 기록 |
| `validate` | 브랜치 | §6.3 검증, `validate.json`, 사건 파일에 `validation` 결과 갱신 |
| `open_pr` | 브랜치 | 전후 지표·검증 결과·`not_validated` 사유·`touched_legacy_findings`를 담은 PR. 사람이 머지 |
LLM에 전달하는 것과 출력 제약은 §6.6.

### 6.3 검증 계약
`verdict ∈ {validated, not_validated}`, "validated ≠ 등가 증명" 고정 문구.
1. `build` 통과.
2. `tests` 통과 + 변경 라인 커버리지 ≥ 0.8(일시 jacoco). 측정 불가 → `not_validated: no_line_coverage_data`. **변경된 실행 가능 라인이 0**(상수·DTO 이동, 어노테이션·시그니처만 변경 등 JaCoCo가 실행 가능으로 세지 않는 변경)이면 커버리지 검사는 `not_applicable`(실패 아님)이고 검증은 빌드·전체 테스트·재스캔·`equivalence_basis`(`structural` 또는 `tests`)로 성립한다 — `coverage_basis: not_applicable_no_executable_lines` 기록. 인터페이스 추출류 아키텍처 변경은 D6에 의해 `apply` 대상이 아니다.
3. `metric_validation`:
   - **목표 개선 합격 함수(지표별)** — 240→239가 "개선"이면 엔진은 편법을 찾는다:
     | 발견 종류 | 합격 |
     |---|---|
     | 중복 | `propose`가 명시한 **`target_pairs` 전부** `pair_dup_tokens = 0` **이고** 새 `new_duplication` 발생 없음. 기본 `target_pairs` = 대상 파일의 모든 쌍; 부분만 겨누면 PR에 "부분 해소(k/n 쌍)" 표기 |
     | 순환 | 해당 SCC 소멸 **이고** 새 SCC 없음 |
     | 복잡도 | 목표 메서드 CYCLO ≥ 20% 감소 **이고** 파일 내 최대 메서드 CYCLO 비증가 — **기본 수정 휴리스틱**이며 P1a류 검증 임계가 아니다. 20%는 실증되지 않았고 조직이 `check`에서 바꿀 수 있다 |
   - 신규 발견 차등: BLOCK(새 순환·새 CPD ≥100·새 P1) → `not_validated`; WARN(P2) 표기; INFO(P3) 기록.
4. `relocation` 플래그 + 증거(§6.4, FAIL 아님).
5. `equivalence_basis ∈ {structural, tests, none}`; `none` → `not_validated`.
5a. **검증 입력 정체성**: `validate.json`은 `validated_tree_id`·`validated_analysis_input_id`·`validated_head_sha`·`validation_scope`를 기록한다. 이것이 없는 `validated`는 `validated`가 아니다(B.4).
6. `diff_lines` > 400 → 사람 리뷰 필수 표기.
7. **사건 기록**: 대상 finding이 캠페인 범위에 있으면 `open_pr`이 브랜치에 사건 파일(`claimed` + `validation` 결과)을 쓴다(§5.5). 원장 상태는 저장되지 않고 머지 뒤 파생 ⊕ 사건으로 계산된다.

### 6.4 굿하트와 재배치
- 순위가 백분위라 절대값 조작의 이득이 작다. 게이트가 원값이라 모집단 조작의 이득도 작다(§5).
- **재배치 플래그**: 목표 파일 `cx`가 30% 이상 떨어졌는데 리포 총 `cx` 변화가 5% 미만이면 `relocation: true`. 이것은 **나쁨의 판정이 아니다** — 좋은 Extract Method도 질량을 옮긴다. 그래서 플래그와 함께 계산 가능한 증거를 붙인다: `union_dup_tokens` 델타, 컴포넌트 간선 수 델타(의존 표면), public 멤버 수 델타, 변경이 파일 경계에만 있었는가. 쪼개기인지 추출인지는 사람이 본다 — 핫스팟이 판결이 아닌 것과 같은 자리.
- 후속 판정(`succession`, §5.5)이 캠페인 수준에서 같은 일을 한다: 해소는 후속 집합 전체에 합격 함수. 문제를 옮긴 것은 개선이 아니다.
- 재현 블록으로 누구나 전후 숫자를 다시 계산할 수 있다. `get_hotspots`는 점수만 주지 않고 증거를 함께 준다 — 점수를 내리는 것이 아니라 증거를 없애는 것이 과제가 되도록.

### 6.5 기계적 vs 생성적
**`structural`**: "토큰·타입 수준 구조가 보존됨. 스택 트레이스·리플렉션·동기화 경계·프로파일링 같은 **관측 가능한 비기능 차이는 있을 수 있음**. 증명이 아니다." **`structural` 전제조건(전부 충족해야 함)** — 토큰 동일은 충분조건이 아니다:
- 구조: 영역이 원본 메서드 몸체 **전체**와 정규화 후 일치(부분 일치 불가).
- 제어 흐름: 영역 안에 `return`·`break`·`continue`·`yield`·라벨 점프 없음. `synchronized`·`try` 경계를 가로지르지 않음.
- 데이터 흐름: 영역 뒤에서 쓰이는(live-out) 지역변수 ≤ 1개이고 원본 반환 타입과 일치. 영역 안에서 재대입되는 외부 지역변수 없음(effectively-final 호환). 이름 가림(shadowing) 없음.
- 객체: `this`/`super` 참조는 원본이 같은 클래스일 때만. 인스턴스 메서드면 호출 측에 수신 객체 존재. 인자 매핑은 Type-2 식별자 대응에서 1:1로 결정.
- 타입·예외: 바이트코드 수준 타입 동일(제네릭 추론 결과 포함), checked exception이 호출 측에서 처리·선언됨.
- 평가 순서·부수효과: 인자는 식별자만(부수효과 있는 표현식 불가).
하나라도 어긋나면 LLM 경로로 넘기고 근거는 `tests`. 위반 8종은 `contract/validation/` 픽스처.

### 6.6 실행 보안 계약
- L1(자기 리포 `scan`/`check`, 대상 코드 실행 없음) / L2(`apply`·`validate`·`open_pr`, 샌드박스 필수).
- **L1′**: "대상 코드가 실행되지 않는다"와 "분석기가 공격받지 않는다"는 다른 말이다. PMD·CPD·ASM(ArchUnit)·JGit은 파서이고 입력은 hostile PR일 수 있다(병리적 소스로 파서 폭주, 조작된 class 파일, 경로 트래버설). **신뢰하지 않는 리포**(fork PR·SaaS CI)의 L1 분석은 프로세스 격리 + 메모리·시간 상한을 필수로 한다.
- **L2 네트워크**: 기본 차단. 의존성은 **사전 적재 캐시 + 락파일 검증**으로 해결하고, 저장소 허용 목록은 캐시 미스 시 폴백(허용 저장소 손상 시나리오를 P9에 포함).
- **격리**: 컨테이너/VM, 호스트 파일시스템 마운트 없음, 임시 작업공간(실행 후 폐기).
- **자원**: CPU·메모리·시간 상한(기본 30분), 초과 시 `not_validated: timeout`.
- **시크릿**: 환경변수·자격증명 전부 제거. PR 생성 토큰은 샌드박스 밖 MCP 서버가 보유하며 권한은 **브랜치 생성 + PR 생성**만(최소 권한).
- **산출물**: `validate.json`·리포트·diff·사건 파일만 허용 목록으로 반출. 임의 파일 반출 금지.
- **MCP 신뢰 경계**: LLM에는 발견 관련 소스 **조각**(영역 ± 컨텍스트)·지표·컴포넌트 맥락만. 리포 전체·저자 데이터·빌드 로그 원문은 전달하지 않음(로그는 요약·오류 라인만). 모든 L2 호출의 입력·산출물 해시를 감사 로그에.
- **구조적 프롬프트 방어**: LLM이 속아도 피해 경로가 없게 한다.
  - LLM 출력 스키마: `{option_id ∈ propose가 낸 집합, edits: [{path ∈ 소스 루트, unified_diff}]}`만. 셸 명령·git 명령·경로 외 파일·네트워크 대상·빌드 스크립트 변경은 스키마상 표현 불가.
  - 경로는 소스 루트 화이트리스트로 정규화 후 검증(`..`·심링크 거부). 빌드 파일(`*.gradle*`, `pom.xml`, `buildSrc/`)은 편집 금지 목록.
  - 소스·주석·커밋 메시지는 구분자로 감싼 데이터. 이 규칙은 "필요하지만 충분하지 않은" 층이고, 충분성은 위 스키마 제약이 담당한다.
  - **감사 로그**: 샌드박스는 임시라 그 안의 로그는 의미가 없다. 로그는 **샌드박스 밖 MCP 서버의 신뢰 경계**에 append-only로 두며, 최소 `{request_hash, input_tree_id, option_id, sandbox_policy_hash, result_hash, validated_tree_id, timestamp}`. 저장소의 무결성·접근 정책은 조직 정책(B.6).
- **L2 1차 지원 빌드 시스템 = Gradle**. 락파일·일시 jacoco·configuration cache 계약이 Gradle을 전제한다. Maven은 의존성 재현 계약이 생긴 뒤(O12).

---

## 7. 통합 JSON 스키마 — 이 예시는 `contract/lens/sample-service/expected.json` 픽스처이며 CI가 재계산 검증한다

재계산 검증 대상: `H = 100·√(0.97·0.94) = 95.5`, `Dx = 100·√(0.88·0.71) = 79.0`, `composite = 0.5·95.49 + 0.3·79.04 + 0.2·0 = 71.5`, `NCCD = 512/185.48 = 2.76`, `F(OrderPolicy) = 100·√(0.95·0.98) = 96.5`, confidence 집계, 그리고 **`lens_percentiles`**(합성 리포 전체에서 렌즈 값의 백분위 — 파일 하나의 measures로는 재계산되지 않으며 리포 전체 픽스처가 결정한다).

```jsonc
{
  "schema": "jqradar/3",
  "project": "sample-service",
  "reproduce": {
    "tool_version": "3.7.2", "scanned_at": "2026-09-07T15:00:00Z",              // 감사용
    "window_anchor": { "type": "head_committer_time", "timestamp": "2026-09-05T11:42:10Z" },
    "head": "git-sha",
    "repository_state_id": "sha256:…", "analysis_input_id": "sha256:…", "classes_id": "sha256:…",
    "environment": { "pmd": "7.16.0", "archunit": "1.5.0", "jgit": "7.3.0", "git": null },
    "classes_reproduction_inputs": { "jdk": "21.0.4", "gradle": "9.1.0", "kotlin": "2.2.0", "compiler_args": ["-parameters"], "annotation_processors": [], "dependency_lock": "sha256:…" },
    "history_backend": { "name": "jgit", "git_version": null },
    "window_applied": { "months": 12, "max_commits": 2000, "bound_hit": "time", "commits_in_window": 1340, "merge_commits_excluded": 210 },
    "bytecode_scope": { "class_roots": ["build/classes/java/main","build/classes/kotlin/main"], "test_classes_included": false,
                        "generated_excluded": true, "external_edges": 812, "external_included_in_metrics": false },
    "component": { "strategy": "auto", "resolved_root": "com.company.dept.project", "count": 41 },
    "parameters": { "cpd.minimum_tokens": 100, "percentile.min_population": 20, "frozen.min_days": 180, "rename.similarity": 60,
                    "hotspot.change_unit": "chg_commits", "verify.min_changed_line_coverage": 0.8,
                    "profile": "jqradar-default", "weights": {"H":0.5,"Dx":0.3,"F":0.2} },
    "percentile_method": { "rank": "average", "formula": "(rank_avg-1)/(N-1)", "quantile": "type7-linear" }
  },
  "population": {
    "all":    { "n": 340, "java": 312, "kotlin": 28,
                "spread": { "cx.java": {"median": 18, "iqr": 27, "max": 87}, "fan_in": {"median": 4, "iqr": 7, "max": 35}, "age_last_days": {"median": 140, "p90": 900, "max": 2100, "valid_n": 338, "unknown_n": 2} } },
    "active": { "n": 212, "java": 194, "kotlin": 18,
                "spread": { "cx.java": {"median": 21, "iqr": 30, "max": 87}, "chg_commits": {"median": 3, "iqr": 5, "max": 18} } },
    "dx":     { "n": 37, "spread": { "union_dup_tokens": {"median": 130, "iqr": 110, "max": 240}, "active_twin_ratio": {"median": 0.33, "iqr": 0.5, "max": 1.0} } },
    "median_files_per_commit": 4, "commit_granularity": "fine", "population_note": null
  },
  "system": { "components": 41, "CCD": 512, "ACD": 12.49, "RACD": 0.305, "CCD_balanced": 185.48, "NCCD": 2.76,
              "cycles": [ {"id":"cyc-1","size":3,"members":["…"],"break_candidates":[{"from":"…","to":"…"}]} ] },
  "components": [ { "id": "….order", "Ca": 24, "Ce": 15, "I": 0.38, "A": 0.0, "D": 0.62, "zone": "stable-concrete",
                    "zone_note": "Martin Zone of Pain 후보. 도메인 코어·유틸리티는 정당할 수 있음", "cycle_id": "cyc-1", "class_edge_count": 131 } ],
  "files": [
    { "id": "f:order-service", "path": "src/main/java/…/order/OrderService.java", "component": "….order", "lang": "java",
      "measures": { "cx": 87, "cx_method": "cyclo", "loc": 640, "file_tokens": 5200, "smells": {"p1":0,"p2":3,"p3":9,"total":12},
                    "chg_commits": 18, "chg_days": 14, "churn": 2210,
                    "union_dup_tokens": 240, "dup_extent": 0.046, "self_dup_tokens": 0, "twins": 2, "active_twins": 1, "active_twin_ratio": 0.5,
                    "fan_in": 24, "age_last_days": 6 },
      "percentiles": { "cx": 0.97, "chg_commits": 0.94, "union_dup_tokens": 0.88, "active_twin_ratio": 0.71 },
      "percentile_population": { "cx": {"population":"active","lang":"java","n":194}, "chg_commits": {"population":"active","n":212},
                                 "union_dup_tokens": {"population":"dx","n":37}, "active_twin_ratio": {"population":"dx","n":37} },
      "lenses": { "H": 95.5, "Dx": 79.0, "F": 0.0, "composite": 71.5, "composite_note": null },
      "lens_percentiles": { "H": {"pct": 0.93, "population": "active", "n": 212}, "Dx": {"pct": 0.81, "population": "dx", "n": 37}, "F": {"pct": 0.45, "population": "all", "n": 340} },
      "arch_context": { "I": 0.38, "A": 0.0, "D": 0.62, "zone": "stable-concrete", "cycle_id": "cyc-1" } },
    { "id": "f:order-policy", "path": "src/main/java/…/order/OrderPolicy.java", "component": "….order", "lang": "java",
      "measures": { "cx": 80, "cx_method": "cyclo", "loc": 410, "file_tokens": 3300, "smells": {"p1":0,"p2":1,"p3":4,"total":5},
                    "chg_commits": 0, "chg_days": 0, "churn": 0,
                    "union_dup_tokens": 0, "dup_extent": 0.0, "self_dup_tokens": 0, "twins": 0, "active_twins": 0, "active_twin_ratio": null,
                    "fan_in": 35, "age_last_days": 1250 },
      "percentiles": { "cx": 0.95, "fan_in": 0.98, "chg_commits": null, "union_dup_tokens": null, "active_twin_ratio": null },
      "percentile_population": { "cx": {"population":"all","lang":"java","n":312}, "fan_in": {"population":"all","n":340},
                                 "chg_commits": {"population":"active","n":212,"reason":"not_in_active"},
                                 "union_dup_tokens": {"population":"dx","n":37,"reason":"no_twins"}, "active_twin_ratio": {"population":"dx","n":37,"reason":"no_twins"} },
      "lenses": { "H": null, "Dx": null, "F": 96.5, "composite": null, "composite_note": "H,Dx null — not in active/dx population" },
      "lens_percentiles": { "H": null, "Dx": null, "F": {"pct": 0.99, "population": "all", "n": 340} },
      "arch_context": { "I": 0.38, "A": 0.0, "D": 0.62, "zone": "stable-concrete", "cycle_id": "cyc-1" } }
  ],
  "duplicate_clusters": [ { "id": "dup:<token_hash>:120", "tokens": 120,
      "occurrences": [ {"path":"…/OrderService.java","start_token":1200,"end_token":1320,"start_line":45,"end_line":82},
                       {"path":"…/OldOrderService.java","start_token":4010,"end_token":4130,"start_line":210,"end_line":247} ],
      "identical_under": ["tokens"], "mechanical_fix_candidate": true } ],
  "duplication_pairs": [ { "a": "…/OldOrderService.java", "b": "…/OrderService.java", "pair_dup_tokens": 240 } ],
  "hidden_couplings": [ { "a": "…/OrderService.java", "b": "…/InvoiceMapper.java", "shared": 9, "tc": 0.75, "static_dependency": false } ],
  "findings": [
    { "id": "fnd:h-order-service", "kind": "hotspot", "lens": "H", "file": "f:order-service", "priority": 95.5, "lens_pct": 0.93,
      "interpretation": "investigate_first", "confidence": "medium",              // cx n=194 → medium, chg n=212 → high, min = medium
      "evidence": [ {"measure":"cx","value":87,"pct":0.97,"population":"active","n":194}, {"measure":"chg_commits","value":18,"pct":0.94,"population":"active","n":212} ] },
    { "id": "fnd:dx-order-service", "kind": "duplication_exposure", "lens": "Dx", "file": "f:order-service", "priority": 79.0, "lens_pct": 0.81,
      "interpretation": "investigate", "confidence": "low",                      // dx n=37 < 50
      "evidence": [ {"ref":"dup:<token_hash>:120"}, {"measure":"union_dup_tokens","value":240,"pct":0.88,"population":"dx","n":37},
                    {"measure":"active_twin_ratio","value":0.5,"pct":0.71,"population":"dx","n":37} ] },
    { "id": "fnd:f-order-policy", "kind": "frozen_core", "lens": "F", "file": "f:order-policy", "priority": 96.5, "lens_pct": 0.99,
      "interpretation": "investigate_first", "confidence": "high",              // all n=312/340 ≥ 200, 조건 없음
      "evidence": [ {"measure":"cx","value":80,"pct":0.95,"population":"all","n":312}, {"measure":"fan_in","value":35,"pct":0.98,"population":"all","n":340},
                    {"measure":"age_last_days","value":1250,"p90_all":900,"min_days":180} ] },
    { "id": "fnd:cyc-1", "kind": "component_cycle", "component": "….order", "cycle": "cyc-1", "confidence": "high" }
  ]
}
```

`check`의 출력 `gate.json`:
```jsonc
{ "profile": "jqradar-default-gate", "policy_hash": "…", "policy_owner": "platform-team", "base": "sha", "head": "sha",
  "eligible_hotspots_from_base": ["f:order-service", "…"],
  "checks": [
    { "rule": "new_duplication", "result": "PASS", "items": [] },                   // items[] = {path_head, path_base_mapped, cluster_id, tokens}
    { "rule": "new_component_cycle", "result": "PASS" },
    { "rule": "hotspot_cx_increase", "result": "WARN", "items": [ {"file": "f:order-service", "cx_base": 80, "cx_head": 87, "delta": 0.0875} ] },
    { "rule": "nccd_increase", "result": "context_changed", "components": [41, 43], "ccd": [512, 540], "nccd": [2.76, 2.71] },
    { "rule": "new_p1_smell", "result": "PASS" } ],
  "result": "PASS" }
```
`validate`의 출력 `validate.json`:
```jsonc
{ "finding": "fnd:dx-order-service", "branch": "jqradar/fnd-dx-dup-3f9a", "option": "opt-2",
  "sandbox": { "id": "…", "network": "deny", "dependency_source": "cache", "timeout_s": 1800, "policy_hash": "…" },
  "build": "passed",
  "tests": { "ran": 214, "failed": 0, "coverage_source": "jacoco-transient", "changed_line_coverage": 0.91 },
  "validated_head_sha": "…", "validated_tree_id": "sha256:…", "validated_analysis_input_id": "sha256:…", "validation_scope": "pre_merge",
  "metric_validation": {
    "target_improvement": { "rule": "duplication", "metric": "pair_dup_tokens", "target_pairs": ["OldOrderService-OrderService"],
                            "resolved_pairs": ["OldOrderService-OrderService"], "before": 240, "after": 0, "accepted": true },
    "new_findings": { "block": [], "warn": [ {"rule": "P2", "count": 1} ], "info": [] } },
  "relocation": { "flag": false, "repo_cx": [18420, 18420], "target_cx": [87, 87], "dup_delta": -240, "component_edge_delta": 0, "public_member_delta": 0 },
  "equivalence_basis": "structural",
  "diff_lines": 62,
  "verdict": "validated", "not_validated_reasons": [],
  "note": "validated ≠ 등가 증명. 라인 실행 ≠ 행위 단언." }
```

`expected.json` 변경 커밋에 동반되는 기록:
```jsonc
{ "fixture_change": { "reason": "library_behavior_change", "library": "pmd", "old": "7.16.0", "new": "7.17.0",
                      "measure": "cpd.union_dup_tokens", "note": "Kotlin 토크나이저가 문자열 템플릿을 한 토큰으로 묶음", "fixtures": ["cpd/overlap-merge"] } }
```

`campaign.json`(조직 소유):
```jsonc
{ "name": "debt-2026Q4", "owner": "platform-team", "created_at": "2026-10-05T09:00:00Z",
  "anchor": { "ref": "v4.2.0", "analysis_input_id": "sha256:…", "window_anchor": "2026-10-04T18:12:33Z" },
  "scope": { "components": ["….order", "….payment"] },
  "targets": [ {"metric": "union_dup_tokens_total", "op": "<=", "value": 6000}, {"metric": "ledger.high.open", "op": "<=", "value": 20} ],
  "definition_hash": "…" }
```
사건 파일 `.jqradar/events/debt-2026Q4/fnd-dx-dup-3f9a…@order-OrderService/20261019T101500Z-pr482.json`(저장되는 유일한 finding 단위 기록, 코드 상태 없음):
```jsonc
{ "schema": "jqradar-event/1", "provenance": { "repository_sha": "…", "created_by": "jqradar-mcp" },
  "campaign": "debt-2026Q4", "finding_id": "fnd:dx:dup:3f9a…:120@…/OrderService.java", "claim_id": "sha256:…",
  "pr": 482, "branch": "jqradar/fnd-dx-dup-3f9a", "claim_base_sha": "…", "claimed_at": "2026-10-19T10:15:00Z", "actor_type": "mcp",
  "validation": { "result": "passed", "scope": "pre_merge", "validated_head_sha": "…", "validated_tree_id": "sha256:…",
                  "validated_analysis_input_id": "sha256:…", "validate_hash": "sha256:…", "at": "2026-10-19T11:30:00Z" } }
```
원장 뷰 한 행(**저장되지 않고** 앵커 스캔 ⊕ HEAD 스캔 ⊕ 사건에서 계산):
```jsonc
{ "id": "fnd:dx:dup:3f9a…:120@…/OrderService.java", "kind": "duplication_exposure", "campaign": "debt-2026Q4",
  "origin": "baseline", "anchor_class": "high",
  "anchor_values": {"Dx": 79.0, "union_dup_tokens": 240, "lens_pct": 0.81}, "current_values": {"union_dup_tokens": 0},
  "first_seen": "2026-10-05T09:00:00Z", "first_observed_estimate": {"value": "2024-03-11T14:02:51Z", "method": "pickaxe", "confidence": "medium"},
  "succession": {"kind": "same"}, "current_priority": {"Dx": null, "interpretation": null, "note": "중복 해소로 dx 모집단 이탈"},
  "debt_age_days": 953, "change_exposure_90d": 7,
  "status": "closed", "merge_drift": true, "validation_scope": "pre_merge",
  "status_basis": {"transition": "open→resolved", "transition_commit": "sha", "event_at_transition": "validation_passed",
                   "event_file": "events/debt-2026Q4/fnd-dx-dup-3f9a…/pr482.json", "validated_tree_id": "sha256:…", "view": "at"},
  "transitions": [ {"at": "sha", "from": "open", "to": "resolved", "attributed_to": "pr482"} ] }
```
`change.json.touched_legacy_findings[]` = `{id, anchor_class, status_before, delta: {…}, status_after_if_merged}`.


### 7.1 HTML 렌더러 — 인터랙티브 시각화 스펙
**원칙**: (1) D28 — JSON의 순수 함수. 렌더러는 숫자를 계산하지 않고, 점수·순위를 만들지 않고, 정렬은 JSON이 정한 키로만. (2) **자립형 단일 HTML** — d3를 인라인 번들, 데이터는 `<script type="application/json">`으로 내장, 네트워크 요청 0건(슬랙에 던지고 회의실에서 열린다; 샌드박스·오프라인 CI에서도). (3) **판정 색 금지** — 좋음/나쁨을 뜻하는 빨강/초록 대신 단일 색상의 **농도**(백분위)와 방향 기호(▲▼). 유일한 예외는 `gate.json`의 FAIL/WARN — 정책 결과라 정책 색을 허용. (4) 추세 차트 없음 — 이력 저장소(백로그) 전까지는 두 점(앵커·지금)만 있으며, 빈 자리에 "추세: 이력 저장소 도입 후"를 적는다. (5) 색 외 채널(크기·테두리·라벨)과 키보드 탐색 — 접근성.

CodeScene 조사(2026-09)에서 가져온 것과 이유를 항목마다 적는다. 가져오지 않은 것: 개인 순위·리더보드 표면(어떤 모드에서도 — D48), 저자·팀 필터와 지식 맵은 `people.attribution`이 team/individual일 때만, Jira 결함·비용 오버레이(네 번째 엔진), ML 우선순위(우리는 인쇄되는 정렬 키), Code Health 절대 점수와 붉은/노란 판정(우리는 백분위와 `interpretation`).

**A. 지도 — `report.json`**
| # | 뷰 | 사양 | CodeScene 대응 |
|---|---|---|---|
| A1 | **시스템 맵** | 원 패킹(d3.pack). 폴더 = 원, 파일 = 잎. 크기 = `loc`(토글로 `file_tokens`). 클릭·휠·핀치·브레드크럼으로 계층 확대·축소, 드래그 패닝. 5,000 파일 초과 시 폴더 수준으로 자동 접기 | 핫스팟 시스템 맵 |
| A2 | **aspect 토글** | 버튼: H · Dx · F · composite(프로필 있을 때) · arch(컴포넌트 zone·SCC 강조) · lang(언어 분포) · confidence(불투명도). 복수 선택 시 각 렌즈 백분위를 **색 채널로 겹침**(가중합 아님 — 시각적 중첩만, 점수를 만들지 않는다). 선택 상태는 URL 해시에 저장·복원 | Combined Aspects |
| A3 | **모집단 슬라이더** | `active` ↔ `all` 전환, 현재 N 표시. F는 `all`에서만 색이 켜진다 | 활동 슬라이더 |
| A4 | **사이드바** | 파일 클릭 시: measures 원값·백분위·모집단 n·`lens_percentiles`·`interpretation`·`confidence`·evidence, `population_note`, `arch_context`, 소속 캠페인·원장 상태(있으면). 컨텍스트 메뉴: 메서드 표(A7)·결합(A5)·코드 위치 열기(로컬 경로 링크) | 컨텍스트 메뉴·Virtual Code Review |
| A5 | **결합 오버레이** | hover 시 연결선 — `hidden_couplings`(실선, 굵기 = `tc`)와 `duplication_pairs`(점선, 굵기 = `pair_dup_tokens`). 클릭으로 **고정**, 고정 상태에서 다른 파일 hover는 다른 색. 사이드바 3탭: 상대 파일·`tc`/`shared`·정적 의존 유무. 테스트-대상 쌍은 "test pair" 라벨 — 긍정 해석을 병기하고 판정하지 않는다 | 변경 결합 hover/lock |
| A6 | **컴포넌트 뷰** | 컴포넌트 노드 그래프(간선 = 정적 의존, 굵기 = `class_edge_count`), SCC 강조, I·A·D 표, **Main Sequence 산점도**(I vs A, D = 거리)와 zone 표기 + 정당한 예외 문구 | 아키텍처 분석 |
| A7 | **메서드 표** | 파일 사이드바에서 메서드별 CYCLO·NCSS. `method_spread`·`change_axes` 측정이 채택되면 변경 hunk 수·변경 축 소속 열 추가 — **해당 측정은 별도 승인 대기** | X-Ray 메서드 표 |
| A8 | **의존성 휠** | 변경 축 클러스터 ↔ 메서드/파일 chord 다이어그램. A7과 같은 조건 | X-Ray dependency wheel |

**B. 변경 리포트 — `change.json`**
| # | 뷰 | 사양 |
|---|---|---|
| B1 | **델타 aspect** | 같은 시스템 맵에서 변경 파일만 채색. 색 농도 = 원값 델타 크기, 기호 = 방향(▲▼). 새 중복 발생·새 SCC는 아이콘. BASE top-decile 자격 파일은 테두리 |
| B2 | **컴포넌트 간선 델타** | 추가·삭제 간선을 방향으로만 구분(좋고 나쁨 색 아님), 새 SCC 강조, `external` 간선 수 변화 |
| B3 | **`touched_legacy_findings` 패널** | 표 + 상태 전이 예고(`status_after_if_merged`) + 이 PR의 claim 여부 |
| B4 | **설명 문장 조립**(A.4) | 항목별 `{value_base, value_head, delta, evidence[]}`에서 문장 생성 — "이 변경으로 이 모듈의 복잡도가 기준선보다 N 증가했고, 과거 변경 집중 영역과 겹치며, 유사 로직이 두 위치에도 존재한다." 판정 단어 없음 |
| B5 | **게이트 결과** | `gate.json`이 있으면 FAIL/WARN/PASS를 정책 색으로, 정책 이름·해시·소유자 표기 |

**C. 원장 뷰 — 파생 ⊕ 사건**
| # | 뷰 | 사양 |
|---|---|---|
| C1 | **캠페인 헤더** | 캠페인 선택, 앵커 SHA·날짜, 상태별 카운트(open/in_progress/validated/rejected/closed/regressed/removed), `anchor_class`별 막대, 목표 대비 진전 — **두 점**(앵커·지금), 추세선 없음 |
| C2 | **finding 표** | 기본 정렬 키(`anchor_class → change_exposure_90d → debt_age`) 인쇄, 필터, 행 클릭 → 앵커 값·현재 값 나란히, 사건 목록, PR 링크 |
| C3 | **Lost findings** | `id_drift`(succession=unknown), `validated_not_resolved`, `closed_unverified`, `relocated_out_of_scope`, `removed`를 별도 절로 — 숨기지 않는다 | 
| C4 | **최근 변경이 닿은 부채** | `change_exposure_90d` 상위, 지도로 점프 |

**공통**: HTML 상단에 `reproduce` 블록과 재현 명령, 내장 JSON 다운로드 버튼. 성능 목표: 파일 5,000개까지 상호작용 60fps, 초과 시 A1 접기. 파일 크기 목표 ≤ 3MB(d3 인라인 포함). 픽스처 `contract/renderer/`(§2.9): JSON에 없는 숫자 검출, 판정 어휘 사전 검사, 해시 복원, 네트워크 0건.

**CodeScene에서 배워 우리 것에 반영한 판단 셋**: (1) Goals의 네 분류(Planned Refactoring·Supervise·No Problem·Critical Code)는 우리 `claimed`·회귀 게이트·(억제 없음)·캠페인 scope에 대응하며, No Problem조차 백그라운드에서 계속 분석해 악화되면 다시 띄운다는 점은 억제를 허용할 때의 기준으로 기록. (2) Lost Notes(rename 추적 실패 목록)는 우리 C3와 같은 문제를 같은 방식으로 다룬다 — 숨기지 않고 목록으로. (3) Code Age 분석이 Deprecated라는 사실은 우리 F 렌즈의 실행 가능성에 대한 경고 신호 — P1a 대비 F의 증분 가치를 배터리 B에서 별도로 본다.
---

## 8. 근거

| 연구/출처 | 방법·대상 | 핵심 결과 | jQRadar에 쓰는 이유 |
|---|---|---|---|
| Tornhill, *Your Code as a Crime Scene*(2015; 2판 2024); *Software Design X-Rays*(2018) | 이력 기반 포렌식 | 핫스팟(코드 크기/들여쓰기 복잡도 × 변경 빈도), 시간적 결합, 코드 나이 | H는 복잡도 프록시를 바꾼 **파생형**(§3.1). 핫스팟 = 우선순위라는 용법(B.2) |
| Tornhill & Borg, *Code Red*(TechDebt 2022) | 39 코드베이스 | 저건강 코드에서 결함·개발 시간 증가 | 코드 건강과 비용의 상관(CodeScene 데이터임을 명시) |
| Tornhill·Borg·Mones, *Refactoring vs Refuctoring*(CodeScene 2024) | 테스트 기반 벤치마크 | LLM 리팩터링 37% 정확, 사실 검증 게이트로 98% | 검증 게이트 필요성(§6.3) |
| *Differential Fuzzing … LLM-Generated Refactorings*(LLMTrust @ FSE 2026) | 6 LLM · 3 데이터셋 · **Python** | 19–35% 기능 비동치, 그중 ~21%는 기존 테스트 통과 | 테스트만으로 부족. **Java/Gradle에 수치 외삽 금지** — 자체 오류율은 P5 |
| R. C. Martin, *Agile Software Development*(2002) | — | I·A·D, Main Sequence | 컴포넌트 단위(§2.2) |
| J. Lakos, *Large-Scale C++ Software Design*(1996) | — | CCD·ACD·NCCD | 시스템 단위, 추세용(§2.3) |
| Lanza & Marinescu, *Object-Oriented Metrics in Practice*(2006) | — | WMC·ATFD·TCC 탐지 전략(GodClass의 출처) | 재료는 측정으로, 임계 판정은 규칙 층으로(§2.1 참조 룰셋 논의) |
| Juergens 외(ICSE 2009); Kapser & Godfrey(2008) | 클론 연구 | 비일관 클론 변경과 결함 / 무해한 클론 | Dx가 "편집되는 중복"만 높이는 이유(§3.2) |
| Netflix TechBlog, *Scaling ArchUnit with Nebula ArchRules*(2026-05) | 운영 사례 | ArchUnit 임포터를 그래프로; 자동 수정은 **탐색 과제** | 배포 형태 참고; 자동 수정 과신 금지(D6) |
| ArchUnit 사용자 가이드·javadoc — `ArchitectureMetrics` | 라이브러리 | Martin·Lakos 메트릭 내장, `dependsOn`은 전이적 | 직접 구현 대신 호출(§2.2–2.3) |
| JaCoCo 카운터 문서 | — | 라인 커버리지 = 그 라인의 명령 중 하나 이상 실행 | "validated ≠ 등가" 고정 문구의 근거(§6.3) |
| JGit `ObjectInserter.Formatter` | 라이브러리 | 오브젝트 삽입 없이 blob ID 계산 | 추적/미추적 통일 내용 ID(§2.8) |
| CodeScene 문서(2026-09 조사) — 시스템 맵·Combined Aspects·변경 결합 오버레이·X-Ray·Goals·Lost Notes | 제품 문서 | 원 패킹 맵, aspect 중첩, 결합 hover/lock, 메서드 수준 X-Ray, Goals 네 분류, rename 추적 실패 목록. **Code Age 분석은 Deprecated** | §7.1 렌더러 원형; C3 Lost findings; F 렌즈에 대한 경고 신호 |
| Changesets · Towncrier · reno · Changie | 릴리스 도구 | PR당 파일 하나, 릴리스 때 소비·삭제 | 사건 파일의 원형(§5.5) |
| RuboCop `.rubocop_todo.yml` · Detekt/Android Lint/PHPStan/Psalm baseline · ESLint bulk suppressions | 린터 | 기존 위반 등록 후 점진 상환 | 브라운필드 등록의 원형 — 단 목록이 부패하므로 우리는 목록을 파생하고 사건만 저장(§5.5) |
| Betterer, 커버리지 래칫 | 테스트 도구 | 개선만 허용하는 기준선 | 보호 기준선의 원형 — 단 덮어쓰지 않고 불변 앵커(§5.4) |
| ADR(Nygard) · DVC · Git LFS | 관례 | append-only 기록 · 작은 포인터 + 외부 산출물 해시 | 사건 레코드·`validate_hash`(§5.5) |
| Terraform state(반대 선례) | — | 크고 가변이며 동시 쓰기 → 리포에 두지 않음 | `.jqradar/`가 리포에 있어도 되는 조건의 경계(§5.5, §12) |
| Bird 외, *Don't Touch My Code!*(FSE 2011) | Windows 코드베이스 | 소유권 분산·마이너 기여자 비율이 결함과 상관 | §2.1 익명 소유권 분산 사실의 근거 |
| DORA(팀 수준 지표 권고); Forsgren 외, *The SPACE of Developer Productivity*(2021) | 산업 지침 | 개인 단위 생산성 지표의 위험, 단일 지표 경계 | B.3의 경험적 논거 — 금지가 아니라 기본 꺼짐의 근거 |
| CQSE/Teamscale 논문·문서; Kamei 외 JIT 결함 예측(TSE 2013); Alves·Ypma·Visser(ICSM 2010); Arcelli Fontana 외 Arcan(ICSA 2017); Mo·Cai·Kazman·Xiao 핫스팟 패턴 | 선행 계보 조사(2026-09-09) | 변경 단위 기준선·finding 추적, 커밋 수준 위험, 벤치마크 임계, 구조 스멜 진화, 이력×아키텍처 | jQRadar 기둥별 선행. 새것은 기둥이 아니라 조합·재현성 계약·리포 내 사건 소싱·증거 사슬 |
| K. Thompson, *Reflections on Trusting Trust*(CACM 1984) | — | 자기를 컴파일하는 컴파일러의 결함은 소스에 흔적 없이 영속 | 자기 적용의 맹점(§9, §12): jQRadar가 못 보는 악화는 jQRadar만으로 게이트하는 한 잡히지 않는다 |
| D. A. Wheeler, *Fully Countering Trusting Trust through Diverse Double-Compiling*(2009) | — | 독립된 둘째 컴파일러로 교차 검증 | 우리 대응물 = 외부 배터리·외부 파일럿·사람 검증자(D84) |
| 컴파일러 부트스트랩 관례(stage0→1→2, stage2 ≡ stage3 고정점) | GCC·rustc·Go·PyPy | 단계적 자기 호스팅과 고정점 검사 | §9 자기 적용 stage 표와 "같은 커밋 → 바이트 동일 원장"의 원형 |
| GitHub Spec Kit(2025–26) | 절차 도구 | constitution + 기능별 spec/plan/contracts/tasks, analyze | 검토 후 **보류**(2026-09-08). 우리 헌장은 §1, 게이트는 자기 적용 |

---

## 9. 검증 계획

### 전제와 파괴 기준
| # | 전제 | 방법 | 깨짐 기준 → 조치 |
|---|---|---|---|
| **P1a** | **구성타당도**: H가 `chg_commits` 단독보다 이후 6개월 개발자 개입을 더 잘 예측한다. H는 `chg`를 성분으로 가지므로 "활동이 지속된다"는 사실만으로는 결합식의 가치가 증명되지 않는다 | 같은 리포·같은 창에서 **기준선 넷**: random / cx-only / chg-only / H. 각각 상위 10% 집합의 6개월 개입 리프트. 개입 제외 규칙: 공백만 변경, `@Generated`/generated 경로만, 내용 변경 없는 대량 rename, 의존성·벤더 경로(`build.gradle*`, `pom.xml`, `libs/`, lockfile)만. **검열 계약**: `evaluation_cutoff` 고정, `followup_days = 180`, 적격 코호트 = `index_time ≤ cutoff − 180d`(6개월 완전 관측만), 결과 창 `[index_time, index_time + 180d]`. 최근 코호트를 미완료 상태로 세지 않는다. 설계는 G0에서 **사전 등록**하고 배터리 B 전에 바꾸지 않는다 | 3개 리포 중 2개 미만에서 `Lift(H) > Lift(chg-only)`, 또는 증분 리프트 중앙값 ≤ 0 → H 식 재설계(복잡도 프록시·결합 함수) |
| P1b | **결과타당도**: H 상위 10%가 결함 수정 커밋을 더 받는다 | 메시지 패턴(검증 전용), 기준선 넷과 함께 | H가 chg-only 대비 증분 없음 → "결함" 문구 제외, "조사 우선순위"만 |
| P2 | 백분위가 리포 나이·크기·커밋 스타일에 전이 | + **`chg_commits` vs `chg_days` 비교 실험**(계약 변경은 다음 개정에서) | 스쿼시에서 뒤집힘 → 그때 계약 변경 논의 |
| P3 | Dx 상위 파일의 쌍둥이가 실제로 비일관 편집을 겪는다 | 사본 중 한쪽만 30일 내 변경된 비율, Dx 상위 vs 하위 | 차이 없음 → `active_twin_ratio` 재정의 |
| P4 | 컴포넌트 D·순환 발견이 실무자에게 문제로 인정된다 | 아키텍트 패널 블라인드 평가 | 인정률 < 60% → zone 표기 제거, 순환만 유지 |
| P5 | §6.3 검증이 잘못된 수정을 거른다 | 비동치 리팩터링 주입(스코프·예외·null·평가 순서), 절반은 Mock 기반 테스트만 있는 영역에 | 통과율 > 10% → `verify.min_changed_line_coverage` 상향, 미커버 영역 `apply` 거부(O5). Mock 영역에서 통과하면 커버리지 측정 경로 재점검 |
| P6 | 재배치 플래그가 쪼개기와 추출을 구분할 증거를 준다 | 합성 분할 vs 진짜 추출 | 증거 델타로 구분 불가 → 증거 항목 추가 |
| P7 | **성능 예산**: High 열 cold P95 ≤ 10분, peak RSS ≤ 2GB, incremental+1 P95 ≤ 60초 | 매트릭스 × {cold, warm, +1, +100, 캐시 무효화}, 각 5회, P50/P95/peak RSS 기록. JGit 단독 | 초과 → §4 최적화 → 네이티브 옵트인(O8 선행) |
| P8 | `component.strategy=auto`가 의미 있는 컴포넌트를 낸다 | **아키텍트 2명 독립 주석 → 불일치 조정 → 참조 경계**, inter-rater agreement(Cohen κ) 기록 | auto 일치율 < 80% → 규칙 조정. κ < 0.6이면 참조 경계 자체를 신뢰하지 않고 리포 교체 |
| P9 | L2 샌드박스가 알려진 벡터를 막는다 | 벡터: 외부 통신, 환경변수 읽기, 호스트 경로, 시간 초과, **fork bomb·FD 고갈·디스크 고갈, /proc·/sys 접근, 컨테이너 capability, Docker 소켓, DNS 리바인딩, 의존성 혼동, 허용 저장소 손상(캐시 미스 강제), 심링크 탈출** | 하나라도 성공 → L2 출시 보류 |
| P10 | configuration cache | `--configuration-cache` 연속 2회 × {깨끗한 환경, 같은 환경, 소스 변경, 정책 변경, 클래스패스 변경}, 멀티모듈 | 실패 → Build Service 재설계 |
| P11 | 적합성 스위트가 라이브러리 버전 변경과 지표 변경을 구분한다 | PMD·ArchUnit·JGit 마이너 버전 상향 후 스위트 실행 | 기대값 변경은 §2.9 `fixture_change` 분류(라이브러리/계약/버그) 없이 머지 불가 |
| P12 | 앵커에 얼린 분류가 개선을 **보이게** 한다 — 상위 finding을 고치면 `high` open 수가 줄고, 지도 `interpretation`처럼 다음 10%가 올라오지 않는다 | 배터리 리포에서 `high` 20개를 합성 수정으로 해소한 뒤 원장 카운트와 지도 라벨 비교 | 원장 카운트가 줄지 않거나 다시 늘면 ID 추적 결함 → P14 |
| P13 | 한정 blame의 비용이 캠페인 생성 1회에 허용된다 | 원장 500건 · 1M LOC · 2K 커밋에서 P95 | > 10분 → pickaxe만; 그래도 초과면 `method: unknown` |
| P14 | §5.5 후속 판정과 **전이 귀속**이 실제 이력에서 맞는다 — `succession = unknown`(→ `id_drift`) 비율, 사람이 보기에 틀린 후속 판정(실은 이동인데 `removed`) 비율, 그리고 **해소를 잘못된 커밋·claim에 귀속한 비율** | 합성 rename·이동·분할·병합 시나리오 + 오귀속 5종 + **인터페이스 추출·구현체 분할(재작성) 시나리오** + 배터리 리포의 실제 리팩터링 커밋 표본을 사람이 라벨링. **순환 finding**: import 기반 근사 그래프와 바이트코드 그래프의 SCC 불일치율 | `unknown` > 5% 또는 오판 > 5% → 토큰 출처 임계(80/20) 조정, 시그니처 계보 가중 상향. 순환 근사 불일치 > 10% → 근사 구간 상태를 `unknown_between_reports`로 격하. **이 계약은 출시 전 픽스처로 고정되며 P14는 그 사후 실패율이다** |
| P15 | **PR-사건 파일 + 캠페인 아카이브 조합이 실제 팀 흐름에서 마찰 없이 굴러간다** — 부품은 선례가 있지만 조합은 새것이다(§5.5) | 배터리가 아니라 **파일럿 팀 한 곳**에서 캠페인 하나를 생성→수정 PR 10개 이상→종료까지. 측정: 사건 파일 누락률(claim 없이 해소된 finding 비율), git 충돌 발생 수, 리뷰어가 사건 파일을 잡음으로 느낀 비율, 종료 안 한 캠페인, **그리고 시각화 사용성 — 첫 4주간 HTML 열람 빈도, 맵 → 코드 위치 이동률, aspect 토글 사용 분포, "무슨 뜻인지 모르겠다"는 질문 수** | 누락률 > 30% 또는 충돌 발생 → 사건 기록 방식 재검토(트레일러 병행 등). 잡음 불만 > 절반 → `linguist-generated`로도 부족, 동반 리포 기본화 검토. **재구성 결정성**: 파일럿 리포의 임의 커밋 20개에서 두 머신이 `ledger --at`을 돌려 바이트 동일해야 한다 — 하나라도 다르면 원장은 신뢰할 수 없고 출시 보류. **저작 모드 관찰**: 파일럿 팀이 `people.attribution`을 어느 모드로 켰는지와 그때의 도입률·`relocation`·게이밍 징후를 기록 — 우리가 주장했던 사회적 위험이 실제인지 이제 데이터로 본다 |
| P17 | **A.3의 자기 검증**: 도구 관여가 선언된 변경이 선언되지 않은 변경보다 `change`에서 finding(새 중복·cx 증가·새 SCC)을 더 연다 | 자기 리포(S2 이후)와 파일럿 리포에서 `declared_ai_assistance` 유/무 변경의 게이트 결과 비교. 선언은 하한선이므로 결과를 "선언된 관여"로만 서술 | 차이 없음 → A.3의 문구를 "AI가 병목을 만든다"에서 "검증은 출처와 무관하게 병목이다"로 약화 |
| P18 | 익명 소유권 분산 사실(`distinct_authors_90d`·`minor_contributor_share`)이 H 대비 P1a·P1b에 증분 예측력을 준다 | P1a 기준선에 `H + ownership` 추가 | 증분 없음 → 사실로만 유지, 렌즈 승격 논의 종료 |

**통계 기록**: 모든 리프트에 부트스트랩 95% CI, 리포별 값, 중앙값을 기록한다. "1.5배"·"2/3 리포" 같은 수치는 **go/no-go 휴리스틱**이며 통계적 결론으로 쓰지 않는다 — 리포 3개는 표본이 아니다.

**P7 워크로드 매트릭스**
| 축 | Low | Medium | High |
|---|---|---|---|
| LOC | 100K | 500K | 1M+ |
| W 안 커밋 | 100 | 1K | 2K |
| 변경 경로 수 | 1K | 10K | 100K |
| rename 쌍 | 10 | 100 | 1K |
| 모듈 | 1 | 20 | 100 |
| 캠페인 finding당 전이 스캔 대상 커밋(finding 파일을 건드린 머지) | 10 | 50 | 100 |
각 셀 × {cold, warm, incremental +1, incremental +100, 캐시 무효화}, 5회, P50/P95/peak RSS 기록. JGit 단독.

**배터리 리포**(나이·크기로 선정; AI 사용 여부로 고르지 않는다 — 선택 효과): 노년(15년+) 후보 Apache Commons Lang·Spring Framework(P5·P11·옛 커밋 빌드의 혹독한 시험대), 중년(5–12년) Netty·Micronaut·Elasticsearch(P2·스쿼시 정책 비교), 청년(≤3년) GitHub 생성일·Java·Gradle·500+ 커밋으로 W1에 확정, Kotlin 혼합 1개, 스쿼시 머지 정책 리포 1개, 깊은 기업형 패키지 합성 리포 1개(P8), 악성 픽스처 리포 1개(P9). jQRadar 자기 리포는 S1 이후 **내부자 데이터**로 병기하되 배터리를 대체하지 않는다(§9 자기 적용).

### 일정 (17주, 2026-09-14 ~ 2027-01-08)
| 주 | 산출물 | 게이트 |
|---|---|---|
| W1–3 | 여섯 계약 동결 + G0 픽스처 + 예시 픽스처화 + P1a 사전 등록 + **원장·캠페인 계약(§5.4–5.7) 초안**. 배터리 리포 확정 | **G0**(W3): 아래 체크리스트 |
| W4–7 | core(측정·백분위·렌즈·JSON), CLI `scan`, `contract/lens·gate` | **G1**(W7): 배터리 A — P2·P7·P8. **자기 적용 S1**: jQRadar 리포 첫 `scan`, 지도를 `docs/self/`에 보존 |
| W8–10 | Gradle(configuration cache), `change` 변경 리포트, 게이트, **인터랙티브 HTML A1–A6 + B1–B5**(§7.1), `contract/renderer` | **G2**(W10, go/no-go): 배터리 B — P1a·P1b·P3·P4·P10. **자기 적용 S2**: 자기 CI에 `jqradarChange`·`jqradarCheck` 필수화 |
| W11 | **캠페인 커맨드·사건 파일·원장 뷰**(§5.4–5.5, 파생은 `change --base <앵커>` 재사용), **후속 판정(토큰 출처)·상태표·`--at/--live`**, **한정 blame**(§5.6), `touched_legacy_findings`(§5.7), `contract/ledger`(**픽스처를 먼저 박고 구현**) | **G2b**(W11): P12·P13·P14 + 재구성 결정성. **자기 적용 S3**: G2 커밋을 앵커로 첫 캠페인(scope = core), `.jqradar/` 첫 생성 |
| W12–15 | MCP, 샌드박스, `propose/apply/validate/open_pr`(사건 파일 기록 포함), OpenRewrite 레시피 + 전제조건 검사기, `contract/validation·security` | **G3**(W15): 배터리 C — P5·P6·P9. **자기 적용 S4**: 자기 finding ≥ 3건을 자기 `propose/apply/validate/open_pr`로 — 사건 파일이 우리 PR에 실린다 |
| W16–17 | Kotlin 들여쓰기·언어별 백분위, 옵트인 팀 렌즈, **원장 뷰 C1–C4 + 메서드 표·휠 A7–A8**(측정 채택 시), 문서, `jqradar/3` 동결, P11. **P15 파일럿 시작**(캠페인 하나, 종료까지는 출시 후 지속) | **G4**. **자기 적용 S5**: 우리 캠페인 원장이 재현 가능하고 정직한 상태(closed든 open이든, `id_drift`·`closed_unclaimed` 미은폐) — 출시 조건 |

원장이 1주로 줄어든 이유: 코드 상태를 저장하지 않으므로 파생 층은 이미 있는 `change`의 BASE를 앵커로 바꾼 것이고, 새로 만드는 것은 캠페인 커맨드·사건 파일 쓰기·뷰 조합뿐이다. 원장을 넣은 이유: 원장 없는 jQRadar는 브라운필드에서 "지금 어디가 나쁜가"(지도)와 "이 변경이 무엇을 바꿨나"(변경 리포트)는 답하지만 **"우리가 나아지고 있나"에 답하지 못하고**, 그 질문은 도입 뒤 석 달째에 반드시 나온다. 밀리면 자르는 순서: 팀 렌즈 → Kotlin 들여쓰기 → 네이티브 git → **한정 blame(`first_observed_estimate`를 unknown으로)**. 원장 자체·픽스처·샌드박스·검증기는 자르지 않는다.

### 자기 적용(self-application) 계약
**"jQRadar는 jQRadar로 만든다."** 사용(도그푸딩)이면서 그 결과가 자기 진화의 게이트가 되는 것.

**용어.** 셋은 뿌리가 같고 다르다. *Dogfooding*(만드는 사람이 자기 제품을 쓴다 — 사용), *Self-hosting/Bootstrapping*(도구가 자기를 만드는 입력이 된다 — GCC·rustc·Go·PyPy — 구성), *Self-application*(분석 도구가 자기 코드베이스를 분석하고 그 결과로 자기 변경을 받아들이거나 거부한다 — ESLint·Clippy·SonarSource·Coverity — 심사). jQRadar는 셋째이며, 자기 호스팅에서 **stage 부트스트랩**과 **고정점 검사**의 절차를 빌린다.

**부트스트랩 문제.** W1에는 도구가 없고, 우리 리포는 처음엔 그린필드라 브라운필드 기능은 자기에게 시험할 부채가 아직 없다. 그래서 단계다:
| stage | 시점 | 자기 적용 | 컴파일러 대응 |
|---|---|---|---|
| S0 | W1–3 | 도구 없음. **개발 절차가 철학을 따른다** — 계약 먼저·픽스처 먼저·`fixture_change`. 첫 커밋부터 머지 커밋·rename 추적이 가능한 커밋 규율(나중에 자기 이력이 분석 가능하도록) | stage0(다른 언어로 쓴 씨앗) |
| S1 | G1 | `scan`이 생기는 순간 첫 대상은 jQRadar 리포. 첫 지도를 `docs/self/<sha>.report.json`(재현 블록 포함)으로 보존 | stage1 |
| S2 | G2 | **모든 PR에 `jqradarChange` + `jqradarCheck`**를 자기 CI에. 기본 게이트 프로필 그대로. 끄거나 우회하면 그 사실과 이유를 §0에 기록 | stage2(자기가 자기를 컴파일) |
| S3 | G2b | **첫 캠페인 = G2 커밋 앵커**, scope = core, 목표를 적어 `target_driven`으로. 그때까지의 우리 부채가 첫 원장. `.jqradar/`가 처음 생기는 리포가 우리 리포 | — |
| S4 | G3 | **AI 에이전트가 자기 finding을 자기 `propose/apply/validate/open_pr`로 끝까지 통과시킨다.** 샌드박스·검증·사건 파일이 우리 PR에 실제로 실린다. **표본 규칙**: 원장 기본 정렬 상위 3건을 **자동 선택**(우리가 고르지 않는다), `succession ≠ same`인 건이 있으면 최소 1건 포함. **조건은 성공이 아니라 정직한 완주다** — `not_validated: low_coverage`도 유효한 결과(§12 "검증 부담"). 3건 전부 `not_validated`면 사유 분포를 §0에 기록하고 차순위로 **최대 3건 더** 확장한 뒤 멈춘다 — 상한 없이 내려가면 쉬운 것이 나올 때까지 고르는 선택 편향이 돌아온다. 검증 예외 승인 워크플로는 두지 않는다(검증 예외는 `check` 정책의 자리) | — |
| S5 | G4 | 출시 조건: 우리 캠페인의 원장이 **재현 가능**하고 **정직**하다 — 두 머신에서 `ledger --at` 바이트 동일, `id_drift`·`closed_unclaimed`·`validated_not_resolved`가 숨겨지지 않음 | stage2 ≡ stage3 고정점 |

**규칙**
- 자기 적용 결과가 나쁘면(우리 PR이 게이트에 걸리고, 우리 원장이 부채를 못 닫고, `relocation`이 뜨면) 그것은 도구의 실패가 아니라 **도구가 일하고 있다는 증거**다. 그 결과도 §0에 쓴다.
- 자기 적용은 개발 속도를 떨어뜨린다. 그것은 A.7이 남에게 요구하는 비용을 우리가 먼저 내는 것이다(B.7).
- 자기 리포의 `docs/self/`는 리포트 이력의 첫 축적이다 — 백로그의 이력 저장소 설계의 첫 실데이터.

**한계 — 자기 적용은 필요하지만 충분하지 않다**
- **Trusting Trust**(Thompson 1984): jQRadar가 어떤 악화를 못 보는 결함이 있으면, jQRadar만으로 jQRadar를 게이트하는 한 그 결함은 잡히지 않고 영속한다. 자기 맹점은 자기 적용으로 드러나지 않는다. 컴파일러 세계의 답은 Wheeler의 독립 둘째 컴파일러(DDC)이고, 우리 답은 **외부 브라운필드 배터리·외부 파일럿 팀·사람 검증자**다. 자기 적용은 이 셋을 대체하지 못한다.
- 자기 적용 데이터는 **내부자 데이터**다. P1a·P2 같은 검증에 증거로 쓰되 그렇게 표시하고, 배터리를 대체하지 않는다.
- 우리 리포는 17주 만에 브라운필드가 되지 않는다. 후속 판정·scope 탈출·`regressed` 같은 브라운필드 계약의 실전 검증은 외부 리포에서.

### 백로그 — 다음 판
| 항목 | 설계 초안 | 비용 |
|---|---|---|
| **finding → 규칙 승격**(A.7) | 원장에서 같은 `kind`+위치가 `regressed`를 n회(초안 2) 겪거나, `introduced`가 같은 컴포넌트에서 n회(초안 3) 반복되면 `check` 규칙 초안(YAML) 또는 ArchUnit 규칙 초안(Java)을 생성해 PR로 제안. 사람이 채택. Nebula ArchRules 조직이면 그 라이브러리 형식으로 | 원장 위에 +1주 |
| **전체 리포트 이력** | HEAD별 `report.json` 축적으로 렌즈 궤적·연결성 축 방향 판정. 이것은 크고 매 스캔 쓰기라 `.jqradar/`가 아니라 CI 아티팩트/외부 스토어 — Terraform 사유(§5.5) | +2주 |

### G0 체크리스트
동결 승인 조건 — 전부 충족:
1. §2.1–2.9와 §6.3–6.6 계약이 리뷰어 2명의 **교차 검토**(계약 간 충돌 점검 포함)를 통과.
2. `contract/percentile·cpd·history·graph` 픽스처가 CI에서 통과하고, §7 예시 JSON이 재계산과 일치.
3. 렌즈 백분위·P90 type-7(18.1)·IQR=0·age null·발생 수준 새 중복·`target_pairs` 각각에 픽스처 ≥ 1.
4. P1a 실험 설계(기준선 넷, 제외 규칙, CI 방법)가 문서화되어 **사전 등록**됨.
5. L2 지원 범위 = Gradle 명시, Maven은 O12.
6. `expected.json` 변경에 `fixture_change`를 요구하는 CI 규칙이 켜져 있음.
7. **증거 사슬 계약이 픽스처로 고정됨** — 툴체인·계약 버전 포함 `analysis_input_id`; `repository_state_id`와의 분리; `validated_tree_id`·검증 provenance; `validation_scope`·`merge_drift`; `validated_not_resolved` 4분기; reanchor 계보; split + scope 혼합; `(campaign, finding, pr)` 멱등성; P1a 코호트 컷오프; `anchor_class` 결정 산출물; reproduce/provenance 분리; S4 자동 선택; **전이 모델과 오귀속 5종 실패 사례**; 실행 라인 0 변경 커버리지 `not_applicable`; 순환 finding 과거 커밋 근사 표기; 재작성 분할의 시그니처 계보. 재감사는 "계약이 존재하는가"가 아니라 **"계약이 서로 모순 없이 실행되는가"**를 본다.

---

## 10. 결정과 열어둔 것

**v3.0–v3.2 결정**
- D1 헤드라인은 H(Tornhill-derived). 복합 점수는 이름 붙은 프로필로만.
- D2 모든 성분은 결합 전 백분위(§2.5). 절대 임계는 `scan`에 없다.
- D3 Martin은 컴포넌트, Lakos는 시스템. 파일에는 맥락만. 계산은 ArchUnit `ArchitectureMetrics`.
- D4 `smells`는 점수 밖. 카운트와 합계만.
- D5 `check`만 정책·설정 파일(v3.7.2: + `people` 절). 회귀 기준, BASE 자격 고정 + 원값 델타.
- D6 아키텍처 수정은 제안만.
- D7 모든 적용은 브랜치, PR에 `validated/not_validated`와 사유. 기본 브랜치 push 금지.
- D8 검증 = 빌드 + 테스트(라인 커버리지) + 재스캔(개선·신규 발견 차등·재배치 플래그) + 등가 근거.
- D9 기계적 수정은 자체 OpenRewrite 레시피, `structural`은 §6.5 전제조건 전부 충족 시에만.
- D10 재현 블록 필수. HTML은 JSON의 순수 함수.
- D11 (v3.7.2 개정) 저작은 세 층: `off`(기본 — 익명 분산 사실 + 선언된 도구 관여), `team`(조직 팀 매핑, ≥3인 집계), `individual`(저자 사실을 실행 산출물에). 조직이 `people.attribution`으로 정한다.
- D12 Kotlin은 렌즈별 범위 명시, 미지원 `null`, `cx` 백분위는 언어별 모집단.
- D13 백분위는 원값·모집단 분포와 함께. 절대 하한은 `check`에만.
- D14 F는 P90 ∧ 180일.
- D15 `component.strategy=auto` 기본, 결정 결과 인쇄.
- D16 커버리지는 라인 커버리지로만, 일시 jacoco.
- D17 이력 백엔드 JGit 단독 기본, 네이티브는 옵트인·적합성·인쇄·델타 거부.
- D18 blame 미사용(예외: 캠페인 생성 시 1회, D57). 이력 지표는 log/diff에서만.
- D19 게이트는 원값, 스캔은 백분위.
- D20 검증 최종어는 `validated`이며 "≠ 등가 증명" 고정 문구.
- D21 L2는 샌드박스 필수, 최소 권한 토큰, 소스는 데이터.
- D22 findings는 `priority · interpretation · confidence · evidence`로 낸다.
- D23 `Dx = √(pct(union_dup_tokens) × pct(active_twin_ratio))`.

**v3.3 결정**
- D24 모집단 셋(`active`/`dx`/`all`)과 렌즈 매핑(H·Dx / Dx / F). 필드별 모집단 기록.
- D25 시간 앵커 = HEAD 커미터 시각. `scanned_at`은 감사용.
- D26 예시 JSON은 적합성 픽스처. 손으로 쓴 숫자 금지.
- D27 H·tc 변경 단위 = `chg_commits`(잠금). `chg_days`는 비교 실험.
- D28 렌즈 confidence = 성분 최소. 멤버십 = `pct ≥ 0.90/0.75`. tie-break `priority desc, path asc, id asc`.
- D29 `active_twin_ratio`: twins=0 → null; Dx 모집단 = `dx`. composite는 세 렌즈 모두 non-null일 때만.
- D30 파일 내용 ID는 git blob 공식으로 통일; `repository_state_id`/`analysis_input_id`/`classes_id` 분리; 환경은 major.minor.patch.
- D31 `equivalence_basis ∈ {structural, tests, none}`; `structural`은 증명이 아님을 정의에 명시.
- D32 목표 개선은 지표별 합격 함수로.
- D33 L2 의존성 = 사전 적재 캐시 + 락파일, 저장소 허용 목록은 폴백. LLM 출력은 타입 제약 스키마(옵션 ID·소스 루트 내 편집만).

**v3.4 결정(기능 추가 없음)**
- D34 렌즈 백분위 계약(H→`active`, Dx→`dx`, F→`all`; 0 포함, null 제외). `interpretation`은 렌즈 백분위만 쓴다.
- D35 분위 = type-7 선형 보간. `P90(age_last_days)`는 유효 나이만.
- D36 confidence `low`에 `IQR = 0` 포함.
- D37 나이 미상 → F = null, `reason: age_unknown`.
- D38 `percentile_population.reason`으로 "값 null"과 "모집단 제외" 구분.
- D39 용어 `duplicate_cluster`, ID = 해시 + 토큰 수(CPD `Match`의 원래 의미).
- D40 새 중복 = 발생 수준 + rename 매핑.
- D41 중복 합격 = `target_pairs` 전부 + 새 발생 없음.
- D42 P1a = 구성타당도(기준선 넷, 증분 리프트, 사전 등록); P1b = 결과타당도; 부트스트랩 CI 기록; 수치는 휴리스틱.
- D43 `analysis_input_id`는 내용 해시; `classes_reproduction_inputs` 명명.
- D44 `expected.json` 변경은 `fixture_change` 필수.
- D45 L2 1차 = Gradle.

**v3.5 결정(철학)**
- D46 §1의 철학은 결정 규칙이다. 충돌하는 제안은 계약이 정교해도 받지 않는다.
- D47 변경 리포트(`change`)가 1차 표면, `scan`은 지도, `check`는 `change.json`의 정책 소비자. 새 측정 없음.
- D48 (v3.7.2 개정) 저작 무관의 사회적 논거 철회. 남는 하드룰 셋: **`.jqradar/`에 정체 저장 금지**(커밋 대상은 영구·공유; "정체"는 이름·이메일·계정 핸들이다 — **PR 번호·커밋 SHA는 정체가 아니라 리포가 이미 노출하는 산출물 참조**이며, 이를 해시로 가리는 것은 뒤집히는 연극이고 `--live`의 PR 추적을 잃는다), **AI/사람 추론 금지**(선언된 트레일러만), **개인 순위·리더보드 표면 금지**(B.2를 사람에 적용). 그 외는 `people.attribution`으로 조직이 정한다(D11). 근거는 도덕이 아니라 경험(DORA·SPACE)·데이터 최소화·정확도.
- D49 (v3.5) 이력 저장소와 규칙 승격은 백로그 — **v3.6에서 부분 번복**: 원장은 범위 안으로(D55), 규칙 승격은 v3.8.

**v3.6 결정 — 브라운필드, "지키는 것"의 수정 포함**
- D50 §0 규칙 수정: 철학과의 충돌은 거부가 아니라 결정을 요구한다 — 제안을 버리거나 철학을 고친다. 기록한다.
- D51 A.1 → 두 방향(보호: 변경 단위 / 개선: 원장 단위). A.8 신설(브라운필드가 기본, 변경이 닿는 부채부터, 앵커 값 불변).
- D52 B.2 수정: 부채 캠페인은 앵커에 얼린 분류로 진전을 잰다 — 판결이 아니라 착수 순서.
- D53 B.3 수정: 기준선은 둘 — 움직이는 보호 기준선(merge-base)과 고정된 캠페인 앵커. 리포 간 비교 금지 유지.
- D54 B.6 수정: 정책은 이름 붙은 자리들(`check` 프로필, 캠페인 정의)에 조직 이름·해시로.
- D55 (개정) 셋째 표면 = 부채 원장 = **파생 층(저장 안 함: 앵커·HEAD 스캔) ⊕ 사건 층(저장: 수정 PR의 claim·validation)**. 뷰는 어느 커밋에서든 결정적으로 재구성. 기본 뷰 top 20.
- D56 (v3.7.1 개정) `anchor_class`는 앵커 시점 렌즈 백분위(0.90/0.75)로 얼려 **결정 산출물로 저장**(`anchor-classes.json`), finding당 불변. 툴체인 재스캔에 흔들리지 않는다.
- D57 blame 한정 재도입: 캠페인 생성 1회, 원장 finding 영역만, 방법·신뢰도 기록, 결과는 `.jqradar/campaigns/<name>.estimates.json`에 커밋(재생성 가능). 매 스캔 blame 금지(D18)는 유지되며 픽스처로 강제.
- D58 `target`은 조직이 캠페인에 적는 데이터. 도구는 담고 추적만, 기본 목표 없음.
- D59 (개정) 일정 16 → **17주**. 자르는 순서 넷째에 한정 blame. 원장 자체는 불가침.
- D60 저장 위치 = 리포 안 `.jqradar/`, 커밋 대상. 별도 서버 없음(서버는 O6 대시보드에서도 읽는 소비자일 뿐). 동반 리포는 옵션, 기본 아님. (O13 닫힘)
- D61 사건은 **수정 PR당 파일 하나**, PR이 자기 diff에 싣는다. `closed` 사건은 쓰지 않는다 — 머지가 종료 행위. 일반 PR과 `scan`·`change`·`check`는 `.jqradar/`에 쓰지 않는다(픽스처로 강제).
- D62 `campaign close`가 `events/<campaign>/`을 트리에서 제거하고 `summary.json`을 남긴다. 과거는 git 이력, `ledger --at`으로 재구성. 6개월 넘은 활성 캠페인에 종료 권고.
- D63 같은 finding의 중복 claim은 git 충돌이 아니라 뷰의 조정 신호(`in_progress (PR n개)`), `claim`은 경고. `.jqradar/events/**`에 `linguist-generated`.
- D64 `id_drift`·`closed_unclaimed`·`validated_not_resolved`·`closed_unverified`처럼 도구가 가르지 못하거나 사람이 규칙을 넘은 상태는 숨기지 않고 표시한다. (v3.6.1: `regressed_or_id_drift`는 후속 판정으로 `regressed`와 `id_drift`로 갈라졌다)
- D65 커밋 트레일러 방식은 스쿼시 머지에서 사건이 사라질 수 있어 채택하지 않음(P15 결과에 따라 병행 재검토).
- D66 (v3.6) HTML 렌더러는 **인터랙티브 자립형 단일 파일**(d3 인라인, 네트워크 0건) — §7.1 스펙. 지도(A)·변경 리포트(B)·원장(C) 세 표면.
- D67 (v3.6) 렌더러 **판정 색 금지** — 농도와 방향 기호만. 예외는 `gate.json`의 정책 결과. 판정 어휘 사전 검사를 픽스처로.
- D68 (v3.6) 추세 차트는 이력 저장소(v3.8) 전까지 없음. 두 점(앵커·지금)만, 빈 자리에 "추세는 v3.8" 명시 — 과대 약속 금지.
- D69 (v3.6) 메서드 표·의존성 휠(A7–A8)은 `method_spread`·`change_axes` 측정 채택 시 활성 — 해당 측정은 별도 승인 대기.

**v3.6.1 결정 — 원장의 판정 의미**
- D70 finding 정체성은 종류별 계약(§5.5 표). 규칙 ID 기반 "아키텍처 위반"은 없다 — 규칙은 ArchRules의 층.
- D71 `succession ∈ {same, moved, split, merged, removed, unknown}`을 토큰 출처(80/20)로 판정하고, 해소는 **후속 집합 전체**에 합격 함수. 삭제는 해소가 아니다.
- D72 쓰는 사건은 `claimed`·`validation_passed`·`validation_failed`만. 머지 여부·순서·`superseded`는 git first-parent 이력에서 파생. ~~최종 머지 사건이 `event_status`를 소유.~~ (v3.7.3: 소유는 전이 커밋 — D100)
- ~~D73 유효 상태 = derived × 최종 머지 사건.~~ (v3.7.3: 전이 이력으로 대체 — D99·D103. `validated`는 PR 시점, `closed`는 앵커 대비라는 구분만 유지)
- D74 뷰 둘: `--at`(머지분만, 결정적, 재구성 테스트 대상) / `--live`(claim 브랜치 포함, 시점 의존). `in_progress`·`stale_claim`은 `--live`에만.
- D75 (v3.7.1 개정) scope는 finding 선택이지 회계 경계가 아니다. **`targets`는 scope 안, `guardrails`는 리포 전체**(기본 ≤ 앵커). `relocated_out_of_scope`는 open 유지. scope 변경은 `reanchor` = 새 계보.
- D76 `first_seen_estimate` → `first_observed_estimate`. "최초 발생"이 아니라 "이력 흔적을 처음 확인한 시점". UI 고정 문구.
- D77 `anchor_class`(진척, 불변)와 `current_priority`(현재 조사)를 분리 표기. 원장 정렬은 전자, 다음 작업 선택은 후자.
- D78 `campaign_mode: tracking_only | target_driven`, `goal_status`. 목표 없는 원장은 추적기임을 표기.
- D79 원장 계약은 `contract/ledger` 픽스처를 먼저 고정하고 구현한다. 재구성 결정성(같은 커밋 → 바이트 동일)은 출시 조건.

**v3.7 결정 — 자기 적용**
- D80 B.7 신설: jQRadar의 첫 대상은 jQRadar. 용어는 *self-application*(도그푸딩 병기), 절차는 컴파일러 stage 부트스트랩을 빌린다.
- D81 S1–S5를 G1–G4 게이트의 통과 조건에 포함. S2(자기 게이트) 우회는 §0 기록 없이는 금지.
- D82 S3의 첫 캠페인은 G2 커밋 앵커, scope = core, `target_driven`. S4는 자동 선택 상위 3건을 자기 수정 경로로 **끝까지 통과**(성공 아닌 정직한 완주), 전부 `not_validated`면 최대 3건 확장 후 멈춤.
- D83 S5(출시 조건) = 자기 원장의 재현 가능성 + 정직성. 닫혔는지가 아니라 숨기지 않았는지가 조건.
- D84 자기 적용은 외부 배터리·외부 파일럿·사람 검증자를 대체하지 않는다(Trusting Trust). 자기 적용 데이터는 내부자 데이터로 표시.
- D85 GitHub Spec Kit은 검토 후 보류. 개발 거버넌스는 외부 절차가 아니라 jQRadar 자신의 게이트(§9).

**v3.7.1 결정 — 증거 사슬 identity → validation → merge → ledger**
- D86 재현성 정체성 셋: `repository_state_id`(트리) / `analysis_input_id`(툴체인·계약·입력 포함, 캐시 키) / `validated_tree_id`(검증 대상). 원칙 둘을 B.4에.
- D87 `analysis_input_id`에 schema·contract·core·엔진 버전·이력 백엔드·알고리즘 버전 포함. 포함되지 않은 입력은 결과에 영향을 주어서는 안 된다(픽스처).
- D88 캠페인 앵커는 `repository_state_id`로 봉인. 툴체인 변경 시 앵커 트리 재스캔. `anchor_class`는 저장(D56).
- D89 검증 = 결과 + 검증 입력 정체성. `validated_tree_id` 없는 `passed`는 `none`.
- D90 `merge_drift`는 실패가 아니라 구분자. `validation_scope ∈ {pre_merge, post_merge}` 표기. post-merge 요구는 조직 정책.
- D91 `validated_not_resolved`는 검증 트리 재스캔부터 4분기. `validator_mismatch`는 그 재스캔에서도 open일 때만.
- D92 `reanchor` = 종료 + `supersedes` 계보의 새 캠페인. 앵커 변경 명령이 아니다.
- D93 succession은 kind별 알고리즘(파일/토큰/SCC/쌍 계보). split 혼합은 ≥ 50% 밖이면 `relocated_out_of_scope`.
- D94 사건 멱등성: `(campaign, finding, pr)`당 파일 하나, `claim_id`. 머지 전 가변 초안 / 머지 후 불변 사건. `actor_type`은 경로.
- D95 분석 산출물은 `reproduce`, 사건·캠페인은 `provenance`.
- D96 P1a는 180일 완전 관측 코호트만(검열 계약). S4 표본은 자동 선택 + succession ≠ same 1건.
- D97 L1′: 신뢰하지 않는 리포의 정적 분석도 프로세스 격리. 감사 로그는 샌드박스 밖 MCP 신뢰 경계.
- D98 NCCD 게이트는 컴포넌트 집합 변화 시 `context_changed`. 20% cx 감소는 기본 휴리스틱으로 격하.

**v3.7.3 결정 — 원장 상태의 전이 모델**
- D99 원장 상태는 "현재 파생 × 최종 머지 사건"이 아니라 **전이 이력**으로 계산한다. "가장 최근 머지된 사건이 소유"는 폐기.
- D100 **귀속 = 전이가 일어난 커밋.** 그 커밋이 사건을 실었으면 그 claim, 아니면 커밋 SHA(`closed_unclaimed`). 시간 순서는 인과가 아니다.
- D101 `closed_unverified`는 해소 전이를 만든 커밋이 `validation_failed` 사건을 실은 경우에만. 다른 커밋의 실패 사건은 기소 근거가 아니다.
- D102 `regressed`는 claim 유무와 무관 — 해소 전이 뒤 `resolved→open` 전이가 있으면 성립.
- D103 전이를 만들지 못한 머지 사건은 `merged_without_effect`이고 원인은 검증 트리 재스캔부터: `validator_mismatch`(선언 범위가 검증 트리에서도 open) / `partially_resolved`(선언 부분집합만 해소) / `merge_drift` / `superseded`. 해소·회귀 판정은 원값·국소 재스캔이라 어느 커밋에서든 계산 가능 — **단 순환 finding은 예외**(D106).

**v3.7.4 결정 — 경계 조건**
- D104 국소 측정은 내용 주소 캐시(`content_id`+엔진 버전), 전이 목록은 `(finding, commit, analysis_input_id)` 캐시. 툴체인 변경 시 전체 재계산을 P7 캐시 무효화 시나리오로 잰다.
- D105 변경된 실행 가능 라인이 0이면 커버리지는 `not_applicable`(실패 아님); 검증은 빌드·전체 테스트·재스캔·`equivalence_basis`로.
- D106 순환 finding의 전이는 리포트가 있는 커밋에서만 정확. 사이 커밋은 import 기반 소스 의존 그래프로 근사하고 `transition_basis: source_imports` 표기. 근사 불일치율은 P14.
- D107 succession 토큰 비율의 분모는 앵커 finding 토큰. 토큰 출처가 실패하면 메서드 시그니처 계보(PMD AST)로 보조. 호출 그래프는 과거 커밋에 없어 계보에 쓰지 않는다.
- D108 D48의 "정체"는 이름·이메일·계정 핸들. PR 번호·커밋 SHA는 리포가 이미 노출하는 산출물 참조이며 해시로 가리지 않는다.
- D109 S4는 성공이 아니라 정직한 완주. 전부 `not_validated`면 사유 기록 후 최대 3건 확장, 그 뒤 멈춤. 검증 예외 승인 워크플로 없음.

**열어둔 것**
- O3 WARN→FAIL 승격 — 조직 결정.
- O4 스쿼시 리포 PR 그룹핑 — P2.
- O5 미커버 영역 `apply` 거부 vs 경고 — P5.
- O6 다중 리포 집계 — 리포 간 순위 위험.
- O7 외부 참조 모집단 — 기본 꺼짐.
- O8 네이티브 git 적합성(`chg_*`·`churn`·공변경 완전 일치, rename 경로 ≥ 99%, `age_last_days` ±1일, git 버전 기록) — blame 제거로 우선순위 낮음.
- ~~O9~~ → D27로 잠금. 잔여: P2 비교 실험 결과에 따른 다음 개정 논의.
- O10 테스트 클래스 스트림.
- O11 (v3.3) 언어별 백분위를 합친 뒤 `interpretation` 임계를 언어별로 둘지 — Kotlin 파일 수가 적은 리포에서 `dx`처럼 null이 잦을 수 있다. 배터리 A의 Kotlin 혼합 리포.
- O12 Maven L2 지원 — 의존성 재현(락) 계약이 먼저 필요. 다음 판.
- ~~O13 원장·캠페인 저장 위치~~ → D60으로 닫힘. 잔여: 동반 리포 옵션을 기본으로 올릴지는 P15(파일럿)의 잡음 불만 비율로.

---

## 11. 비목표 — 할 수 있지만 하지 않는 것
- **절대 품질 등급**("건강도 72점")을 리포 간 비교 가능한 형태로 내는 것. 복합 점수는 이름 붙은 프로필로만, 헤드라인은 H, 리포 간 비교 기능은 만들지 않는다(B.3).
- **개인 순위·리더보드 표면. AI/사람 추론. 리포(`.jqradar/`)에 정체 저장.** 저자 *사실*은 조직이 `people.attribution`으로 켠 범위에서 계산한다 — 금지가 아니라 기본 꺼짐(D11·D48). 도구가 하지 않는 것은 사람에 대한 *판결 표면*과 *추론*이다.
- **기본 브랜치 자동 커밋·자동 머지.** 모든 적용은 브랜치, 머지는 사람(D7).
- **아키텍처 자동 변경.** 인터페이스 추출·컴포넌트 분리·순환 끊기는 제안까지(D6).
- **의미 동치 증명.** `validated`는 증명이 아니다. 뮤테이션 테스트·차등 퍼징은 범위 밖 — 다음 도구.
- **GitClear식 추세 진단**(복사 대 이동 비율, 연결성). jQRadar는 스냅샷 렌즈 + 델타 + 앵커 대비 개선이며 그 파생 지표는 재지 않는다.
- **네 번째 분석 엔진**(임베딩, 커버리지 필수화, 이슈 트래커, 런타임). PMD·ArchUnit·JGit으로 고정.
- **PMD 룰셋 판정을 우리 이름으로 내는 것.** GodClass 등 임계값 규칙은 규칙 층(ArchRules·PMD)의 것. 우리는 quickstart 참조 룰셋을 설명용으로만.
- **핫스팟 순위를 점수로 곱하는 것.** 성분은 사실로 내되 곱하지 않는다.
- **매 스캔 blame.** 유일한 예외는 캠페인 생성 시 한정 1회(D57).
- **부채 전부 해소를 목표로 하는 것.** 캠페인은 조직이 고른 부분집합이고, 도구는 목표를 정하지 않는다(A.8, D58).
- **원장을 외부 서버에 두는 것.** 서버는 다중 리포 대시보드(O6)에서도 읽는 소비자일 뿐(D60).
- **관측기(`scan`·`change`)의 설정 파일.** 정책은 `check` 프로필과 캠페인 정의 두 자리에만(B.6).

## 12. 위험
- **P1a 실패**: 핫스팟이 이 조직 리포에서 개입도 예측하지 못하면 헤드라인이 무너진다. G2 전 수정 워크플로 미착수.
- **검증 부담**: 테스트가 빈약한 브라운필드에서 `apply`의 대부분이 `not_validated`가 된다. 정직한 결과다. 도구가 테스트를 대신 쓰지는 않는다.
- **팀 순위 압력**: 리포 점수는 팀 점수로 읽힌다. 복합 점수는 헤드라인이 아니고, 리포 간 비교 기능은 만들지 않는다. 캠페인 원장도 리포 내부 기준이다.
- **라인 커버리지의 한계**: 실행 ≠ 단언. 커버리지 0.9의 `validated`도 단언 없는 테스트 위에 서 있을 수 있다. PR 고정 문구.
- **샌드박스 잔여 위험**: 컨테이너 탈출, 허용 목록 저장소 손상, 프롬프트 인젝션의 새 변종. P9는 알려진 벡터만 검사한다. 구조적 방어(LLM은 옵션 ID·소스 루트 내 편집만)가 마지막 선, 감사 로그가 사후 추적.
- **재현성 vs 성능**: 네이티브 git 가속기는 옵트인·적합성·인쇄로 막아도 "다른 머신, 다른 git 버전"이 남는다. blame 제거로 발생 확률은 낮아졌다.
- **재배치 플래그의 해석**: 좋은 추출과 쪼개기를 도구가 가르지 못한다. 증거를 붙이고 사람이 본다.
- **Kotlin 기대치**: "Java/Kotlin" 문구가 PMD 악취까지 기대하게 만든다. 문서·UI에 범위를 반복 표기.
- **계약 간 충돌**: 계약을 각각 잘 썼는데 합치면 모순인 경우가 반복된다(모집단 정의와 F 렌즈, 시간 기준점, 검증과 해소). 적합성 스위트가 그 방어선이지만 스위트도 사람이 쓴 기대값 위에 서 있다 — G0에서 계약을 교차 검토하는 리뷰어를 두 명 이상 둔다.
- **P1a 사전 등록**: 배터리 B 결과를 본 뒤 실험 설계를 바꾸면 검증이 아니다. G0에서 설계를 고정하고, 변경이 불가피하면 이유와 함께 기록한다.
- **철학과 기계장치의 간격**: §1은 "진화 관찰 시스템"이라 하지만 이력 저장소 전까지는 스냅샷 + 델타 + 앵커 대비 개선이다. 문서·UI가 A.6을 기능처럼 말하면 과대 약속이다. 그때까지는 "이 변경"·"지금 지도"·"이 캠페인"만 말한다.
- **철학의 마모**: 감사 회차는 계약을 조이고 목적은 보지 않는다 — §1이 계약 문장으로 마모된다. 매 판 §1을 소유자가 다시 읽는 것을 릴리스 절차에 넣는다.
- **앵커의 노화**: 캠페인이 길어지면 앵커 시점 분류와 현재 실체가 벌어진다("앵커에서 high였지만 지금은 사소함"). 분류는 얼려 두되 원장 뷰는 앵커 값과 현재 값을 나란히 보이고, 재앵커는 조직의 명시적 행위로만.
- **원장 ID 드리프트**: rename·이동·분할에서 거짓 상태. 상태를 저장하지 않으므로 파일에 굳지 않고, 후속 판정이 `unknown`을 `id_drift`로 드러낸다. P14가 재고, 5% 넘으면 토큰 출처 임계 조정·정체성 강화.
- **생소한 조합**: 부품(Changesets·rubocop_todo·Betterer·ADR·DVC)은 흔하지만 이 조합은 새것이다. P15 파일럿 전까지는 "검증된 방식"이라 말하지 않는다. 온보딩은 선례 용어로 설명한다.
- **`.jqradar/`가 Terraform state가 되는 날**: 작고·머지 뒤 불변·PR당 하나라는 성질 때문에 리포에 둘 수 있다. 매 스캔이 무언가를 쓰기 시작하면 그 성질이 깨지고 리포를 떠나야 한다 — 픽스처가 그 선을 지킨다(D61).
- **렌더러가 둘째 판정 층이 되는 것**: 색과 배치는 말없이 판정한다. 빨강 하나로 "나쁨"이 되고 크기 하나로 "중요"가 된다. D67(농도·방향만)과 판정 어휘 검사가 그 선이지만, 크기 = `loc`이 "큰 파일 = 문제"로 읽히는 것까지는 막지 못한다 — 범례에 "크기는 코드 양이지 문제 크기가 아니다"를 고정 문구로.
- **캠페인 중 툴체인 업그레이드**: 앵커 트리를 새 툴체인으로 재스캔하면 파생 값이 움직인다. `anchor_class`는 저장돼 불변이지만 `anchor_values`는 "현재 툴체인으로 잰 앵커"라고 표기해야 한다 — 그렇지 않으면 "95였는데 왜 92냐"가 나온다.
- **`merge_drift`의 일상화**: 활성 main에서는 거의 모든 `closed`가 `merge_drift: true`다. 그것을 경고처럼 그리면 잡음이고, 숨기면 거짓이다 — 구분자로 표시하되 색을 주지 않는다(D67).
- **Trusting Trust**: jQRadar가 못 보는 악화는 jQRadar만으로 jQRadar를 게이트하는 한 영속한다. 자기 적용을 하면서 외부 배터리·파일럿·사람 검증을 줄이려는 유혹이 생길 것이다 — 그 순간 자기 맹점이 굳는다. D84가 선이다.
- **저작 정책의 결과**: 금지를 풀었으니 `individual`을 켠 조직에서 개인 지표가 게이밍·저항을 낳는지는 이제 우리 주장이 아니라 관찰 대상이다(P15). 우리가 틀렸다면 — 아무 문제 없다면 — 기본값을 `team`으로 올리는 논의를 한다. 우리가 맞았다면 기본 `off`가 데이터로 정당화된다. 어느 쪽이든 도구가 조직 대신 결정하지 않는다.
- **자기 적용의 편향**: 우리는 자기 지표를 게이밍하는 법을 가장 잘 안다. 우리 PR에서 `relocation`·`validated_not_resolved`가 뜨는 빈도를 P15 파일럿 팀과 비교해 우리가 유독 깨끗하면 의심한다.
- **전이 스캔 비용**: 상태를 전이 이력으로 계산하려면 finding 파일을 건드린 머지마다 국소 재스캔이 필요하다. 원값·국소라 싸지만 캠페인이 크고 오래되면 `--at` 뷰 시간이 늘어난다 — P7 매트릭스의 전이 스캔 행이 잰다. 캐시 무효화(툴체인 변경)가 전이 전체를 다시 계산하게 만드는 것도 여기 든다.
- **`--live`의 유혹**: 시점 의존 뷰가 편해서 결정적 뷰 대신 쓰이기 시작하면 재현성 주장이 새는 자리가 된다. `--live` 출력에 "시점 의존, 재현 대상 아님" 고정 문구.
- **프런트엔드 범위 확장**: 인터랙티브 맵은 쉽게 커진다. §7.1의 A1–A8·B1–B5·C1–C4 밖의 뷰는 백로그. W8–10이 빡빡해 A7–A8·C는 W16–17로 뒀다.
- **한정 blame의 재확장 압력**: "한 번만"이 "가끔"이 되고 "매 스캔"이 된다. 매 스캔 경로에서 blame 호출 시 실패하는 픽스처로 D57의 예외 범위를 고정.
- **부채 전부를 겨누는 캠페인**: A.8 위반. scope 없는 캠페인에 경고, 원장 뷰 기본 top 20.
- **"지키는 것"을 다시 헌법으로 다루는 습관**: 이번에 B.2·B.3·B.6을 고친 것은 옳았고, 다음에도 필요하면 고쳐야 한다. §0의 규칙이 그것을 허용한다.
