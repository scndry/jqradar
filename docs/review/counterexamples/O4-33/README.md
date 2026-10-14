# O4-33 — `findings`·`items`의 정렬 키 (반례 (B) 갈림 · 게이트 G0 — `schema/`의 순서 린트)

- **인용**: §2.5 표 D202-1 "| `findings` | `kind`의 고정 순서(…) · `priority desc` · `path asc` · `id asc` |" · "| `gate.json` `checks` · `items` | 프로필 선언 순서 · `file`/`path_head asc` |". §7의 finding은 `file`(파일 **id**)을 갖고 `path`를 갖지 않는다; 순환 finding은 `component`, 숨은 결합 finding은 `pair {a, b}`만 갖는다.
- **입력**(`run.py` 안): id 순서와 경로 순서가 반대인 두 파일(`f:alpha` → `src/Z.java`, `f:zeta` → `src/A.java`)에 같은 priority(90.0)의 hotspot finding 둘; `new_duplication` 행에 같은 `path_head`(`src/A.java`)의 새 발생 둘.
- **두 값**(`run.py`가 계산한다):
  - findings — `file`(id)로 비교하면(지금의 순서 린트 `_order_key`) `[fnd:h-2, fnd:h-1]`, `files[]`의 `path`로 비교하면 `[fnd:h-1, fnd:h-2]`. 둘 다 "`path asc`"의 읽기다.
  - items — 같은 `path_head`의 두 순서가 **둘 다** 린트를 통과한다 — 키가 전순서가 아니라 두 구현이 다른 바이트를 낸다.
- **무엇이 갈리나**: 배열 순서는 바이트다(D154) — 두 구현이 같은 산출물을 다른 바이트로 낸다. 렌즈 없는 finding(순환·숨은 결합)은 `priority`도 `file`도 없다 — 키가 그 종류에서 무엇인지도 표에 없다.
- **게이트**: 값(순서)이 `schema/` 스위트(G0)의 순서 린트의 것 → G0(D266).
