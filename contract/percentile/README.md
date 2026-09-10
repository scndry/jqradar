# `percentile/` — 백분위·분위 계약 (§2.5, §3.7) · 게이트 **G0**

## 이 계약이 고정하는 것

**"상위 10%"가 무엇을 뜻하는지 한 가지로 못 박는다.** jQRadar의 모든 렌즈는 원값이 아니라 리포 내부 백분위 위에 서 있고(B.3), `interpretation`은 렌즈 백분위 하나만 본다(§3.7, D34). 그래서 순위·동점·작은 모집단·null의 처리가 흔들리면 지도 전체가 흔들린다.

고정하는 다섯 가지:

1. **성분 백분위** — 경험적 CDF, 동점 평균 순위, `pct(x) = (rank_avg(x) − 1)/(N − 1)`. 최소값 → 0, 최대값 → 1.
2. **모집단 셋** — `active`(H) / `dx`(Dx) / `all`(F), `cx`는 각 모집단 안에서 언어별. 그리고 **"값이 null"과 "모집단에서 제외"는 다른 상태**다 — `percentile_population.reason ∈ {not_in_active, no_twins, age_unknown, insufficient_population}`(D38).
3. **작은 모집단** — `N = 1 → null`, `N < percentile.min_population(20) → null`.
4. **분위(quantile)** — type-7 선형 보간(Hyndman–Fan). `h = 1 + q·(N − 1)`, `Q(q) = x_⌊h⌋ + (h − ⌊h⌋)·(x_⌊h⌋₊₁ − x_⌊h⌋)`.
5. **confidence** — `low ⇔ N < 50 ∨ IQR = 0 ∨ (median > 0 ∧ IQR < 0.25·median) ∨ (coarse ∧ 성분 = chg_commits)`; `high ⇔ N ≥ 200 ∧ low 조건 없음`; 그 외 `medium`. 렌즈 confidence = 기여 성분의 **최소**(D28). 기여 성분은 렌즈 식의 백분위 성분이다 — H: `cx`·`chg_commits`, Dx: `union_dup_tokens`·`active_twin_ratio`, F: `cx`·`fan_in`(나이 조건은 지시변수라 성분이 아니다, §3.7).

## 케이스 모양

이 계약은 **순수 수치 함수**다 — git 이력도 소스 트리도 결과에 영향을 주지 않는다. 그래서 케이스의 전제는 합성 리포가 아니라 측정값 배열 하나다.

```
<케이스>/input.json      측정값 배열 + 파라미터 (손으로 쓴다)
<케이스>/expected.json   compute.py가 만든다 (손으로 쓰지 않는다)
```

## 산술 — 부동소수점을 쓰지 않는다

`compute.py`는 전부 `fractions.Fraction`(정확 유리수)으로 계산한다. IEEE-754 double로 §2.5의 픽스처 예를 그대로 평가하면 **18.1이 나오지 않는다**:

```
h    = 1 + 0.9*9        = 9.099999999999999644729...
frac = h - 9            = 0.099999999999999644729...
Q    = 9 + frac*(100-9) = 18.09999999999996767...
```

계약이 적은 값은 `18.1`이다(§2.5). 정확 유리수로 계산하면 `h = 91/10`, `Q = 9 + (1/10)·91 = 181/10 = 18.1`로 정확히 일치한다. `expected.json`에 실리는 것은 이 값이다. 유효숫자 손실 없이 끝나는 십진수로 떨어지지 않는 값은 `non_terminating` 맵에 정확 유리수로 함께 기록한다 — 그 맵이 비어 있으면 파일 전체가 정확값이다.

## 최소 케이스 (§2.9)

| 케이스 | 무엇을 잡나 | 디렉터리 |
|---|---|---|
| 동점 | 동점 평균 순위. 3중 동점의 `rank_avg`가 같고, 그 앞뒤 순위가 건너뛴다 | [`ties/`](ties/) |
| N=1 | 유일한 파일의 pct는 0이 아니라 **null**(`(1−1)/(1−1)`은 0/0) | [`single-file/`](single-file/) |
| N<20 | `percentile.min_population` 미만 → 전원 null, `reason: insufficient_population` | [`below-min-population/`](below-min-population/) |
| 렌즈 백분위(0 포함) | null 렌즈 값은 랭킹에서 **제외**, 0은 **포함**. F가 대부분 0인 분포에서 0의 pct | [`lens-percentile-zero-included/`](lens-percentile-zero-included/) |
| P90 type-7 | `[1,2,…,9,100]`, q=0.9 → h=9.1 → **18.1** | [`p90-type7/`](p90-type7/) |
| IQR=0 → low | median=0·IQR=0·N≥200에서 `IQR < 0.25·median`은 0<0이라 놓친다. `IQR = 0` 절이 잡는다 | [`iqr-zero-low-confidence/`](iqr-zero-low-confidence/) |
| 언어 분리 | `cx` 백분위가 java/kotlin 모집단에서 따로 계산됨(D12) | **미작성** |
| 0 팽창 | 0이 다수인 성분에서 동점 평균 순위가 0에 주는 pct | **미작성** |

미작성 둘은 G0 동결 전에 필요하다(§9 G0 #2·#3).

## 미해결 — 계약이 답하지 않는 것

1. **`median`·`IQR`의 분위 방법이 명시되지 않았다.** §2.5는 type-7을 "F의 P90"에 대해서만 지정하는데, `median`·`IQR`도 분위이고 §2.5 표시 규칙(`IQR < 중앙값의 25%` → `population_note`)과 §3.7 confidence가 둘 다 쓴다. 이 픽스처는 `reproduce.percentile_method.quantile = "type7-linear"`를 **단일 방법 선언**으로 읽어 `median = Q(0.5)`, `IQR = Q(0.75) − Q(0.25)`로 계산했다. 계약이 확정되면 이 문단을 지운다.
2. **`lens_percentiles.<lens>.n`이 모집단 크기인지 랭킹 집합 크기인지 불분명하다.** §7 예시는 `F: {pct: 0.45, population: "all", n: 340}`인데 같은 예시의 `age_last_days.valid_n = 338`이고 §3.3에 의해 나이 미상 2건은 F = null이므로 랭킹 집합은 338이다. 인쇄된 340으로는 pct를 재계산할 수 없다(B.4). 이 픽스처는 두 값을 **`n_population`과 `n_ranked`로 나누어** 기록하고, pct는 `n_ranked`로 계산한다.
