# `reproducibility/` — 식별자·환경 계약 (§2.8) · 게이트 **G0**

## 이 계약이 고정하는 것

**"같다"가 세 가지 다른 뜻을 갖는다는 것**(§2.8, D86).

| 정체성 | 무엇이 같으면 같은가 | 쓰임 |
|---|---|---|
| `repository_state_id` | 트리(정렬된 `(path, content_id)` 전체의 sha256) | 캠페인 앵커의 봉인(§5.4, D112) |
| `analysis_input_id` | 트리 **+ 툴체인 + 계약 버전 + 파라미터** | 캐시 키 |
| `validated_tree_id` | 검증이 실제로 돈 트리 | 검증의 증거 결속(§6.3 5a, D89) |

그리고 두 원칙을 실행 가능하게 만든다(B.4):
- **포함되지 않은 입력은 결과에 영향을 주어서는 안 된다.** 환경변수 하나에 숫자가 흔들리면 캐시가 거짓말을 한다.
- **포함된 모든 입력은 `reproduce`에 값 또는 해시로 나타나야 한다**(D111).

## 케이스 모양 — 합성 리포다

§2.9가 이 계약을 합성 리포 쪽에 둔 이유: `analysis_input_id`의 입력에 **창 안 커밋 SHA 목록**과 `window_anchor`(HEAD 커미터 시각)가 들어간다(§2.8). 트리만으로는 전제가 닫히지 않는다.

```
<케이스>/tree/          커밋되는 소스 트리
<케이스>/input.json     이력 명세(커미터·고정 시각·커밋별 경로) + 두 실행의 툴체인
<케이스>/expected.json   compute.py가 만든다
```

이력은 `compute.py`가 임시 디렉터리에 **결정적으로** 만든다 — 커미터 이름·메일·시각을 고정하므로 커밋 SHA가 언제나 같다. `.git`은 커밋하지 않는다.

## 최소 케이스 (§2.9)

| 케이스 | 무엇을 잡나 | 상태 |
|---|---|---|
| 같은 트리·다른 PMD 버전 | `analysis_input_id` **다름** ∧ `repository_state_id` **같음**. 툴체인이 키에서 빠지면 PMD 7.16과 7.17이 같은 키를 만든다 | [`same-tree-different-pmd/`](same-tree-different-pmd/) ✅ |
| `reproduce`에 없는 환경변수 변경 | 결과 **불변**(원칙 검사, D87) | 위 케이스가 `irrelevant_environment_change`로 함께 검사 ✅ |
| 파라미터 하나 변경 | `cpd.minimum_tokens` 100→120에 `analysis_input_id` **변경** ∧ `repository_state_id` 불변. 그리고 **캐시 키는 사영**(D159): 그 파라미터를 읽는 측정(`pair_dup_tokens`)만 미스, 읽지 않는 측정(`cx`)은 적중. 키에서 파라미터를 빼면 거짓 적중이 나는 것(검사가 무는가)과 §2.8 밖 입력이 키에 들어오면 거부되는 것도 같이 본다 | [`parameter-change-cache-projection/`](parameter-change-cache-projection/) ✅ |
| `reproduce`만으로 id 재계산 | 인쇄된 값·해시만으로 `analysis_input_id`를 다시 만들어 대조(D111) | 미작성 |
| 두 머신 바이트 동일 | **비교 대상의 정의**(D154) = `reproduce.scanned_at`·`reproduce.classes_reproduction_inputs`를 뺀 전부. 두 머신의 산출물이 그 규칙으로 JCS 바이트 동일 ∧ 제외 필드는 **실제로 다름** ∧ 제외 필드는 id 입력에 없음 ∧ 넷째 종류 필드(머신 이름)를 심으면 잡힘(D158) | [`byte-identity-comparison-target/`](byte-identity-comparison-target/) ✅ — 실제 두 머신에서의 실행은 G1(측정 코드)부터 |
| 도달 불가 커밋이 새지 않는다 | 버려진 브랜치를 더해도 `head`·`repository_state_id`·`analysis_input_id` **셋 다 같고** 도달 불가 개수만 다르다. 구현이 `git log --all`로 이력을 읽으면 값은 갈리는데 id는 같아서 재현성 주장이 조용히 샌다 | [`unreachable-commits-do-not-leak/`](unreachable-commits-do-not-leak/) ✅ |
| 시각 표기 | 같은 unix 초를 `Z`·`+00:00`·`+09:00`·`-07:00`으로 적은 넷이 정규 표기(`YYYY-MM-DDTHH:MM:SSZ`, D157)로 **같은 바이트·같은 id**. 먼저 날것 넷이 **네 id**를 내는 것을 보인다(JCS는 문자열 안을 안 건드린다). 파이썬 `isoformat()`(`+00:00`)이 패턴에 실패하는 것도 단언 — 이 계산기가 v3.9.0 전까지 정확히 그 자리에 있었다 | [`time-notation-canonical/`](time-notation-canonical/) ✅ |
| `people.attribution` 토글 | 같은 트리·이력·툴체인을 `off`와 `team`으로 → `analysis_input_id` **변경** ∧ `repository_state_id` 불변(D160). `off`에서도 `people`이 해시에 들어간다. 사영: `team_count` 키만 미스, `cx`·`pair_dup_tokens` 적중 | [`attribution-toggle-changes-id/`](attribution-toggle-changes-id/) ✅ |
| 매핑 한 줄 수정 | 둘 다 `team`, 팀 매핑 파일 한 줄만 다름 → `team_mapping_sha256`이 바뀌어 id 변경, `team_count` 키만 미스(D160·D159). 키에서 매핑 해시를 빼면 **거짓 적중**이 나는 것(검사가 무는가)도 단언 | [`team-mapping-edit-cache-projection/`](team-mapping-edit-cache-projection/) ✅ |
| full clone vs `--depth 3` shallow clone | 같은 트리·같은 창 안 커밋 목록 → `last_commit_map_sha256`이 달라 id 다름 ∧ shallow는 `age_unknown` ∧ `history_complete: false`(D146·D148·D149) | 미작성 |
| 정규 인코딩 = RFC 8785 JCS | RFC 벡터를 **같은 바이트로** 내는가. 순진한 sorted-key JSON이 그 벡터에서 **갈리는가**(검사가 무는가). id 입력 영역에서는 둘이 바이트 동일한가. float를 **거부**하는가 | [`jcs-canonical-encoding/`](jcs-canonical-encoding/) ✅ |

창 밖 커밋과 id의 관계는 **두 계약이 절반씩** 진다. 여기(`unreachable-commits-do-not-leak`)는 **id가 같아야 하는 쪽** — 도달 불가 커밋은 창의 입력이 아니므로 세 id가 전부 불변이다. `history/authors-window-truncated-by-count`는 **값이 달라지는 쪽** — 창 상한이 90일 구간을 자르면 `distinct_authors_90d`가 달라진다. 창 밖만 다른 두 리포로는 전자를 만들 수 없다: 커밋 SHA가 조상을 물고 가서 `commit_list_sha256`이 갈리고 `analysis_input_id`가 구조적으로 달라진다(실험으로 확인). 버려진 브랜치는 HEAD의 조상이 아니라서 그 자리가 성립한다.

D128에 따라 **해시 형식(`pattern`)의 강제도 이 디렉터리가 진다** — §7 예시가 자리표시자를 쓰므로 스키마에 형식을 걸 수 없고, G1에 예시가 픽스처에서 생성되기 전까지는 여기가 그 자리다. 아직 미작성.

## 결정 — 정규 인코딩은 RFC 8785 JCS (D138)

해시는 **바이트**에 대한 것이므로 입력을 바이트로 펴는 방법이 계약이어야 한다. 이전 판은 §2.8이 입력 **목록**만 정했고, 이 계산기가 `sorted-key compact UTF-8 JSON, separators=(',',':')`를 자기 주석에 **선언하고** 썼다 — 계약이 아니라 구현의 사정이었다. v3.8.3이 §2.8에 `RFC8785-JCS`를 넣어 닫았다(D138).

`contract/tools/jcs.py`가 그 구현이고 `jcs-canonical-encoding/`이 계약이다. 세 가지를 같이 본다 — 일치만 보이는 검사는 아무것도 증명하지 않는다(D131):

1. **RFC 벡터를 재현하는가.** §3.2.3의 속성 정렬 예와 §3의 문자열 이스케이프 예를 바이트 그대로 낸다.
2. **순진한 인코딩이 그 벡터에서 갈리는가.** 파이썬 `json.dumps(sort_keys=True)`는 **코드포인트**로 정렬하고 JCS는 **UTF-16 코드 유닛**으로 정렬한다. 😀(U+1F600)은 UTF-16에서 대리쌍 `D83D DE00`이라 דּ(U+FB33)보다 **앞선다** — 코드포인트 순서와 반대다. 그래서 `naive_sorted_key_fails_rfc_vector`가 참이다. 이 단언이 없으면 "JCS를 쓴다"는 주장이 검사되지 않는다.
3. **id 입력 영역에서는 둘이 바이트 동일한가.** 지금 `analysis_input_id`가 먹는 것은 ASCII 키·정수·문자열뿐이라 두 인코딩이 같은 바이트를 낸다. 그래서 이 전환에서 `same-tree-different-pmd`와 `unreachable-commits-do-not-leak`의 **해시가 하나도 움직이지 않았다** — 재계산 diff가 `canonical_encoding` 줄 둘뿐이다. `fixture_change`가 그 사실을 진다.

**부동소수점은 거부한다.** D138이 id 입력에 두지 않기로 했고(분수 파라미터는 십진 문자열 `"0.8"`), 금지를 산문이 아니라 구조로 막는다(D126) — `jcs.dumps`가 `FloatInCanonicalInput`을 던진다. RFC 8785 §3의 `numbers` 벡터를 **거부하는** 케이스를 같이 두었다: JCS 자체는 ES6 직렬화로 받지만 우리는 좁힌 것이고, 나중에 누가 float 지원을 "고쳐 넣는" 것을 그 케이스가 막는다.

남는 미작성은 위 표의 둘(`reproduce`만으로 재계산 · full vs shallow clone)과 D128의 해시 `pattern` 강제다.

## 결정 — 시각의 정규 표기 (D157)

`head_committer_time`은 `window_anchor.timestamp`로 id에 **해시로** 들어간다. PR #4에서 `%cI`가 UTC를 `Z`/`+00:00`으로 섞어 CI가 잡았고 계산기가 `%ct`로 바뀌었다 — 그런데 그 뒤의 `isoformat()`이 `+00:00`을 냈다. 표기가 계약이 아니어서 계산기가 제 사정대로 적은 것이고, 어느 머신의 어느 라이브러리가 어떻게 적느냐에 id가 걸려 있었다. v3.9.0이 §2.7에 표기를 정했다(D157): UTC · RFC 3339 · 초 · `Z` · 소수 초 없음, unix 초에서 생성. `canonical_time()`이 그 구현이고 `time-notation-canonical/`이 계약이다. 이 전환으로 `same-tree-different-pmd`·`unreachable-commits-do-not-leak`의 `analysis_input_id`가 움직였다 — `fixture-changes/2026-09-21-time-notation-d157.json`이 그 사실을 진다.

## 결정 — 저작 정책은 id 입력이다 (D160)

"정책이지 파라미터가 아니다"(§4.3, B.6)는 조직이 **어디에** 적는가의 분류이지 **무엇이 결과를 바꾸는가**의 분류가 아니다 — 교차 검토 S2가 리뷰어 다섯 전원 모순으로 지목했다. v3.9.1이 `people.attribution`과 팀 매핑 파일의 해시를 §2.8 입력에 넣고 `reproduce.people`로 인쇄하게 했다(off에서도 `{off, null}`). 계산기의 id 스펙에 `people`이 들어가 기존 다섯 케이스의 id가 움직였다 — `fixture-changes/2026-09-22-people-in-analysis-input-id.json`. 매핑 파일의 해시는 정체가 아니다(파일 하나의 해시, `policy_hash`와 같은 부류) — 픽스처의 매핑 내용은 가짜 이름이고 `expected.json`에는 해시와 줄 수만 남는다. `team_count`의 키(§4.5 셋째 예)는 저자 집합·attribution·매핑 해시·k인데, 저자 집합은 창 안 커밋 목록의 함수라 이 픽스처는 `commit_list_sha256`을 그 자리에 둔다.

## 결정 — 비교 대상과 캐시 키의 경계 (D154·D158·D159)

"두 머신 바이트 동일"은 **무엇을** 비교하는지가 정해져야 주장이 된다. D154가 정했다: `reproduce.scanned_at`·`reproduce.classes_reproduction_inputs`를 뺀 전부. 그 밖의 필드는 id 입력이거나 id 입력의 결정적 함수여야 하고 셋째 종류는 없다(D158) — `byte-identity-comparison-target/`이 넷째 종류(머신 이름)를 심어 규칙이 그것을 잡는 것을 보인다. 캐시 키는 `analysis_input_id`의 **사영**이다(D159): 어느 키에 있는 것은 §2.8에 있어야 하고 §2.8에 없는 것은 어느 키에도 없어야 한다 — `parameter-change-cache-projection/`이 양방향을 단언한다. PRD가 예로 든 사영은 `pair_dup_tokens` 하나(§4.5)이고, `cx`의 사영은 픽스처가 §2.1의 정의에서 읽어 선언한 것이다.
