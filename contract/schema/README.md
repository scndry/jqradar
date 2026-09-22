# `schema/` — 산출물 스키마 계약 (§7, §2.9 `schema/` 행) · 게이트 **G0**

## 이 계약이 고정하는 것

**스키마가 문법 검사가 아니라 계약이라는 것.** 산출물 8종(`report`·`change`·`gate`·`validate`·`campaign`·`event`·`fixture_change`·`people` — D161)마다 **긍정 1 + 거부되어야 할 변조 ≥ 1**을 두고, 변조는 타입 오류가 아니라 **하드룰**을 겨눈다(D124).

전부 통과하는 스키마는 아무것도 지키지 않는다. 첫 판에서 §7 예시 다섯이 한 번에 통과했을 때 이 디렉터리의 조상이 생겼고, 그 뒤 실제로 잡은 것들이 이 계약이 있는 이유다:

- `path_base_mapped`가 `null`을 못 받던 버그 — 진짜 새 발생은 BASE에 대응 경로가 없다(§5.2)
- `gate`에 하드룰 변조가 0이던 것 — `context_changed`가 어느 규칙에나 붙어 판정 탈출구가 되던 자리(D98)
- `not { pattern }`에 `type: "string"`이 없어 정상적인 `null`을 거부하던 버그 — `pattern`은 문자열 아닌 값에 무시된다
- `if`/`then` 안까지 `additionalProperties: false`를 넣어 조건부가 통째로 죽던 회귀 — `if`가 "이 속성만 가진 문서"에만 맞게 되어 D78·D89·D98이 전부 무력해졌다. **이 케이스들이 그것을 그 자리에서 잡았다.**

## 세 층 (D125·D126·D127)

하드룰은 한 스키마에만 걸면 다른 표면으로 샌다. 그리고 층을 잘못 고르면 못 막는다.

| 층 | 무엇을 막나 | 왜 이 층인가 |
|---|---|---|
| `additionalProperties: false` | 형태가 알려진 객체의 없는 필드 — `files[].author`(D48), `findings[].severity`·`score`(B.2), `campaign.quality_grade`(B.3), `gate.score`, `validate.severity` | 스키마가 열려 있으면 금지된 것을 **더해도** 통과한다(D126) |
| `not { type: "string", pattern }` | 자유 텍스트(`*_note`)의 판정 어휘(D67·D127) | 렌더러는 JSON의 **순수 함수**라 JSON에 들어간 판정 단어는 그대로 화면에 뜬다 — UI에서만 막으면 늦다 |
| **원문 텍스트 린트** | 직렬화 스케일(D115·D125) | JSON Schema로는 **불가능**하다. `multipleOf: 0.1`은 이진 부동소수점에서 `95.6`을 거부한다 — 스키마에 넣으면 옳은 값이 죽는다. 읽을 때도 `double`을 경유하지 않는다(`parse_float=str`) |

판정 어휘 사전은 [`contract/judgment-vocabulary.json`](../judgment-vocabulary.json) **한 곳**에만 있다. `contract/schema/`(지금)와 `contract/renderer/`(G2)가 같은 파일을 읽고, `vocabulary-sync` 케이스가 스키마에 심긴 패턴이 사전과 어긋나지 않았는지 본다.

## 케이스 모양

```
<케이스>/input.json      {check, kind, schema, base, patch|text_patch, mechanism, contract_ref, what}
<케이스>/expected.json    compute.py가 만든다 — verdict와 거부된 경로
```

- `base` — `prd:§7:<블록>`은 **prd.md에서 직접** 읽는다. §7 예시가 곧 픽스처이므로(D26) 복사본을 두면 드리프트한다. §7에 예시가 없는 `change`만 [`base/`](base/)에 손으로 쓴 문서를 둔다. G1에 §7 예시가 `contract/lens/sample-service/`에서 **생성**되면(D128) `prd:` 참조가 그쪽으로 옮겨간다.
- `kind` — `positive` / `hard_rule` / `structural`. 판정 기준은 하나다: **계약을 모르는 사람이 §7 예시만 보고 스키마를 써도 잡혔을까?** 아니오면 `hard_rule`.

## 실행

```sh
python3 contract/schema/compute.py            # 케이스 실행 + expected.json 재생성
python3 contract/schema/compute.py --check    # 커밋된 것과 같은지 (CI)
python3 contract/schema/vocabulary.py --sync  # 사전 -> 스키마 pattern 심기
```

집계가 함께 나온다. 대상 하나라도 하드룰 변조가 0이면 그 줄에 **`D124 미충족`**이 찍힌다.
