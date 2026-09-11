# `contract/` — 적합성 스위트 (§2.9)

> 계약과 픽스처가 먼저다. 구현은 그 설명이다.
> v3.1·v3.2의 산술 오류와 v3.3의 계약 충돌이 이 순서의 이유다(§0-3·§0-4).

## 이 디렉터리가 고정하는 것

`contract/<계약>/<케이스>/`는 **하나의 계약 문장이 실제로 무엇을 뜻하는지**를 실행 가능한 형태로 못 박는다.
계약 문장은 사람이 읽고, 픽스처는 기계가 읽는다. 둘이 어긋나면 **문서를 고치는 PR이 먼저**다(CLAUDE.md §2).

각 케이스는 다음을 갖는다:

| 파일 | 뜻 |
|---|---|
| `input.json` 또는 합성 리포(트리 + 스크립트 생성 git 이력) | 계약의 **전제** — 손으로 쓴다 |
| `expected.json` | 계약의 **결론** — 손으로 쓰지 않는다. 계산 스크립트가 만든다 |
| 계산 스크립트 (`compute.py` 등) | `input` → `expected`의 재계산 경로. 함께 커밋한다 |

**케이스 모양은 계약에 따라 다르다**(§2.9). `percentile/`·`cpd/`·`graph/`·`schema/`는 순수 수치·구조 계약이라 `input.json` 하나로 전제가 완결된다. `history/`·`ledger/`·`gate/`·`reproducibility/`는 이력 자체가 입력이라 합성 리포(트리 + **스크립트가 결정적으로 만드는** 이력)가 있어야 한다 — `reproducibility/`가 그런 이유는 `analysis_input_id`의 입력에 창 안 커밋 SHA 목록과 `window_anchor`가 들어가기 때문이다(§2.8).

## 하드룰

- **`expected.json`을 손으로 고치지 않는다.** 기대값을 바꾸는 커밋은 `fixture_change` 레코드를 반드시 동반한다(§2.9 끝, P11) — [`fixture-changes/`](fixture-changes/)에 파일 하나, 스키마는 [`schemas/fixture_change.schema.json`](../schemas/fixture_change.schema.json). 원인 분류 없이는 머지 불가 — 회귀 테스트가 "새 정답을 손으로 승인하는 테스트"로 변질되는 것을 막는 장치다.
- **산술은 정확 유리수**(§2.5 산술 계약, D115·D121). 파생은 전정밀에서, 반올림은 마지막에 한 번. IEEE-754 `double`은 §2.5의 픽스처 예 `18.1`조차 재현하지 못한다.
- **숫자는 계산에서 나온다.** 예시조차 픽스처다(B.4, D26).
- 실패 메시지는 **어느 계약(§n)이 깨졌는지** 말해야 한다(CLAUDE.md §4).

## 디렉터리와 게이트 (§2.9 표)

| 디렉터리 | 무엇을 고정하나 | 게이트 | 현재 |
|---|---|---|---|
| [`percentile/`](percentile/) | §2.5 성분·렌즈 백분위, type-7 분위, §3.7 confidence | **G0** | 6/9 케이스 |
| [`schema/`](schema/) | §7 스키마 7종 × 긍정 1 + 하드룰 변조 ≥ 1(D124) | **G0** | **45 케이스** |
| [`reproducibility/`](reproducibility/) | §2.8 정체성 셋의 분리와 `reproduce` 완전성(D111) | **G0** | 1/5 케이스 |
| [`cpd/`](cpd/) | §2.6 클러스터·합집합·쌍 투영 | **G0** | **5 케이스** |
| [`history/`](history/) | §2.7 앵커·창·rename, 그리고 blame 금지의 강제(D113) | **G0** | **10 케이스** |
| [`graph/`](graph/) | §2.2–2.3 컴포넌트 그래프·Lakos 검산, P8 합성 리포 | **G0** | **8 케이스** |
| [`lens/`](lens/) | §3 렌즈 조립과 null 전파 | G1 | 스켈레톤 |
| [`gate/`](gate/) | §5.2–5.3 BASE 자격 고정·발생 수준 새 중복 | G1 | 스켈레톤 |
| [`renderer/`](renderer/) | §7.1 렌더러가 JSON의 순수 함수임(D28·D67) | G2 | 스켈레톤 |
| [`ledger/`](ledger/) | §5.4–5.5 전이 모델·귀속·정체성 | G2b | 스켈레톤 |
| [`validation/`](validation/) | §6.3 합격 함수·검증 입력 정체성 | G3 | 스켈레톤 |
| [`security/`](security/) | §6.6 L2 샌드박스 벡터(P9) | G3 | 스켈레톤 |

"스켈레톤"은 **README만 있고 케이스가 없다**는 뜻이다 — 게이트가 오기 전에 케이스를 박는 것이 이 디렉터리의 일이다.

## 공유 자원

- [`judgment-vocabulary.json`](judgment-vocabulary.json) — 판정 어휘 사전. **한 곳에만 있고** `schema/`(G0, JSON 층)와 `renderer/`(G2, HTML 층)가 같은 것을 읽는다(D127).
- [`fixture-changes/`](fixture-changes/) — `expected.json`을 바꾼 이유(D129).
- [`tools/exact.py`](tools/exact.py) — **계약이 아니다.** 계산기들이 공유하는 정확 산술과 결정적 직렬화(§2.5·D115·D121). 직렬화가 갈리면 같은 값이 다른 바이트가 되고 "두 머신 바이트 동일"이 계산기마다 다른 뜻이 된다. 계산기 전부가 이것을 쓴다.

## 실행

```sh
python3 contract/percentile/compute.py       --check
python3 contract/schema/compute.py           --check
python3 contract/reproducibility/compute.py  --check
```

`--check` 없이 부르면 `expected.json`을 재생성한다. 재생성이 값을 바꾸면 `fixture-changes/`에 레코드를 같은 커밋에 넣어야 한다(§2.9, D129).

G0 이후 이 스위트는 `jqradar-core`의 파라미터화 테스트가 돈다(CLAUDE.md §4). 지금은 스크립트가 그 자리를 대신한다.
