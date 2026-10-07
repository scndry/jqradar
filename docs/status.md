# 상태 — 다음 세션이 이어받을 것

**지금**: S0 / G0. **G0 체크리스트(§9) 7항목 중 남은 것은 #1 하나다.** v3.8.4가 그 조건을 바꿨다(D140) — 리뷰어의 종류가 아니라 **§2.1–2.9 교차 검토의 열린 발견이 0**인 것이고, 검토 주체는 **다중 모델 패널**이다(D141). "사람 2명·외부 1명" 요구는 G0에서 빠졌고 D84가 지키던 것은 G3의 외부 배터리·외부 파일럿으로 옮겼다(D142, `~~D84~~`). #2–#7은 CI가 매 PR에서 지킨다. **입구가 생겼다** — [`review/README.md`](review/README.md)와 `python3 docs/review/g0-review.py`(5분, 기계가 확인한 것 한 표 + 읽을 쌍 여덟). [`g0-review-packet.md`](g0-review-packet.md)는 참고 자료로 내렸다.

**#1의 범위는 §2.1–2.9다**(D136). §6.3–6.6 교차 검토는 값 층 픽스처(`contract/validation`·`security`)가 서는 **G3 입장 조건**으로 옮겼다 — 문장만 읽은 검토를 통과로 세지 않기 위해서다.

**있는 것**: `prd.md` v3.10.9(D1–D215). `contract/` 케이스 **211종** — percentile 6 · **schema 147** · cpd 7 · history 26 · graph 11 · reproducibility 14. 공용 모듈 `contract/tools/historywalk.py`(§4.5 걷기 — history·reproducibility가 같은 구현). CI 가드 하나 더: `ci/check-reproduce-kinds.sh`(§7 reproduce 줄마다 종류 표시). `schemas/` **8종**(`people.schema.json`, D161). Gradle 골격과 자체 ArchUnit 규칙 넷 + 반례(11 tests). CI **5잡**. `docs/preregistration/p1a.md`, `docs/battery.md`(실측).

**§2.9의 배정 공백은 닫혔다**: §2.4 파일 쌍(D134)과 §2.1 저자 사실(D135)이 `contract/history/`로 배정되고 케이스 넷이 섰다. 정체 부재 검사는 **출처로 가른다** — 저자 해시와 `repository_state_id`는 둘 다 64 hex라 모양으로 못 가르므로, 알고 있는 저자 식별자의 해시 72개가 산출물에 없음을 본다.

**v3.9.0이 열린 25 중 여섯을 주장으로 닫았다** — S5(D154 비교 대상) · N3(D158 `reproduce` 세 종류) · S6(D159 캐시 키 사영) · O-3(D155 스케일 표) · S13(D156 분수 파라미터 문자열) · R4-2(D157 시각 표기). 계약이 먼저 서고(`docs/prd-v390` 첫 커밋, 스위트 붉음) 스키마·린트·픽스처가 따라가 초록이 됐다: `percentile_method`의 `arithmetic`·`output`이 `required`, 분수 파라미터가 `type: string`(JSON 숫자 → 거부), 스케일 린트가 표 `D155-1` 전체를 보고(변조 5 추가) `display.RACD`가 4자리, 재현성 케이스 셋(비교 대상·시각 표기·캐시 키 사영, 반례 넷이 물었다). 표 `D155-1`을 글자 그대로 구현한 린트가 §7 예시에서 `age_last_days` 요약 넷을 잡았고 코드에서 채우지 않고 멈췄다 — 소유자가 §0-29 보정으로 표에 넣었다(판 번호 불변, PR #17의 전례). 같은 보정이 §4.5의 `cpd.language`(문서에 없던 파라미터)를 지웠고 픽스처가 따라갔다. **닫힘 표시가 붙었다** — 여섯 행에 근거 열과 `닫힘 — D154…D159`. 아래 출력은 그 뒤 계산기가 낸 것이다: 닫힘 11 · 열림 19. 이 수는 적은 것이 아니라 계산된 것이다.

**v3.9.1이 열린 19 중 셋을 주장으로 닫았다** — S2(D160 저작 정책은 id 입력) · S9(D161 저자 사실은 `people.json`, k는 팀 집계에) · R4-6(D162 off 닫힌 목록). 같은 순서: 계약 먼저(스위트 붉음 — 이번엔 §7 추출기의 '7개' 가정이 스키마보다 먼저 멈췄다) → 추출기·스키마 8종·변조 9 → 재현성 둘(토글·매핑 한 줄, 기존 다섯의 id 이동 = `fixture_change`) → history 둘(팀 접기·off 부재 검사) → 초록. `author_id`는 v3.9.2(D163, 한 줄 판)가 닫았다 — 조직 팀 매핑 파일이 정한 키이고 git 이름·이메일이 아니며, 매핑에 없는 저자는 `unmapped`로 접혀 `authors_unmapped`로 센다. 교차 검토 key가 아니라 닫힘 표시는 없다. **닫힘 표시가 붙었다** — 셋에 근거 열과 `닫힘 — D160·D161·D162`. `--count`: 닫힘 14 · 열림 16 — 계산기가 낸 수다.

**v3.9.3이 열린 16 중 넷을 주장으로 닫았다** — S7(D164 `shared`는 W 안, tc ≤ 1) · S4(D165 파일×클러스터 수준·새 발생 수·서로 다른 파일 ≥ 2·게이트 손잡이) · R2-5(D166 자기 중복은 한 파일에만 있는 클러스터의 것) · R1-9(D167 `hidden_couplings` 정렬 키). 이 군은 §7 예시의 모양을 바꾸지 않아 첫 커밋이 **초록**이었다 — 예고대로. 픽스처: `cpd/mixed-cluster`(200·200·0·1), `history/shared-window-limited`(두 창, tc ≤ 1 불변식 인쇄), `history/hidden-coupling-sort-order`(키 넷을 밟는 쌍 넷). `hidden_couplings` 배열이 쌍 있는 케이스에 더해져 기존 둘의 expected에 키가 늘었다(`fixture_change`). `gate/`(G1)는 문장만. **닫힘 표시가 붙었다** — 넷에 근거 열과 `닫힘 — D164·D165·D166·D167`. `--count`: 닫힘 18 · 열림 12 — 계산기가 낸 수다.

**v3.9.4가 열린 12 중 일곱을 주장으로 닫았다** — N1(D168 두 단계 기록, 뜻은 소속) · S3(D169 지름길의 렌즈별 조건) · S10+15(D170 적격 main 소스·`no_bytecode`) · O-4(D171 `interpretation`은 `lens_pct`의 함수, 항상 객체) · R1-5·R4-3(D172 composite는 렌즈가 아니다) · S14(D173 `population_note` 시험). 식은 건드리지 않았다 — §7의 렌즈 값·pct 전부 불변을 첫 커밋에서 대조했다(더한 것은 OrderService의 `cx.all` 0.9678·`fan_in.all` 0.8820). 첫 커밋의 붉음은 schema 36(예시가 옛 모양에 걸림) + 스케일 린트 8(리프 키가 모집단 이름) — 후자는 소유자가 예상 밖으로 잡아 D155-1 아래 "표의 이름은 경로에서 찾는다"를 적었고 린트가 경로 규칙을 얻었다. 스키마: 두 단계 `percentiles`·`percentile_population`, `lensPercentile`(항상 객체, pct null ↔ reason), `lens_percentiles`는 H·Dx·F로 닫힘, `arch_context` nullable, `fan_in` null → reason(if/then), `reason` + `no_bytecode`. 변조 +5, 재조준 3(`fixture_change`). `lens/`(G1)는 문장만. **닫힘 표시가 붙었다** — 일곱에 근거 열과 `닫힘 — D168…D173`. `--count`: 닫힘 25 · 열림 5 — 계산기가 낸 수다. 남은 다섯은 S8(§2.2·§2.4·§3.5) · S11(§2.6·§5.3·§6.3) · S12(§2.7·§5.5) · N6(§2.2·§5.3) · O-6(§2.2·§2.3) — 절이 흩어져 있어 군이 아니라 한 줄 판들일 듯하다.

**다섯 한 줄 판(v3.9.5–v3.9.9, D174–D178)이 남은 다섯을 닫았다** — S12(D174 W와 first-parent는 다른 질문) · N6(D175 SCC 게이트도 `context_changed`) · S8(D176 그래프 밖 쌍은 판정하지 않음) · O-6(D177 auto 분할은 1회) · S11(D165·D178 §6.3이 §5.3의 손잡이를 가리킴). 다섯 첫 커밋이 전부 초록이었고, 그중 둘(N6·S8)은 초록이 이행의 증거가 아니었다 — §7이 안 바뀌어 스위트가 옛 스키마를 몰랐다; 긍정 케이스(`accept-gate-scc-context-changed`·`accept-report-test-pair`)가 그 자리를 채웠다. 픽스처: `history/window-vs-first-parent`, `history/hidden-coupling-sort-order`의 (A,ATest), `graph/auto-oversized-grandchild-not-split`. **닫힘 표시가 붙었다** — `--count`: 닫힘 30 · 열림 0 · 밖 2. **열림 0은 D151의 정지 조건이 아니다**(§0-38) — 다음은 3차 라운드, 입력을 바꿔서: 쌍 목록에 §2 내부 쌍(§2.6↔§2.1 토크나이저)과 다섯 판이 만든 접점(§2.7↔§5.5, §2.2↔§5.3, §2.4↔§3.5의 null 정렬).

**3차 라운드(2026-10-06, 입력 `pairs@816c35bfca1d` — 처음으로 입력을 바꾼 라운드, D151(b))가 들어왔다.** 넷(Haiku·Sonnet·Opus·Fable, 각자 별도 세션, 넷 다 `--verify` 선행)의 기록과 종합(대응표 먼저)이 `docs/review/records/2026-10-06-*.md`에 있다. 계산기: **범위 안 총 70 = 닫힘 30 + 열림 40, 밖 16**. Haiku는 세 라운드 연속 0건·"모순 없음" 전부(통과의 증거가 아니다 — D141), 나머지 셋이 안 65·밖 16을 냈고 병합해 안 40·밖 14가 새 key다. 결정이 이웃 절에 안 내려간 모양이 아홉(reason 사전, D159의 사영이 측정 캐시에만, D175가 §5.3에만 + §7 gate.json의 SCC 행 PASS, '일'의 단위, 표 D155-1의 누락, reproduce 세 종류에 자리 없는 값, 산술 계약 밖의 double·log₂ …) — 3차 입력의 "볼 것"이 겨눈 그대로. Kotlin 축이 처음 열렸다(쌍 16 배정 §4.4). 쌍 9(토크나이저)는 사실상 아무도 못 봤다. **범위 안 새 발견 0이 아니므로 D151 연속의 첫째가 아니다** — 결정 판(묶음 열 개쯤)으로 간 뒤 쌍 목록이 또 바뀐다. 아래 출력 블록은 3차 뒤의 것이다.

**결정 판 묶음이 시작됐다 — 1/10 산술(v3.10.0, D179–D183, PR #49 머지)과 2/10 단위·표(v3.10.1, D184–D187).** 2/10의 구현 PR에서 스케일 린트가 산출물 8종 전부를 보게 되자 **§7 report 예시의 `age_last_days: 6`·`1250`과 evidence `value: 1250`을 `integer_in_scaled_field`로 잡았다** — D184(경과 시간은 2자리, 후행 0 유지)대로면 `6.00`·`1250.00`이어야 하고 §0-40의 "움직이는 수 셋"에 그 둘이 없다. prd.md의 자리라 코드에서 채우지 않았고 소유자 보정을 기다린다(§0-29의 `age_last_days` 보정과 같은 모양 — 표를 글자 그대로 구현한 린트가 예시의 빈 곳을 잡는 두 번째 사례). 그 보정 뒤 `check-all`이 초록이 된다. 닫힘 표시는 묶음들이 끝난 뒤 한 PR.

**3/10 reason 사전(v3.10.2, D188–D191).** 첫 커밋은 예고대로 초록 — §7의 수·모양 불변. 스키마가 따라갔다: `report.schema.json`의 `reason` enum 셋(성분·렌즈 / `arch_context`·`component` / `hiddenCoupling`)이 **`$defs.reason` 하나**(§2.5 표의 열 이름)로 모이고 자리마다 표의 셋째 열이 부분집합으로 걸렸다(`percentile_population`의 `age_last_days`·`fan_in`은 이름 붙은 자리, 나머지 성분은 소속 사유 셋; `lens_percentiles`의 H·Dx·F 각각; 쌍은 `outside_bytecode_scope`·`no_bytecode`; 컴포넌트는 `isolated_component`). finding은 `kind`별 if/then — 파일 렌즈 finding이면 `lens_pct`·`interpretation` required, 순환·Hidden Coupling이면 금지(D191). 긍정 둘(`invalid_metadata`인 F, `no_bytecode` 쌍) + 변조 다섯. `history/`: `uncommitted-file`(작업트리에만 있는 파일 → `uncommitted`, 옛 기본값 `age_unknown`이 3차 T2(b)의 '구현이 고른 이름'이었다), `hidden-coupling-sort-order`에 (A,M) `no_bytecode`·(P,PTest) 동률 → `outside_bytecode_scope` — 쌍의 사유는 파일의 이유(`class_graph_absent`)에서 계산하고, 그래프 밖 파일이 든 쌍에 boolean을 주면 계산기가 멈춘다. `--count`가 범위 밖을 열림/닫힘으로 갈라 센다(반례 10 `outside-closed-is-not-inside`) — 밖의 닫힘은 안의 수에 더하지 않는다(D152·D153). **PRD 공백 둘**(PR 본문): `change.json`의 `touched_legacy_findings[]`는 `anchor_class`가 모든 항목에 required이고 `kind`가 없어 순환·Hidden Coupling finding을 가를 수 없다(D191은 report의 finding에만 걸었다); §2.5 표의 `not_in_active`는 렌즈(H)에만 있어 active가 아닌데 `twins ≥ 1`인 파일의 Dx 사유에 이름이 없다(스키마는 표 그대로 — Dx에 `not_in_active`는 거부). 닫힘 표시는 묶음들 뒤 한 PR — 그때 밖 key S3-24·O3-9에도 붙는다. **공백 둘은 소유자가 같은 판 안에서 보정했다**(§0-41 보정, 판 번호 불변): `touched_legacy_findings[]`에 `kind`, `anchor_class`는 파일 렌즈 finding에만(D191 대괄호에 §5.7·§7); 표의 `not_in_active`에 Dx. 스키마가 따라갔다 — `change.schema.json` if/then(kind별) + 긍정 1·변조 3, report Dx 부분집합 + 긍정 1(보정 전 거부되던 문서가 통과한다는 것이 공백의 실물이었다).

**4/10 캐시 사영(v3.10.3, D192–D195).** 첫 커밋 초록 — §7 바이트 불변. `reproducibility/` 셋이 이행을 진다: `history-cache-key-is-a-projection`(백엔드 토글 → 층 1 전부 미스, `rename.similarity` → 전부 적중; 변조 셋 — 백엔드를 빼면 거짓 적중, 읽지 않는 파라미터를 넣으면 헛미스, §2.8 밖은 거부), `shallow-then-unshallow-no-false-hit`(합성 리포를 `--depth 2`로 떠서 경계 커밋의 층 1 항목이 **둘** — 관측된 부모 없음/있음; unshallow 재스캔 = fresh full clone과 바이트 동일; 관측된 부모를 키에서 빼면 A·B의 마지막 커밋이 경계 커밋으로 돌아온다 — O3-5의 실물), `transition-cache-hits-across-head`(새 커밋 → id 변경 ∧ 전이 키 전부 적중; `succession`·`class_roots` → 전부 미스; 창 안 커밋 목록을 넣으면 증분이 죽는다). **계산기의 구멍 하나**: `bytecode_scope` 범위 정의가 §2.8 (i)·§7 [id]인데 id 스펙에 없었다 — 전이 사영의 부분집합 검사가 잡아 스펙에 넣었고 재현성 id 전부가 움직였다(`fixture_change`, `percentile_method`와 같은 종류). `team_count` 키에서 `k_threshold`가 빠졌다(D186·D195). `identity-absent-when-attribution-off`가 `build/jqradar/` 캐시 디렉터리를 실제로 쓰고 훑는다(키에 저자 집합 → `must_be_caught`). 착지 반례 09 `range-is-not-landing` — 소유자의 세션이 `(D192–D195)` 범위 표기로 걸린 성질을 못 박았다. 닫힘 표시는 묶음들 뒤 한 PR.

**5/10 context_changed 착지(v3.10.4, D196–D198) — §7의 값이 바뀐 첫 판.** 첫 커밋은 예고대로 `validate.json`의 두 필드(`components`·`component_identifiers_equal`)에서만 붉었다(accept-validate + 파생 3, `additionalProperties: false`); `gate.json`의 SCC 행 `PASS → context_changed`는 스키마를 통과해 gate 쪽은 초록이 이행의 증거가 아니었다. 스키마가 따라갔다: `validate.schema.json` — 두 필드, `rule: cycle`이면 둘 다 required(if/then), `component_identifiers_equal: false` → `verdict: not_validated` ∧ `not_validated_reasons ∋ context_changed`(if/then); 긍정 1(`accept-validate-cycle-context-changed`) + 변조 2. `gate.schema.json` — **교차 제약**(`nccd_increase`가 `context_changed` ⇔ `new_component_cycle`도; `contains`/`not contains`라 조직 프로필이 한 규칙을 빼면 걸리지 않는다, B.6); 변조 2(한쪽만 `context_changed`, 양방향). `accept-gate-scc-context-changed`는 이제 §7과 같은 문서 — 설명만 역사로 갱신(`fixture_change`). `validation/`(G3)·`ledger/`(G2b)는 문장. 소유자 세션의 사고 기록: 치환 하나가 실패한 **절반 적용 파일로 `check-all`이 초록**을 낸 적이 있다 — 적용 스크립트는 전부 성공했을 때만 쓴다(cherry-pick -q 사고와 같은 부류). 남은 묶음 다섯: 6 쌍의 집합·방향, 7 한정 걷기, 8 Kotlin, 9 §7 잔여, 10 원장 경계. 닫힘 표시는 묶음들 뒤 한 PR.

**6/10 쌍의 집합·방향·순서(v3.10.5, D199–D202).** 첫 커밋은 예고대로 report 3·validate 2의 뿌리에서 32 케이스가 붉었고 스키마가 따라갔다: `duplicationPair` 두 수 + 불변식 if/then(한쪽 0 ⇔ 다른 쪽 0), `hiddenCoupling`에 `chg_commits_a/b` required, `validate`의 `before`/`after`가 `duplication_pair`면 `{a, b}` 객체. **배열 순서 린트**(`order_lint`, 파싱 후 — 표 D202-1의 키와 a < b; `swap` 패치로 변조 넷)가 섰고 **§7에서 둘을 잡았다**: `duplicate_clusters[0].occurrences`(OrderService 1200이 OldOrderService 4010 앞 — `(path, start_token) asc` 위반)와 `people.json`의 `teams`(payments가 other 앞 — `team asc` 위반). prd.md의 자리라 코드에서 채우지 않았고 **소유자가 같은 판 안에서 보정했다**(§0-44 보정 — 표 `D202-1`을 적은 판이 자기 예시에서 그 표를 어기고 있었다: '초록은 이행의 증거가 아니다'의 실물이 판 안에서 나왔다). 보정 뒤 `order_violations`가 §7 블록 여덟 전부에서 0이고 order 케이스 여섯이 섰다 — 긍정 셋은 처음 쓰였고 변조 셋은 위반이 3 → 1로 줄었다(`fixture_change`, #50의 8 → 1과 같은 모양). `files` 인덱스 뒤집힘은 `rejected_at`만 받는 대신 **패치 인덱스를 0 ↔ 1로** 바꿔 케이스의 뜻을 보존했다(`fixture_change`). cpd: `a_dup_tokens`·`b_dup_tokens`, `rename-swaps-sides`(B → `0B.java`면 100·200 ↔ 200·100 — 옛 한 수는 200 → 100으로 움직였다), 한쪽 0 입력은 멈춤(bite). history: 행에 분모, `generated-test-stub-not-in-pairs`(대칭 배제). reproducibility: 섞은 삽입 순서 → 같은 바이트, 정렬 규칙 없으면 다름. 남은 묶음 넷: 7 한정 걷기, 8 Kotlin, 9 §7 잔여, 10 원장 경계.

**7/10 한정 걷기(v3.10.6, D203–D205).** 첫 커밋 초록 — §7 불변. **계산기가 창 밖을 걷지 않았다**(§0-45)는 관찰이 이 묶음의 무게였고, 걷기가 처음 들어갔다: `contract/tools/historywalk.py`(프런티어 → 모든 조상·머지 통과 → 경로마다 첫 접촉에서 멈춤 → 지배되지 않는 접촉 중 커미터 시각 최대·SHA 동률; 어느 한 경로에서든 접촉 전에 graft에 닿으면 `age_unknown`). `history/` 넷: `window-outside-last-commit-recovered`(400.00 — §7의 1250 모양), `frontier-walk-dag`(O3-4 — F1·G1이 지배되지 않는 접촉, G1이 마지막; '시작점 하나의 조상만' 변조는 m0을 낸다), `deep-shallow-equals-full`(깊이 5 = full·`history_complete: true`, 깊이 3은 C만 null), shallow 불변식 셋. 기존 21의 값은 불변이고 맵·완전성·`walk`가 인쇄된다(`fixture_change`). **계산기의 구멍 셋째**: `last_commit_map_sha256`이 id 스펙에 없었다(§2.8 (i)·D146) — `deep-shallow-same-id`가 드러냈고(맵이 id에 없으면 얕은 shallow도 full과 같은 id) 스펙에 넣어 재현성 id 전부가 움직였다. **§2.8 (i) ↔ id 스펙 자기 반례**(`--selftest`, (i)의 이름 21 ↔ 스펙 키 17의 대응표)가 `check-all`에 들어갔다 — 첫 정규식이 숫자 든 이름 둘을 빠뜨린 것을 자기 반례가 잡았다. 남은 묶음 셋: 8 Kotlin(§7 H `n_ranked` 212가 바뀌는 유일한 묶음), 9 §7 잔여, 10 원장 경계.

**8/10 Kotlin(v3.10.7, D206–D209) — §7의 값이 바뀐 둘째 판, 렌즈 백분위가 바뀐 첫 판.** H의 `n_ranked` 212 → 194 + `n_population` 212, `lens_pct` 0.9289 → 0.9275(180/194 — 212는 다시 계산할 수 없는 n이었다, B.4). **D207이 가장 무거웠다**: 초안의 '들여쓰기는 자(尺)이지 증인이 아니다'를 소유자가 고르지 않았다 — 함수 경계와 주석 제거는 파서이고 토크나이저라 넷째 엔진을 텍스트 집계라 부른 것(B.1). Kotlin의 `cx`·`loc`·`smells`는 미지원 null(`unsupported_language` — 사전에), Kotlin은 Dx·순환·숨은 결합·이력만; `cx_method`는 `cyclo` 하나(들여쓰기는 어느 D도 세운 적 없는 본문 문장이라 취소선 없이 지움). 스키마: `lang: kotlin` → 셋 const null(if/then, 변조 `cx: 0`), `cx_method` enum `[cyclo]`(변조 `indent`), 긍정 `accept-report-kotlin-file`(append 패치 — §7에 Kotlin 파일이 없어 첫 커밋이 초록이었다); `gate` 새 P1 행에 `files_examined`·`files_unmeasured` required(D208, 변조 1); `change` `items` **일곱째 키 `smell_delta`**(D209 — ~~D120~~; 밖 key O3-29를 닫는 결정; `unmeasured` ⇔ 한쪽 null의 if/then, 변조 셋). 첫 커밋은 gate 두 정수에서만 붉었고 `change`의 일곱째 키는 §7에 예시가 없어 `base/change.json`에서 — 구현 PR에서 — 붉었다(§0-40 T7 잔여의 자리). 남은 묶음 둘: 9 §7 잔여(남은 key가 비었을 가능성 — 초안에서 센다), 10 원장 경계.

**9a 범위 정의(v3.10.8, D210–D212).** 첫 커밋은 예고된 둘에서 붉었다 — `reproduce`·`bytecode_scope` 닫힘, 그리고 **§2.8 (i) ↔ 스펙 자기 반례가 `source_scope → 표에 없다`로 처음 실측됐다**(#55에서 넣은 이유). 스키마: `source_scope`(required·닫힘·`origin` enum, convention이면 `generated_roots: []`·main 둘뿐의 if/then), `bytecode_scope.unmapped_classes`; 긍정 1(convention) + 변조 3. 재현성: id 스펙에 `source_scope` — **이번 id 이동은 `contract_change`**(앞의 셋은 계산기의 구멍 `bug_fix`); `same-tree-different-origin`(build·convention은 적격 목록이 같아도 id가 다르다 — 범위 자체가 입력; cli 덮어쓰기는 목록을 바꾼다; 블록을 스펙에서 빼면 id 충돌). `graph/generated-source-excluded-by-propagation`(D211 — `@Generated` 최상위 타입과 그 중첩·람다가 바깥 타입으로 접혀 함께 밖, 소스 없는 클래스는 `unmapped_classes: 1`). 남은 것: 9b(F3-15·F3-6·S3-19) → 9c(정정 다섯 + O3-16 `닫힘 — D187`) → 9d(T4·T10) → 닫힘 표시 PR → 10/10 G3 목록 PR → 4차 입력 설계. 메모리: `change.schema.json` `items`의 `required`(소유자 probe)는 다음 스키마 PR에.

**9b finding 선정·단위·빈 모집단(v3.10.9, D213–D215).** 첫 커밋은 예고된 둘(report `findings/4`의 `pair`, gate `checks/2`의 `eligible_n`)에서 붉었다. 스키마: `finding.pair`(kind `hidden_coupling`이면 required, 아니면 금지 — D191의 if/then에 한 가지), gate 핫스팟 행에 `eligible_n` required, `change` `anchor_class` 열거 `high`·`medium`·null — **`low`는 죽은 어휘였다**(선정 규칙 `lens_pct ≥ 0.75`를 적지 않았기 때문에 enum에 살아 있었다; `change-unknown-anchor-class`를 `low`로 재조준 — 어제까지 통과하던 값이 거부되는 것이 D213의 증거, `fixture_change`). **미룬 스키마 보정 둘을 같은 PR에서 닫았다**(소유자 probe): `change` `items`의 `required`(여섯 — `remediation_effect`만 선택; 변조 `change-items-without-smell-delta`), `report` `bytecode_scope`의 `required`(여섯 전부; 변조 `report-bytecode-scope-without-unmapped-classes`) — 그리고 `window_applied`도 같은 모양이라 아홉 필드를 `required`로(`history_complete`·`graft_boundary_shas` 포함; §7은 전부 갖고 있어 붉지 않았다). 남은 것: 9c(정정 다섯 + O3-16 `닫힘 — D187`) → 9d(T4·T10) → 닫힘 표시 PR → 10/10 G3 목록 PR → 4차 입력 설계.

**남은 것은 열린 발견이다.** O14가 D151·D152로 닫히고 `g0-review.py --count`가 서면서 이 수는 **사람 보고가 아니라 계산**이 됐다. 지금 출력:

```
    G0 #1 열린 발견 — 기록에서 센 수 (D140·D151·D152)
      읽은 종합: 2026-09-11-종합-서브에이전트-사전검토.md, 2026-09-14-종합-2차-다중모델-패널.md
      범위 안 `dedupe_key`  총 30
        닫힘  30 — D111, D126, D146, D147, D148, D149, D150, D154, D155, D156, D157, D158, D159, D160, D161, D162, D164, D165, D166, D167, D168, D169, D170, D171, D172, D173, D174, D175, D176, D177, D178
        열림  40
      범위 밖 (G3 목록으로) 총 16 — 닫힘 0 · 열림 16 — 안의 수에 더하지 않는다(D152·D153)
      **닫힘 표시는 기록에서만 읽는다** — `닫힘 — D<n>`이 적힌 key만 닫힌 것으로 센다.
      `prd.md`를 읽어 추측하지 않는다. 표시가 없으면 열린 것이다.
      보고 — 세지 않았거나 어긋난 것:
        [쪼갬] 2026-09-11-종합-서브에이전트-사전검토.md: 15 — 10과 같은 개별(R1-7). 한 key로 접는다
        2                            §2.1 §2.7 §2.8 §2.9 §4.3
        3                            §2.5 §3.3 §3.7
        4                            §2.1 §2.6 §5.2 §5.3
        5                            §2.7 §2.9 §7
        6                            §2.8 §4.5
        7                            §2.1 §2.4 §2.7 §2.8
        8                            §2.2 §2.4 §3.5
        9                            §2.1 §2.7 §2.9
        10+15                        §2.1 §2.2 §2.5 §3.3 §3.4
        11                           §2.6 §5.3 §6.3
        12                           §2.7 §5.5
        13                           §2.8 §7
        14                           §2.5 §3.7
        R2-5(미부착)                    §2.1 §2.6
        R1-5(미부착)                    §2.5 §3.6 §3.7 §7.1
        R1-9(미부착)                    §2.9 §3.5 §3.7
        R4-2(미부착)                    §2.7 §2.8 §2.9
        R4-3(미부착)                    §2.5 §3.6 §3.7
        R4-6(미부착)                    §2.1 §2.7
        N1                           §2.5 §3.3
        N3                           §2.8 §7
        N6                           §2.2 §5.3
        O-3(미부착)                     §2.5 §2.8
        O-4(미부착)                     §2.5 §3.7
        O-6(미부착)                     §2.2 §2.3
```

**총과 열린이 처음으로 갈렸다.** 닫힘 표시가 기록에 붙으면서 `열림 25 < 총 30`이 **계산**에서 나왔고, v3.9.0 뒤 `열림 19`, v3.9.1 뒤 `열림 16`, v3.9.3 뒤 `열림 12`, v3.9.4 뒤 `열림 5`가 됐다. 닫힌 스물다섯은 S1(D146–D150)·R2-3(D111)·N4(D148)·N7(D111·D126)·N8(D148)과 v3.9.0의 여섯 S5(D154)·S6(D159)·S13(D156)·R4-2(D157)·N3(D158)·O-3(D155)과 v3.9.1의 셋 S2(D160)·S9(D161)·R4-6(D162), v3.9.3의 넷 S7(D164)·S4(D165)·R2-5(D166)·R1-9(D167), v3.9.4의 일곱 N1(D168)·S3(D169)·S10+15(D170)·O-4(D171)·R1-5·R4-3(D172)·S14(D173)이고, 표마다 **근거 열**이 왜 그 D가 그 주장을 닫는지 적는다 — 계산기는 그 열을 읽지 않는다(표시의 유무만 본다). `prd.md`를 읽어 추측하지 않으므로 표시 없는 25는 열린 것이다.

계산기의 자기 반례는 아홉이다 — 닫힘/열림을 뒤집지 않는가, 걸친 것을 밖이라 하지 않는가(D152), 출처 없는 것을 세지 않는가, 쪼개진 것을 둘로 세지 않는가, **표의 절 집합이 개별과 다르면 어긋남을 내는가**, 실재하지 않는 개별을 가리키는 항목을 세지 않는가, **D 번호가 붙은 분리를 쪼갬으로 접지 않는가**(D153). 마지막 셋은 계산기가 **표가 아니라 개별을 정본으로 읽는다**는 것과 D153의 분리를 지킨다.

**2차가 들어왔다.** 27 = 1차 21 + 2차의 새것 6(N1·N3·N6 + 미부착 O-3·O-4·O-6). N2·N5는 범위 밖이라 세지 않고 G3 목록으로 간다. 2차 개별 열은 1차 key가 이미 낸 발견을 다시 낸 것이라 **1차 행의 출처로 흡수됐다** — 재발견은 수를 늘리지 않는다(D151의 dedupe가 그 자리다). N4는 소유자가 패널 밖에서 낸 것이라 개별 기록이 없어 "출처 없음"으로 보고되고 세지 않는다 — **패널 밖 발견이 셀 자리를 갖지 못한다**는 것은 남는 질문이다. 패널이 이미 두 번 돌았고 **둘 다 "통과시키지 않음"**이다.

| 패널 | 구성 | 결과 |
|---|---|---|
| 1차 | 동일 모델 서브에이전트 5 | 발견 **15건**, 5/5 통과시키지 않음 |
| 2차 | 실행 모델 넷 — Haiku·Sonnet·Opus·Fable | 각각 **1·4·9·5건**, 새 발견 4건 |

2차가 D141을 낳은 자료다. **Haiku는 쌍 1–8 전부 "모순 없음"**을 냈는데 그중 쌍 2는 1차가 만장일치로 모순이라 하고 shallow clone 실험으로 확인한 자리다(같은 트리·같은 창 안 커밋 목록인데 `age_last_days` 1100 vs 200) — 합의를 세면 실험으로 확인된 모순이 희석된다. 반대로 **Opus는 1차 5/5가 "모순 없음"으로 치운 쌍 1에서 모순**을 냈고(§2.5 `percentile_population`은 필드당 `population` 칸이 하나인데, 창 12개월·F 조건 `age ≥ 180`이라 200일 전에 바뀐 파일은 `active`이자 F 후보여서 `cx`에 `pct_active`와 `pct_all`이 둘 다 필요하다), **Sonnet·Fable은 독립적으로** §5.4 ↔ §5.5의 `anchor_class` 저장/파생 모순을 잡았다(1차 15건에 `anchor_class` 0건 — v3.7.1에서 D56에 "결정 산출물로 저장"을 넣으며 §5.5 파생 목록을 안 고친 것, 문서 규칙 2의 또 한 사례).

**패널 기록 열두 장이 리포에 있다** — 1차 일곱(리뷰어 5 · 종합 · 예시)과 2차 다섯(Haiku · Sonnet · Opus · Fable · 종합). D141이 "모델별 판정을 따로 적는다"를 계약으로 만들었고, 그 산출물이 이제 리포 안에 있다. 두 종합 모두 **개별 기록이 정본**임을 머리말에 적는다 — 종합이 원본을 덮는 것이 이 프로젝트가 경계해 온 실패다.

**`prd.md` §0-23·§0-24의 "측정 기록은 리포에 커밋되어 있지 않다"는 그 판 당시의 기록이다.** §0-21과 같은 부류로 보아 건드리지 않았다 — 이력을 사후에 고치지 않는다. 지금 상태는 이 문단이 진다.

기록은 `docs/review/records/`에 생기고 **리뷰어가 PR로 올린다** — 통과시키지 않은 판단과 모호로 남긴 쌍까지 같은 자리에 적는다(§9).

**다음 — 소유자의 결정이 먼저**: **O14의 정지 규칙**(열린 발견 0을 언제 0이라 할 수 있는가)과, 남은 발견들 중 무엇을 먼저 닫을지. 1차 종합이 "최소 넷은 먼저 닫혀야 한다"고 지목한 것(발견 1·2·3·5) 중 **발견 1은 v3.8.5(D146–D149)가 닫았고**, 그 판이 만든 §2.7의 근거 모순은 **v3.8.6(D150)이 닫았다**. 2차의 새것 중 `history_complete` ↔ `graft_boundary_shas`는 PR #20이 닫았다. 남은 것은 전부 **계약 결정**이다. 리뷰어를 더 붙여도 닫히지 않는다 — 오히려 늘어난다. 통과하면 계약 동결, 그 뒤 G1(§9 W4–7): core 측정·백분위·렌즈·JSON, CLI `scan`, `contract/lens`·`gate`, 자기 적용 S1(`docs/self/`에 첫 지도 보존).

**열린 공백**: O 항목 아홉과 PRD 공백을 패킷 §5에 모았다. 패킷이 "가장 위험한 하나"로 적었던 `analysis_input_id`의 **정규 인코딩**은 v3.8.3이 닫았다 — RFC 8785 JCS(D138), `contract/reproducibility/jcs-canonical-encoding`이 RFC 벡터로 못 박는다. "결정이 §10에만 적히고 본문이 안 따라온다"를 기계로 잡을 구조가 없던 것도 닫혔다 — 결정 항목이 바꾼 절을 대괄호로 들고(D139) `ci/check-decision-landing.sh`가 절 단위로 본다. `distinct_authors_90d` × `max_commits`는 D137이 닫았다. **새로 열린 것은 O14 — "열린 발견 0"의 정지 규칙**이다. D140의 조건은 그만 찾으면 0이 되므로(굿하트) 언제 "더 없다"고 말할 수 있는지가 필요하다. 결정 전까지 §12의 임시 읽기("마지막 라운드에서 **새로** 나온 것이 0")를 쓴다. 두 패널 모두 목록 **밖** 쌍이 목록 안보다 생산적이었으므로(1차 발견 2·6·8·10·11·12, 2차 새 넷 중 셋) 후보 (c) "라운드마다 쌍 목록을 바꾼다"가 핵심으로 보인다.

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

## 계약 표류 사고 — 2026-09-11 (§9: 자기 적용 결과가 나쁘면 그것도 기록한다)

**갈라진 것.** 리포의 `prd.md`가 **v3.8.0**인데 두 PR이 그 파일에 없는 계약을 구현했다.

| | main에 있던 것 | 세션이 계약으로 삼은 것 |
|---|---|---|
| `prd.md` 첫 줄 | v3.8.0 | v3.8.2 |
| D134·D135·D136·D137 | **없음** | 있음 |
| §0-20·§0-21 | **없음** | 있음 |

PR #9는 D134(§2.4 파일 쌍)·D135(§2.1 저자 사실)를, PR #10은 D137(90일 ∩ 창)을 구현했다. **둘 다 리포의 진실에 근거가 없었다** — CLAUDE.md §2의 "`prd.md`가 진실이다"가 두 PR 동안 깨져 있었다.

**왜 안 보였나.** `prd.md`가 **main에 대한 커밋되지 않은 작업트리 수정**으로 있었다. `git checkout`은 충돌이 없으면 미커밋 수정을 브랜치 간에 그대로 옮긴다. 그래서 `git checkout main && git pull` 뒤의 `head -1 prd.md`가 **언제나 v3.8.2**를 냈다 — 커밋된 파일이 아니라 그 수정을 읽은 것이다. `main = v3.8.2`라는 보고는 `git rev-parse HEAD`(main의 SHA)와 작업트리 파일을 한 줄에 묶은 출력이었고, **둘이 어긋난 것을 보여 주는 출력이 없었다.** 브랜치 둘 다 `prd.md` 커밋 0건.

**어떻게 알았나.** 기계가 아니라 소유자가 찾았다. 세션이 "§0-21·D137은 있는데 §2.1·§2.7에 ∩ W가 없다 — 새 dangling reference"라고 보고했고, 소유자가 그 셋을 리포에서 찾다가 **셋 다 없는 것**을 봤다. 그 보고는 리포에 대해 거짓이었다(있는 파일은 작업트리의 미커밋본이었다). 자기 적용이 이것을 못 잡은 이유는 단순하다 — **`prd.md`가 리포의 것인지 검사하는 자리가 없었다.**

**닫은 것.** CLAUDE.md §6에 한 줄: 인용한 D 번호가 전부 **리포의** `prd.md`에 있는가(`git show main:prd.md | grep -c '^- D<n>'`). 작업트리가 아니라 `main:` 경로로 읽는 것이 요점이다.

**스위트는 처음부터 잡을 힘이 있었다.** `contract/schema/`는 `prd.md`의 §7 예시를 꺼내 `schemas/`로 검증한다 — v3.8.2를 커밋하자마자 `accept-report`가 실패했다(예시에 생긴 `authors_window_truncated`가 스키마에 없었다). 두 PR 동안 조용했던 이유는 검사가 약해서가 아니라 **CI가 언제나 v3.8.0을 읽었고 그것은 자기 스키마와 맞았기 때문**이다. **검사가 볼 수 있는 자리에 계약을 놓는 것이 검사보다 앞선다.**

**새 검사가 못 잡는 것.** §6의 한 줄은 "D 번호가 `prd.md`에 있는가"를 본다. **결정은 §10에 적혔는데 본문이 안 따라온 경우는 잡지 못한다** — 이 프로젝트의 반복 실패 모드(문서 규칙 2)이고 이번에도 같이 일어났다. v3.8.2의 첫 판은 D137이 §10에 있는데 §2.1·§2.7에 `∩ W`가 없었고, 그 확인이 `'90일 ∩ 창'` **부분 문자열**로 이뤄져 §5.5의 `change_exposure_90d` 괄호에서 맞아 거짓 통과했다. **그 판은 main 이력에 없다** — PR #11의 첫 커밋(`3e5ba85`)을 머지 전에 amend해서 `e072c33`으로 다시 쌓았고, main에 닿은 v3.8.2는 처음부터 `∩ W`를 가진 판이다. 이 문단을 git 이력과 대조하면 찾을 수 없다는 뜻이라 여기 적는다 — 기록의 정확성을 다루는 문서가 자기 기록으로 재현되지 않는 것은 같은 실패의 축소판이다. 본문 문장의 유무는 **절 단위로** 봐야 한다(`awk '/^### 2\.1 /,/^### 2\.2 /'`) — 파일 전체 `grep`은 다른 절의 우연한 일치를 통과로 셴다. **절 단위 검사 자체도 틀릴 수 있다**: awk 범위 패턴은 시작 줄이 종료 패턴에도 맞으면 그 한 줄에서 끝나므로, `awk '/^### 2\.7 /,/^### [0-9]+\.[0-9]+ /'`처럼 종료를 일반형으로 쓰면 **언제나 0건**을 낸다 — 있는 문장을 없다고 보고한다. 이 세션의 확인 스크립트가 실제로 그랬고, 같이 돌린 다른 검사가 옳아서 결론만 맞았다. 종료 패턴은 시작을 배제해야 한다(위처럼 `2.2`로 고정하거나, 시작 줄 다음부터 세는 추출기를 쓴다). 기계로 닫으려면 "D가 §10에 있으면 그 D가 지목한 절에도 있는가"를 검사해야 하는데, 결정이 어느 절을 바꾸는지는 지금 구조화돼 있지 않다(§10 항목이 절 번호를 자유 텍스트로 부른다). **PRD 공백으로 표시한다.**

**남는 것 — 이 사고가 이력에 남긴 사실.**

- v3.8.1은 **자기 커밋을 갖지 못했다.** 파일이 v3.8.2에 덮여 재구성할 수 없었고, 중간 상태를 지어내는 것은 B.4가 막는다. `prd.md` 이력은 v3.8.0 → v3.8.2로 건너뛴다(PR #11).
- PR #9·#10의 커밋 시각이 계약(PR #11)보다 **앞선다.** 머지 순서를 #11 → #10으로 해서 머지 이력에서는 계약이 앞서게 했지만, 커밋 시각은 고칠 수 없다.
- `50cc5e8 docs(prd): §0-19 v3.8.0`은 세션이 쓴 커밋인데 `Co-authored-by: Claude` 트레일러가 없다. `declared_ai_assistance`의 **과소 선언**이다(§5.1·D48). main 이력은 재작성하지 않으므로(위 §이력 재작성 기록) 그대로 두고 여기 적는다 — S1에서 이 리포를 스캔할 때 이 커밋은 사람 단독으로 읽힌다.
