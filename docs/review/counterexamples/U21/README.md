# U21 — D202-1이 덮지 않는 id 입력 배열의 순서 (반례 (B) 갈림 · 게이트 G0 — `reproducibility/`)

- **인용**: §2.5 표 D202-1 — 배열의 순서를 정하는 표(그 머리의 "모든 배열"); §2.8 `source_scope`(`main_roots`·`test_roots`·`generated_roots` — `[id]`, D210). `main_roots`의 순서를 정하는 문장은 표에도 §2.8에도 없다 — 두 순서가 둘 다 허용된다.
- **입력**: `contract/reproducibility/same-tree-different-origin/`의 트리·이력과 `convention` 범위(`main_roots` = `src/main/java`·`src/main/kotlin`).
- **두 값**(`run.py`가 계산한다 — `contract/reproducibility/compute.py`의 `analysis_input_id`): `main_roots`를 사전순으로 넣은 id와 역순으로 넣은 id — 다르다(JCS는 배열의 순서를 건드리지 않는다).
- **무엇이 갈리나**: 같은 트리·같은 범위·같은 툴체인에서 두 구현이 다른 `analysis_input_id`를 낸다 — 캐시 미스와 "두 머신 바이트 동일"의 실패. 순서 린트는 표에 없는 배열을 통과시킨다. 같은 모양이 `test_roots`·`generated_roots`·`bytecode_scope.class_roots`에 있다.
- **게이트**: 값이 `reproducibility/` 스위트(G0)의 것 → G0(D266).
