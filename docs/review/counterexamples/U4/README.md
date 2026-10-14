# U4 — reason 사전의 '오는 자리'와 스키마 (반례 (A) 불일치 · 게이트 G0 — `schema/`)

- **인용**: §2.5 "**`reason` 사전**(D188 — …) 셋째 열 '오는 자리'는 스키마의 if/then 부분집합과 **같은 표**다 — 사전이 한 곳이라는 말은 스키마가 이 표를 베낀다는 뜻이다" · 표의 행 "`no_bytecode` | … | 성분(`fan_in`)·렌즈(F)·`arch_context` 전체 null·쌍(D190)" · "`unsupported_language` | … | 성분(`cx`·`loc`·`smells`)·렌즈(H·F)".
- **입력**: §7 report 블록(`contract/schema/compute.py`가 꺼내는 그 문서)의 첫 파일에 사전이 허용한 (사유, 자리)를 하나씩 넣는다.
- **두 값**(`run.py`가 계산한다):
  - `no_bytecode` @ `arch_context` — 사전: 허용 · 스키마: 거부(`arch_context`의 `reason`은 `isolated_component`뿐, A도 값이어야 한다).
  - `unsupported_language` @ `percentile_population.loc` — 사전: 허용 · 스키마: 거부(`loc`은 명시된 성분이 아니고 그 밖의 성분은 소속 사유 셋뿐).
  - 대조군 `unsupported_language` @ `percentile_population.cx` — 사전·스키마 둘 다 허용(검사가 무는지).
- **무엇이 갈리나**: Kotlin 파일의 `loc` 백분위·클래스 없는 파일의 `arch_context`를 사전대로 쓴 산출물이 스키마에서 거부된다 — "같은 표"가 아니다. 리뷰어가 적은 나머지(나이 칸의 '성분' 표기, 원장 뷰 `anchor_values`의 `no_bytecode`)는 이 반례에 넣지 않았다.
- **게이트**: 값(스키마 판정)이 `schema/` 스위트(G0)의 것 → G0(D266).
