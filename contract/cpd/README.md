# `cpd/` — CPD 집계 계약 (§2.6) · 게이트 **G0**

## 이 계약이 고정하는 것

**중복을 "쌍"이 아니라 "클러스터"로 센다**는 것과, 클러스터에서 파일·쌍 단위 숫자를 뽑는 **투영 규칙**. 공식이 아니라 투영이 논점이다 — 같은 CPD 출력에서도 어떻게 접느냐에 따라 Dx 순위가 통째로 달라진다.

- **중복 클러스터** = 같은 정규화 토큰 열의 **모든** 발생. A↔B와 C↔D가 같은 열이면 CPD가 이미 한 객체로 낸다(D39).
- **파일별** `union_dup_tokens` = 그 파일의 모든 발생 구간 **합집합**(겹침 병합).
- **쌍별** `pair_dup_tokens(A,B)` = A·B를 모두 포함하는 클러스터들의 **A쪽** 구간 합집합(A = 경로 사전순 앞).
- **자기 중복** = 발생이 한 파일에만 있는 클러스터. `self_dup_tokens`에 들어가고 **twin이 아니다**.

토큰 구간은 반개구간 `[start, end)`이고 길이는 `end − start`다.

## 케이스 모양

순수 수치 계약이라 `input.json` 하나로 전제가 완결된다(§2.9). 입력은 **CPD가 낸 것**(정규화 토큰 열의 발생 집합)이고, 출력은 §2.1이 쓰는 값들이다.

## 최소 케이스 (§2.9)

| 케이스 | 무엇을 잡나 |
|---|---|
| [`overlap-merge/`](overlap-merge/) | `[100,200) ∪ [150,250)` = **150**(250이 아니다). §2.6이 본문에 적은 예 |
| [`unordered-pair/`](unordered-pair/) | `pair(A,B) == pair(B,A)` — A쪽 투영으로 고정. 방향이 없으면 값이 둘이 된다 |
| [`self-duplication/`](self-duplication/) | 자기 중복은 `union_dup_tokens`에 들어가되 `twins`를 늘리지 않는다. twins=0이면 dx 모집단 밖(D29) |
| [`threshold-boundary/`](threshold-boundary/) | `minimumTokens=100`에서 99는 아니고 100은 맞다. 거부된 것도 기록한다 |
| [`four-occurrences-one-cluster/`](four-occurrences-one-cluster/) | 네 파일의 같은 열 = 클러스터 **1개**(쌍 6개가 아니다, D39) |
| [`mixed-cluster/`](mixed-cluster/) | **D166** — A 2회·B 1회 혼합 클러스터: `union(A) 200`·`pair(A,B) 200`·**`self(A) 0`**·`twins(A) 1`. 자기 중복은 한 파일에만 있는 클러스터의 것이다 — 혼합의 반복을 넣으면 두 번 셈 |

## 실행

```sh
python3 contract/cpd/compute.py --check
```
