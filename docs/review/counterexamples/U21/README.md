# U21 — D202-1이 덮지 않는 배열 (반례 (A) 불일치 · 게이트 G0 — `schema/`의 순서 린트)

- **인용**: §2.5 표 D202-1 머리 "산출물의 모든 배열은 이 키로 정렬된다 … **표에 없는 배열이 산출물에 나오면 실패한다** — 새 배열은 표에 먼저 들어온다, D269" · 표의 행 "키 없는 문자열 배열(`source_scope`의 `main_roots`·…, `bytecode_scope.class_roots` …) | `asc`(§2.8의 경로 비교)".
- **어디까지 닫혔나**: id 입력인 범위의 루트 배열의 순서(처음 반례 — 사전순·역순이 다른 `analysis_input_id`)는 D269로 닫혔고 `reproducibility/source-scope-roots-order-canonical`이 그 값을 박는다. 남은 주장은 "표가 모든 배열을 덮지 않는다"다.
- **입력**: §7 블록 전부(`contract/schema/compute.py`가 꺼내는 그 문서들)와 prd.md의 표 D202-1(행의 첫 칸 백틱 이름 — 코드 속 목록이 아니다).
- **두 값**(`run.py`가 계산한다): D269대로 표에 없는 배열을 세면 §7 블록이 **거부**된다(표에 없는 배열 20개 — 위치가 뜻인 `[base, head]` 쌍 `ccd`·`nccd`·`repo_cx`·`target_cx`, `evidence`·`transitions`·`guardrails`·`targets`, 빈 배열들 …) vs §7 예시는 긍정 케이스라 **통과**해야 한다.
- **둘째 어긋남**: 표의 "키 없는 문자열 배열 → `asc`"는 위치가 뜻인 문자열 배열도 덮는다 — `classes_reproduction_inputs.compiler_args`(javac 인자)를 정렬하면 다른 명령이 된다.
- **무엇이 갈리나**: D269의 "표에 없는 배열은 실패"를 그대로 구현하면 §7이 붉고, 구현하지 않으면 U21의 주장이 남는다. 표가 그 배열들(과 위치 순서라는 종류)을 먼저 받거나, 규칙이 좁혀져야 한다 — 결정이다(구현 세션은 그 부분에서 멈췄다, CLAUDE.md §7).
- **게이트**: 값(린트 판정)이 `schema/` 스위트(G0)의 것 → G0(D266).
