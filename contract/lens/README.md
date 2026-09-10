# `lens/` — 렌즈 조립 계약 (§3) · 게이트 **G1**

## 이 계약이 고정하는 것

**성분에서 렌즈로 올라갈 때 null이 어떻게 전파되는가**와 **무엇을 곱하지 않는가**를 못 박는다.

- `H = 100·√(pct_active,lang(cx) × pct_active(chg_commits))` — 변경 단위는 `chg_commits`로 **잠금**(D27).
- `Dx = 100·√(pct_dx(union_dup_tokens) × pct_dx(active_twin_ratio))`, 모집단 `dx`. `twins = 0` → `active_twin_ratio` null → Dx **null**(경쟁에 없다, D29).
- `F = 100·√(pct_all,lang(cx) × pct_all(fan_in)) × 𝟙[age > P90_all(age) ∧ age ≥ 180]`. `age_last_days = null` → F **null**(0이 아니다, D37).
- `composite` = **세 렌즈가 모두 non-null일 때만**. 재정규화는 부풀리고 0 대입은 깎으므로 둘 다 하지 않는다(D29).
- 아키텍처 맥락은 **붙이는 것**이지 곱하는 것이 아니다(§3.4).
- 렌즈 confidence = 기여 성분의 **최소**(D28).

§7의 `sample-service` 예시 전체가 이 디렉터리의 픽스처다 — CI가 measures로부터 `H`·`Dx`·`F`·`composite`·`NCCD`·confidence·`lens_percentiles`를 재계산해 대조한다(§7 머리말).

## 최소 케이스 (§2.9)

| 케이스 | 무엇을 잡나 | 상태 |
|---|---|---|
| **`sample-service/`** | §7 예시 전체의 재계산. `H = 95.5`, `Dx = 79.0`, `composite = 71.5`, `NCCD = 2.76`, `F(OrderPolicy) = 96.5` | 미작성 |
| H/Dx/F 각 모집단 | 같은 파일이 모집단마다 다른 pct를 받는다 | 미작성 |
| composite null | 한 렌즈가 null이면 composite null + `composite_note` | 미작성 |
| confidence 최소 집계 | 성분 하나가 low면 렌즈도 low | 미작성 |
| tie-break | `priority desc, path asc, id asc`(D28) | 미작성 |
| F null(나이 미상) | 나이 null → F null, `interpretation`도 null | 미작성 |

`percentile/`의 케이스가 성분 수준을 고정하고, 여기가 그 위의 조립을 고정한다 — 순서가 그래서 G0 → G1이다.
