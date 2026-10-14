# U8 — `repository_state_id`·`head`는 [id]인가 (반례 (A) 불일치 · 게이트 G0 — `reproducibility/`)

- **인용**: §7 report `reproduce` — `"head": "git-sha"  // [id]`, `"repository_state_id": …  // [id] [fn] [id]`(첫째가 `repository_state_id`); §7 머리 주석 "필드는 세 종류뿐(D158·§2.8): [id] id 입력 · [fn] id 입력의 결정적 함수 · [x] 비교 제외(D154)"; §2.8 `repository_state_id` = HEAD 트리의 경로 중 작업트리에 있는 것의 `(path, content_id)`, **내용은 작업트리 바이트**(D223); §2.8 `analysis_input_id`의 입력은 소스 파일 `(path, content_id)`의 **적격 목록**("`repository_state_id`의 트리 전체가 아니다")·창 안 커밋 SHA 목록(머지 제외 — §2.7) — `head`도 `repository_state_id`도 목록에 없다. 계산기의 자기 반례 `I_TO_SPEC`는 `repository_state_id → source_files`, `head → commit_list_sha256`으로 **이름만** 대응시킨다.
- **입력**: `run.py`가 합성 리포 셋을 만든다 — (1) 커밋 하나(`A.java`·`README.md`), 작업트리의 `README.md`만 고친 스캔과 깨끗한 스캔; (2) 같은 비머지 이력 위에 메시지만 다른 머지 HEAD 둘(커미터 시각 같음).
- **두 값**(`run.py`가 reproducibility 계산기로 계산한다): [id]대로면 `analysis_input_id`가 같은 두 스캔은 그 필드도 **같다**; 계산기로는 (1) `analysis_input_id` 같고 `repository_state_id` **다르다**(README는 적격 소스가 아니다), (2) `analysis_input_id`·`repository_state_id` 같고 `head` **다르다**(머지는 W 밖이라 목록에 없다).
- **무엇이 갈리나**: 두 필드는 id 입력이 아니고(입력이 달라도 id가 같다) id 입력의 함수도 아니다(같은 입력에서 다른 값) — D158의 "넷째 종류는 없다"가 깨진다. 비교 대상(D154)인데 [x]도 아니라 "같은 id, 다른 바이트"의 두 리포트가 생긴다. `head`는 비머지 HEAD에서만 목록이 봉인한다.
- **게이트**: 값(id와 그 필드의 관계)이 `reproducibility/` 스위트(G0 — §2.8 (i) ↔ id 스펙의 자기 반례도 거기)의 것 → G0(D266).
