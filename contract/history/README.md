# `history/` — 이력 계약 (§2.7) · 게이트 **G0**

## 이 계약이 고정하는 것

**시간의 기준점**, **무엇을 커밋으로 세는가**, **rename을 어떻게 잇는가**, 그리고 **blame을 부르지 않는다는 것**.

- **앵커 = `HEAD_TIME`**(HEAD 커밋의 커미터 시각). 같은 HEAD를 **언제 재도 같은 값**이 나와야 한다 — `scanned_at`은 감사 메타데이터일 뿐 계산에 들어가지 않는다(D25).
- **창 W** = `[HEAD_TIME − 12개월, HEAD_TIME]`의 **비머지** 커밋, 최신순 최대 2,000. 먼저 닥치는 상한을 적용하고 `bound_hit`에 적는다. **first-parent 한정이 아니다** — 머지되어 도달 가능한 브랜치 커밋도 세고 머지 커밋 자체만 뺀다.
- **rename** tie-break = 유사도 → 경로 편집 거리 → 사전순. 앞 둘이 동률이면 `rename_ambiguous`.
- **나이** = `HEAD_TIME − 마지막 비머지 커밋 시각`. 결정 불가·음수면 **null**(0이 아니다, D37).
- **blame 금지**(D18·D113). 예외는 캠페인 생성 1회뿐이다(§5.6·D57).
- **파일 쌍**(§2.4·D134) — `shared` = 두 파일을 함께 만진 비머지 커밋 수, `tc = shared / min(chg_commits_a, chg_commits_b)`, 보고 기준 `shared ≥ 5 ∧ tc ≥ 0.5`. `static_dependency`는 **명세가 준다** — 그래프는 이 계약의 입력이 아니다(§2.2의 일이다).
- **저자 사실**(§2.1·D135) — `distinct_authors_90d`(최근 90일) · `ownership_max_share`·`minor_contributor_share`(W 안). **익명 집계만 기록한다.** 합성 리포의 저자는 고정 가짜 값이고 계산기는 그것을 메모리에서만 쓴다 — 정체는 `expected.json`에 들어가지 않는다(D48).

## 케이스 모양 — 합성 리포다

이력 자체가 입력이라 트리만으로 전제가 닫히지 않는다(§2.9). 트리는 커밋되고 **git 이력은 `compute.py`가 결정적으로 만든다** — 커미터 이름·메일·시각을 고정하므로 커밋 SHA가 언제나 같다. `.git`은 커밋하지 않는다.

**git에 판정을 위임하지 않는다.** 창 걸기·머지 제외·나이·rename tie-break는 §2.7의 규칙을 계산기가 직접 구현한다. git의 rename 휴리스틱을 그대로 쓰면 JGit과 다른 숫자가 나올 수 있고(§4.5·D17이 네이티브 백엔드를 옵트인으로 둔 이유), 그러면 픽스처가 계약이 아니라 특정 구현을 고정한다. git에서 읽는 것은 **사실**뿐이다: 커밋 SHA·부모·커미터 시각·변경 경로·추가/삭제 라인.

같은 이유로 **유사도는 케이스가 선언한다**. 케이스는 유사도가 설계상 명백한 모양(내용 동일 = 100)으로 만들어 그 값에 기대지 않는다.

## 최소 케이스 (§2.9)

| 케이스 | 무엇을 잡나 |
|---|---|
| [`anchor-fixed/`](anchor-fixed/) | 같은 HEAD를 다른 날 재도 같은 값. v3.2까지 이 기준점이 없었다(§0-4 #2) |
| [`merge-commits-excluded/`](merge-commits-excluded/) | 부모 ≥ 2는 세지 않는다. 브랜치 커밋은 센다 |
| [`window-bound-time/`](window-bound-time/) | 12개월 상한이 먼저 — `bound_hit: time` |
| [`window-bound-count/`](window-bound-count/) | 커밋 수 상한이 먼저 — `bound_hit: count` |
| [`coarse-granularity/`](coarse-granularity/) | 중앙값 > 20 → `coarse`. `chg_commits`의 confidence가 low로(§3.7) |
| [`rename-tiebreak/`](rename-tiebreak/) | 유사도 동률 → **경로 편집 거리**가 결정 |
| [`rename-ambiguous/`](rename-ambiguous/) | 앞 둘 다 동률 → 사전순이 결정하고 `rename_ambiguous` 표기 |
| [`shallow-clone-age-unknown/`](shallow-clone-age-unknown/) | graft 경계 커밋에서 읽은 나이는 **null**(D37) |
| [`negative-age-invalid-metadata/`](negative-age-invalid-metadata/) | 음수 나이 → null + `invalid_metadata`(0으로 자르지 않는다) |
| [`blame-forbidden-on-scan-change/`](blame-forbidden-on-scan-change/) | **D113** — scan·change 경로에 blame이 없다 |
| [`pair-report-threshold/`](pair-report-threshold/) | §2.4 보고 기준 `shared ≥ 5 ∧ tc ≥ 0.5`을 **양쪽에서** 밟는다. 세 쌍이 경계를 다르게 지난다 |
| [`tc-squash-vs-merge/`](tc-squash-vs-merge/) | 같은 작업을 두 이력으로 — `tc`가 **0.5와 1**. 판정은 없고 두 수다 |
| [`author-facts-minor-threshold/`](author-facts-minor-threshold/) | 마이너 기여자 `< 5%` 경계. 20커밋에서 0.05는 미만이 아니고, 21커밋에서 1/21은 미만이다 |
| [`identity-absent-when-attribution-off/`](identity-absent-when-attribution-off/) | **D48·D135** — 정체가 산출물에 없다. 모양이 아니라 **출처**로 가른다 |
| [`authors-window-truncated-by-count/`](authors-window-truncated-by-count/) | **D137** — 90일 지표를 창 안으로 자른다. 같은 이력을 두 창으로 봐 `distinct_authors_90d`가 1과 2로 갈린다 |
| [`team-folding-k-threshold/`](team-folding-k-threshold/) | **D161** — k 하한(≥3인)은 팀 집계의 조건. 3인 미만 팀은 `other`로 접혀 2인 팀 하나만 만진 파일은 `team_count: 1, teams_folded: 1` — 값은 있고 라벨은 없다. 정확히 3인 팀은 접히지 않는다 |
| [`off-closed-list-absence/`](off-closed-list-absence/) | **D162·D126** — off가 내는 저자 유래 필드는 셋으로 닫힌다(`team_count`는 필드 부재, 저자 사실은 어느 모드에도 없다). 부재 검사라 `must_be_caught` 5 + `must_not_be_caught` 4 — `distinct_authors_90d = 1`은 잡히면 안 된다 |
| [`shared-window-limited/`](shared-window-limited/) | **D164** — `shared`는 W 안. 같은 이력을 12개월·240개월 창으로 봐 `shared` 6 → 9, 두 창 모두 `tc ≤ 1`(불변식 인쇄). 근거는 일관성, 재현성이 아니다(D150) |
| [`hidden-coupling-sort-order/`](hidden-coupling-sort-order/) | **D167** — 정렬 키 넷을 하나씩 밟는 쌍 넷: (G,H) · (A,B) · (E,F) · (C,D). 정적 의존 있는 쌍은 `tc = 1`이어도 마지막, 동점은 `shared` 다음 `a` |

## blame 검사는 값이 아니라 부재를 본다

§2.9가 이 검사를 `ledger/`(G2b)에서 여기(G0)로 옮긴 이유: **강제 장치가 대상 코드보다 앞서야 한다.**

**주석과 문자열 리터럴을 가르는 것이 이 케이스의 핵심**이고, 그 결정과 근거는 [`blame-forbidden-on-scan-change/README.md`](blame-forbidden-on-scan-change/README.md)에 있다. 요약: 주석은 버리고 리터럴은 남기되, 리터럴은 **명령 조각 모양**일 때만 증거다. `--porcelain`은 `blame`과 연접할 때만 센다.

케이스가 `must_be_caught`(4)와 **`must_not_be_caught`(5)** 를 둘 다 선언한다 — `schema/`가 긍정과 변조를 둘 다 요구하는 것과 같다(D124). 전자는 규칙이 **무는지**, 후자는 **너무 물지 않는지**를 지킨다. 하나라도 어긋나면 `verdict: reject`.

둘 다 실제 구멍을 찾았다:
- `git blame`(띄어쓰기) 마커가 `new ProcessBuilder("git", "blame", "-p")`를 놓쳤다
- 넓힌 마커가 이번엔 `@DisplayName("어기면 잡는다 — git.blame()")`을 잡았다 — **이 리포에 있는 문장**이다

## 정체 부재는 출처로 가른다 (D135)

`identity-absent-when-attribution-off`가 §2.4·저자 사실 중 가장 까다로운 자리다.

산출물에는 `sha256:`이 **정당하게** 가득하다 — `repository_state_id`·`analysis_input_id`·`classes_id`·중복 클러스터의 토큰 해시·정책 해시. 저자 이메일의 sha256과 이것들은 **둘 다 64 hex라 문자열 모양으로 가를 방법이 없다.**

그래서 가르는 축을 구문에서 **출처**로 옮긴다. 합성 리포의 저자 식별자는 우리가 정했으므로 그 값들의 해시(sha256·sha1·md5 × 전체·접두 8·12·16자, 72개)를 미리 계산해 **그 특정 문자열이 산출물에 없음**을 본다. 무해한 해시를 무해하다고 증명할 필요 없이 **유해한 해시의 부재**를 증명하면 된다.

접두까지 보는 이유: **12자만 실어도 재식별에 충분하다.** §2.7이 "해시도 저장하지 않는다(재식별 가능)"고 적은 자리다.

금지 문자열 자체는 `expected.json`에 적지 않는다 — 적으면 그것이 정체의 사본이다. 개수와 판정만 기록한다.

부재 검사이므로 `must_be_caught`(2) + `must_not_be_caught`(3)를 함께 둔다(D131). 후자가 특히 중요하다: 모양으로 가르려 하면 정상 산출물의 `repository_state_id`가 오탐으로 걸린다.

## 90일 지표는 창 안으로 자른다 (D137)

§2.1의 `distinct_authors_90d`는 90일 고정이고 창은 12개월 ∧ 2,000커밋 중 먼저 닥치는 것이다. 커밋이 많은 리포에서 개수 상한이 90일보다 짧은 구간을 남기면 두 지표가 서로 다른 구간을 본다.

**답은 창을 넓히는 것이 아니라 90일을 자르는 것이다.** `[HEAD_TIME − 90d, HEAD_TIME] ∩ W`. 근거는 §2.8이다: `analysis_input_id`의 입력이 창 안 커밋 SHA 목록이므로, 창 밖 커밋이 값에 영향을 주면 **같은 id가 다른 값을 낸다** — D87이 막는 자리다. 넓히면 그 커밋들이 id에 들어가야 한다.

절단 사실은 **창의 속성**이라 `reproduce.window_applied`에 한 번만 적는다(`authors_window_truncated`·`authors_window_days`). 파일마다 적으면 "이 파일이 잘린 구간에 커밋을 가졌나"를 아는 것처럼 읽히는데, 그 커밋들이 창에서 사라져 판정하는 것이므로 **알 수 없다** — `closed_unclaimed`·`id_drift`가 지키는 선과 같다.

### 절단은 "창이 짧다"가 아니라 "상한이 잘랐다"다

10일 된 리포는 90일을 못 봤지만 **볼 것이 없었다.** 그것을 `truncated: true`로 적으면 "데이터를 잃었다"로 읽힌다. 판정은 존재로 한다 — 최근 90일 안의 비머지 커밋 중 **창이 제외한 것이 있는가**(`commits_excluded_within_90d`).

따라서 **시간 상한(12개월)은 90일 구간을 자를 수 없다**: 90일 ⊂ 12개월이므로 자를 수 있는 것은 개수 상한뿐이다. [`window-bound-time/`](window-bound-time/)이 그것을 반대쪽에서 보인다 — `bound_hit: time`인데 `truncated: false`다.

`authors_window_days`는 0에서 자른다. 커미터 시각이 뒤죽박죽이면 HEAD가 자기 조상보다 이를 수 있고(§2.1 `invalid_metadata`) 그때 음수 일수는 아무 뜻이 없다.

### 원칙의 다른 절반은 `reproducibility/`가 진다

이 계약은 **값의 독립성**(창 밖 커밋이 값을 움직이지 않는다)을 본다. 짝인 **id의 동일성**은 `max_commits`로 잘린 커밋으로 시험할 수 없다 — 커밋 SHA가 조상을 물고 가므로 창 밖이 달라지면 창 안 SHA도 달라지고 `commit_list_sha256`이 갈린다. 그래서 [`contract/reproducibility/unreachable-commits-do-not-leak/`](../reproducibility/unreachable-commits-do-not-leak/)이 **도달 불가 커밋**으로 양면을 한 번에 닫는다(HEAD SHA가 동일하므로 id도 값도 같아야 한다).

## 실행## 실행

```sh
python3 contract/history/compute.py --check
```
