# `contract/fixture-changes/` — `expected.json`을 바꾼 이유

§2.9: 기대값을 바꾸는 커밋은 `fixture_change {reason ∈ {library_behavior_change, contract_change, bug_fix}, library?, old?, new?, measure, note}`를 **반드시 동반한다**. 원인 분류 없이는 머지 불가 — 회귀 테스트가 "새 정답을 손으로 승인하는 테스트"로 변질되는 것을 막는 장치다(P11).

레코드 하나 = 파일 하나, 이름은 `<날짜>-<슬러그>.json`. 스키마는 [`schemas/fixture_change.schema.json`](../../schemas/fixture_change.schema.json)이고 G0 체크리스트 #6의 CI 규칙이 이것을 검사한다(D119).

**레코드의 위치는 이제 계약이다**(§2.9, D129). 파일이어야 하는 이유: 커밋 메시지나 PR 본문은 스키마로 검증할 수 없어 G0 체크리스트 #6의 CI 규칙이 설 자리가 없다.
