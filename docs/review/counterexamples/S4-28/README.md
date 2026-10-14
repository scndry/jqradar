# S4-28 — G0 픽스처의 비율 필드 직렬화 (반례 (A) 불일치 · 게이트 G0 — `history/`·`cpd/`·`percentile/`)

- **인용**: §2.5 "스케일은 **고정**이다(`setScale(n, HALF_EVEN).toPlainString()`, 후행 0 유지 — `0.38`이 아니라 `0.3800`)" + 표 D155-1 "| 비율(0–1) | `pct`·…·`dup_extent`·…·`tc`·`ownership_max_share`·… | **4자리** |"; §2.9 "**값은 그대로인데 직렬화만 바뀐 경우도 `contract_change`다** — 직렬화 형식은 계약이기 때문이다".
- **입력**: `contract/history/author-facts-minor-threshold/input.json` — `src/Boundary21.java`의 `ownership_max_share` = 19/21.
- **두 값**(`run.py`가 계산한다): D155-1의 4자리 `0.9048` vs G0 픽스처의 직렬화(`contract/tools/exact.py` — 끝나지 않는 유리수는 12자리 HALF_EVEN) `0.904761904762`. 같은 모양은 끝나는 값에도 있다(`tc` 0.6 vs D155-1의 `0.6000`).
- **무엇이 갈리나**: 같은 이름의 필드가 산출물(§7)과 G0 픽스처에서 다른 바이트 — D155-1이 픽스처에도 걸리는가(그러면 픽스처 재생성 + `contract_change`), 아니면 픽스처의 중간 사실은 대상이 아닌가(그러면 §2.5가 면제를 적는다; `contract/percentile/README.md`는 "반올림 전 값"을 따로 정했다).
- **게이트**: 값이 `history/`(그리고 `cpd/`·`percentile/`) 스위트(G0)의 것 → G0(D266).
