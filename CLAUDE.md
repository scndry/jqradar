# CLAUDE.md — jQRadar

이 리포는 jQRadar(Java Quality Radar)를 만든다. **`prd.md`가 진실이다.** 코드·픽스처·문서가 `prd.md`와 어긋나면 조용히 다르게 구현하지 말고, `prd.md`를 고치는 변경을 같은 PR에 넣고 §0에 기록한다. 충돌은 결정을 요구한다 — 제안을 버리거나 철학을 고친다(§0 규칙).

jQRadar는 jQRadar로 만든다(§1 B.7). 이 리포가 첫 대상이다. 지금은 **S0 단계(G0 전)**: 도구는 없고, 개발 절차가 철학을 따른다.

---

## 1. 결정 규칙 — 무엇을 제안·구현하든 먼저 여기에 비춘다 (`prd.md` §1 B)

- **B.1 증인 셋.** PMD(메트릭·quickstart 참조 룰셋·CPD), ArchUnit(`ClassFileImporter` + `ArchitectureMetrics` — 어설션 아님), JGit(log·diff — 매 스캔 blame 없음). **네 번째 엔진을 추가하지 않는다.** OpenRewrite는 §6.5의 수정기다.
- **B.2 현장 ≠ 판결.** 점수·순위·심각도를 만들지 않는다. 산출물은 `priority · interpretation · confidence · evidence`. 아키텍처 변경은 제안까지.
- **B.3 자기 기준선.** 성분은 리포 내 백분위(§2.5). 절대 임계는 `scan`에 없다. 리포 간 비교·사람 순위 표면은 만들지 않는다.
- **B.4 다시 계산할 수 없는 숫자는 의견이다.** 숫자 → 측정 → 계약 → 픽스처. 예시·기대값을 손으로 쓰지 않는다. 재현성 정체성 셋: `repository_state_id` / `analysis_input_id`(툴체인·계약 버전 포함) / `validated_tree_id`.
- **B.5 겸손한 수정.** 브랜치에서만, 샌드박스에서만, 검증과 함께. `validated ≠ 등가 증명`.
- **B.6 정책은 조직의 것.** 조직이 적는 자리는 셋뿐 — `check` 프로필, 캠페인 정의, `jqradar.yml`의 `people` 절. `scan`·`change`·`ledger`는 무설정.
- **B.7 먼저 우리에게.** G1부터 이 리포를 스캔하고, G2부터 이 리포의 PR을 `jqradarCheck`로 게이트한다.

---

## 2. 하드룰 — 어떤 이유로도 하지 않는다

- 기본 브랜치에 직접 커밋·푸시. 모든 작업은 브랜치 + PR.
- **픽스처 없이 계약을 구현**. `contract/<계약>/<케이스>/`에 합성 리포 + `expected.json`을 먼저 박고, 구현은 그 설명이다(§2.9).
- `expected.json`을 손으로 고치기. 바꾸려면 `fixture_change {reason, library, old, new, measure, note}`를 같은 커밋에(§2.9).
- 매 스캔·매 `change` 경로에서 `git blame` 호출, 또는 `.jqradar/`에 쓰기(D18·D61). 위반은 픽스처가 잡는다.
- `.jqradar/`에 이름·이메일·계정 핸들 저장(D48·D108). PR 번호·커밋 SHA는 정체가 아니다.
- 출력·UI에 판정 어휘(bad / poor / 나쁨 / 위험 / 불량 …)와 좋음·나쁨 색(D67).
- 렌더러에서 JSON에 없는 숫자를 계산하거나 점수·순위를 만들기(D28).
- `prd.md` 본문(§1–§12)에 "이전 판과 같음"·"vX §n 그대로" 식 참조, 편집 메모, `(vX.Y)` 태그(문서 규칙 1·2). 이력은 §0에만.
- 저자·AI 여부를 **추론**하기. `declared_ai_assistance`는 커밋 트레일러에서 선언된 것만(D48).

---

## 3. 지금 할 일 — S0 / G0 (W1–3, `prd.md` §9)

G0 통과 조건은 `prd.md` §9 "G0 체크리스트" 7항목. 순서:

1. **읽기.** `prd.md` §1(철학), §2(측정 계약), §2.9(적합성 스위트), §5(변경·원장·게이트), §6.3–6.6(검증·보안), §7·§7.1(스키마·렌더러), §9(검증 계획·자기 적용), §10(결정 D1–D109). 제안하기 전에 D 번호로 근거를 댄다.
2. **`contract/` 스켈레톤과 G0 픽스처.** 디렉터리: `percentile/ reproducibility/ cpd/ history/ graph/`(G0) · `lens/ gate/ renderer/`(G1) · `ledger/ validation/ security/`(G2b·G3). 각 케이스 = 합성 리포를 스크립트로 생성 + `expected.json`. 최소 케이스 목록은 §2.9 표. **기대값은 계산으로 만들고, 계산 스크립트를 함께 커밋한다.**
3. **JSON Schema 6종** → `schemas/`: `report`, `change`, `gate`, `validate`, `campaign`, `event`. §7의 jsonc 스케치를 기계 검증 가능하게. `contract` 부분집합(`reproduce·measurements·conflicts·delta`)을 스키마에 명시.
4. **Gradle 멀티모듈 골격**: `jqradar-core`, `jqradar-cli`, `jqradar-gradle-plugin`, `jqradar-ledger`, `jqradar-mcp`, `jqradar-remediation`(§4.1). 의존 버전은 `gradle/libs.versions.toml`에 major.minor.patch로 고정(§2.8 `environment`).
5. **자체 ArchUnit 규칙**(우리 코드에만): `jqradar-core`가 `people` 정책 없이 `PersonIdent` 이름·이메일을 산출물로 내보내지 않는다; `scan`/`change` 경로에서 `BlameCommand` 호출 없음; `.jqradar/` 쓰기는 `jqradar-ledger`만.
6. **P1a 사전 등록** → `docs/preregistration/p1a.md`: 기준선 넷(random / cx-only / chg-only / H), 개입 제외 규칙, `evaluation_cutoff`·180일 완전 관측 코호트, 부트스트랩 95% CI. 배터리 B 전에 바꾸지 않는다.
7. **배터리 리포 확정** → `docs/battery.md`: 나이·크기로만 선정(§9). 이 리포는 S1 이후 내부자 데이터.

G0 전에는 **core 측정 코드를 쓰지 않는다.** 계약과 픽스처가 먼저다 — v3.1·v3.2의 산술 오류와 v3.3의 계약 충돌이 그 이유다.

---

## 4. 코드 규약

- Java 21, Gradle(Kotlin DSL), JUnit 5. Kotlin은 대상 언어이지 구현 언어가 아니다.
- 모듈 경계: `core`는 빌드 도구·IDE·LLM 무지. `ledger`만 `.jqradar/`에 쓴다. `remediation`은 L2 샌드박스 안에서만 실행된다(§6.6).
- 측정은 순수 함수로: 같은 `analysis_input_id` → 같은 출력. 시간은 `HEAD_TIME`(HEAD 커미터 시각)에서만 읽는다(§2.7). `System.currentTimeMillis()`는 `scanned_at` 외에 쓰지 않는다.
- 캐시 키는 커밋이 아니라 **내용**(`content_id` + 엔진 버전)이다(§4.5).
- 픽스처 테스트는 `contract/`를 파라미터화 테스트로 돈다. 실패 메시지는 어느 계약(§n)이 깨졌는지 말한다.
- 렌더러(d3 인라인, 자립형 단일 HTML)는 JSON의 순수 함수. 네트워크 요청 0건(§7.1).

---

## 5. 커밋·PR 규율 (S0부터 — 나중에 우리 이력이 분석 대상이 된다)

- **머지 커밋 유지, 스쿼시 금지.** 이동·개명은 `git mv`. `chg_commits`·rename 매핑·`succession`이 우리 이력에서 계산 가능해야 한다(§2.7).
- `Co-authored-by:` 트레일러를 지우지 않는다 — `declared_ai_assistance`의 자료다(§5.1).
- 커밋 메시지 첫 줄에 계약 참조: `feat(core): §2.5 percentile engine (type-7 quantile)`.
- PR 본문에 반드시: 구현한 계약(§), 통과한 픽스처, `prd.md` 변경 여부와 §0 항목, "PRD 충돌" 섹션(없으면 "없음").
- `prd.md`를 고치면: §0에 항목, 결정이면 §10에 D 번호(기존 결정은 지우지 않고 취소선 + 대체 참조).

---

## 6. 세션 종료 전 체크

- [ ] 새 계약에 픽스처가 있고 통과하는가.
- [ ] `expected.json` 변경에 `fixture_change`가 있는가.
- [ ] `prd.md`와 충돌이 없는가 — 있으면 코드가 아니라 문서를 고치는 PR을 먼저.
- [ ] 하드룰 §2 위반이 없는가(blame·`.jqradar/`·정체·판정 어휘·네 번째 엔진).
- [ ] 이력 규율(머지 커밋·`git mv`·트레일러)을 지켰는가.
- [ ] 다음 세션이 이어받을 상태를 `docs/status.md`에 3줄로.

---

## 7. 모르면

추측으로 계약을 채우지 않는다. `prd.md`에 답이 없으면 (1) §10 열어둔 것(O·)에 해당하는지 보고, (2) 해당하면 그 결정 조건을 갖춘 실험이나 픽스처를 제안하고, (3) 해당하지 않으면 "PRD 공백"으로 PR에 적고 멈춘다. 계약 없는 구현보다 멈추는 것이 싸다.
