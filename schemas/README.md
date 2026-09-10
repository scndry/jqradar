# `schemas/` — 산출물 JSON Schema 6종 (§7)

§7의 jsonc 스케치를 **기계 검증 가능하게** 옮긴 것이다. draft 2020-12.

| 파일 | 산출물 | 계약 | §7 예시 |
|---|---|---|---|
| [`report.schema.json`](report.schema.json) | `jqradar scan` → 지도 | §2, §3 | 있음 ✅ |
| [`change.schema.json`](change.schema.json) | `jqradar change --base` → 변경 리포트(1차 표면) | §5.1–5.2, §5.7 | **없음** ⚠️ |
| [`gate.schema.json`](gate.schema.json) | `jqradar check` → 게이트 | §5.3 | 있음 ✅ |
| [`validate.schema.json`](validate.schema.json) | `validate` → 검증 결과 | §6.3 | 있음 ✅ |
| [`campaign.schema.json`](campaign.schema.json) | `campaign create` → 조직이 소유하는 정의 | §5.4 | 있음 ✅ |
| [`event.schema.json`](event.schema.json) | 사건 파일 = 원장의 사건 층 | §5.5 | 있음 ✅ |

## 원칙

1. **필드마다 §번호.** 모든 `description`이 계약의 어느 문장에서 왔는지 가리킨다. 스키마는 계약의 재진술이지 새 계약이 아니다.
2. **계약이 정하지 않은 것은 닫지 않는다.** `check`의 규칙 이름은 조직이 적는 자리라(B.6) enum이 아니고, `change.json`의 항목 이름은 §5.1이 정하지 않아 enum이 아니다. 추측으로 계약을 채우지 않는다(CLAUDE.md §7) — 대신 `x-jqradar-unresolved`에 무엇이 열려 있는지 적는다.
3. **하드룰은 구조로 막는다.** 설명으로만 적으면 지켜지지 않는다.
   - `event.schema.json`은 `additionalProperties: false`다 — 이름·이메일·핸들(D48·D108)도, 코드 상태·원장 상태(D55·D61)도 **스키마상 표현 불가**하다.
   - `verdict: "validated"`는 `validated_tree_id`·`validated_analysis_input_id`·`validated_head_sha`·`validation_scope`를 `if/then`으로 요구한다 — 이것이 없는 `validated`는 `validated`가 아니다(§6.3 5a, D89).
   - `campaign_mode: "target_driven"`은 `targets`를 요구한다(D78).
   - `changeItem`은 `verdict`·`severity`·`score`·`rank`·`grade`를 `not`으로 금지한다 — §5.1의 "판정 단어는 없다"를 기계로 옮긴 것이다.
4. **겉모양 패턴은 강제하지 않는다.** `sha256:<hex>` 같은 형식은 `description`에만 적는다. §7의 예시는 `"sha256:…"`·`"git-sha"` 같은 자리표시자를 쓰는데, 그것을 `pattern`으로 거부하면 **스키마가 자기 계약의 예시를 거부**하게 된다. 실제 픽스처(`contract/lens/sample-service/`)가 생기면 그쪽에서 실제 해시를 대조한다.

## `report.schema.json`의 contract 부분집합

CLAUDE.md §3.3이 요구한 대로 `x-jqradar-contract-subset`에 명시했다 — 적합성 스위트(§2.9)가 **재계산으로 대조하는** 경로들이다. 이름 대응에 주의:

| CLAUDE.md §3.3의 이름 | prd.md 본문의 이름 | 경로 |
|---|---|---|
| `reproduce` | `reproduce`(§2.8) | `/reproduce` |
| `measurements` | `measures`(§2.1) · `population`(§2.5) · `system`·`components`(§2.2–2.3) | `/files/*/measures` 외 |
| `delta` | `change.json`의 항목(§5.1) — **report에는 없다** | (change 쪽) |
| `conflicts` | **대응 없음** | — |

`conflicts`는 prd.md 본문(§1–§12) 어디에도 없는 이름이라 슬롯을 비워 두고 `unresolved`를 적었다. 무엇을 가리키는지는 소유자의 결정이다.

## 실행

```sh
python3 -m pip install -r schemas/requirements.txt

python3 schemas/validate_examples.py             # §7 예시가 스키마를 통과하는가
python3 schemas/validate_examples.py --negative  # 하드룰 변조본이 거부되는가
python3 schemas/validate_examples.py --dump out/ # 추출한 예시를 파일로
```

`--negative`가 있는 이유: 전부 통과하는 스키마는 아무것도 지키지 않는다. 첫 작성에서 §7 예시 다섯이 한 번에 통과했을 때 이 모드를 만들었고, 그 과정에서 `path_base_mapped`가 null을 못 받는 버그를 찾았다(진짜 새 발생은 BASE에 대응 경로가 없다).

## 아직 스키마가 없는 §7 예시

- **`fixture_change` 레코드**(§2.9 끝) — `expected.json` 변경 커밋에 동반된다. CI 규칙(G0 #6)이 이것을 검사하므로 스키마가 필요해질 수 있다.
- **원장 뷰 한 행**(§5.5) — 저장되지 않고 파생되는 뷰라 "산출물 스키마 6종"에 들지 않았다. `--at` 재구성 결정성(D79)을 검사하려면 결국 필요하다.
