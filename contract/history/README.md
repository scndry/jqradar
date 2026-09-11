# `history/` — 이력 계약 (§2.7) · 게이트 **G0**

## 이 계약이 고정하는 것

**시간의 기준점**, **무엇을 커밋으로 세는가**, **rename을 어떻게 잇는가**, 그리고 **blame을 부르지 않는다는 것**.

- **앵커 = `HEAD_TIME`**(HEAD 커밋의 커미터 시각). 같은 HEAD를 **언제 재도 같은 값**이 나와야 한다 — `scanned_at`은 감사 메타데이터일 뿐 계산에 들어가지 않는다(D25).
- **창 W** = `[HEAD_TIME − 12개월, HEAD_TIME]`의 **비머지** 커밋, 최신순 최대 2,000. 먼저 닥치는 상한을 적용하고 `bound_hit`에 적는다. **first-parent 한정이 아니다** — 머지되어 도달 가능한 브랜치 커밋도 세고 머지 커밋 자체만 뺀다.
- **rename** tie-break = 유사도 → 경로 편집 거리 → 사전순. 앞 둘이 동률이면 `rename_ambiguous`.
- **나이** = `HEAD_TIME − 마지막 비머지 커밋 시각`. 결정 불가·음수면 **null**(0이 아니다, D37).
- **blame 금지**(D18·D113). 예외는 캠페인 생성 1회뿐이다(§5.6·D57).

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

## blame 검사는 값이 아니라 부재를 본다

§2.9가 이 검사를 `ledger/`(G2b)에서 여기(G0)로 옮긴 이유: **강제 장치가 대상 코드보다 앞서야 한다.** G0에는 scan/change 코드가 없어 실제 스캔 대상이 0이고, 그 상태의 "통과"는 "검사하지 않았다"와 구별되지 않는다. 그래서 케이스가 **반례를 함께 선언한다**(`must_be_caught`) — 각 조각이 반드시 걸려야 하고, 하나라도 놓치면 `verdict: reject`다.

그 반례가 실제로 구멍을 찾았다: 처음 마커가 `git blame`(띄어쓰기 포함)이라 `new ProcessBuilder("git", "blame", "-p")`가 빠져나갔다. **자체 ArchUnit 규칙 2도 이것을 못 잡는다** — 타입 의존이 없어 바이트코드에 흔적이 없기 때문이다. 소스 검사와 바이트코드 검사는 겹치는 것이 아니라 서로 다른 구멍을 막는다.

## 실행

```sh
python3 contract/history/compute.py --check
```
