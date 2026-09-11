# `schemas/` — 산출물 JSON Schema 7종 (§7)

§7의 jsonc 스케치를 **기계 검증 가능하게** 옮긴 것이다. draft 2020-12.

| 파일 | 산출물 | 계약 | §7 예시 |
|---|---|---|---|
| [`report.schema.json`](report.schema.json) | `jqradar scan` → 지도 | §2, §3 | 있음 ✅ |
| [`change.schema.json`](change.schema.json) | `jqradar change --base` → 변경 리포트(1차 표면) | §5.1–5.2, §5.7 | **없음** ⚠️ |
| [`gate.schema.json`](gate.schema.json) | `jqradar check` → 게이트 | §5.3 | 있음 ✅ |
| [`validate.schema.json`](validate.schema.json) | `validate` → 검증 결과 | §6.3 | 있음 ✅ |
| [`campaign.schema.json`](campaign.schema.json) | `campaign create` → 조직이 소유하는 정의 | §5.4 | 있음 ✅ |
| [`event.schema.json`](event.schema.json) | 사건 파일 = 원장의 사건 층 | §5.5 | 있음 ✅ |
| [`fixture_change.schema.json`](fixture_change.schema.json) | `expected.json`을 바꾼 이유 | §2.9 끝 | 있음 ✅ |

## 원칙

1. **필드마다 §번호.** 모든 `description`이 계약의 어느 문장에서 왔는지 가리킨다. 스키마는 계약의 재진술이지 새 계약이 아니다.
2. **계약이 정하지 않은 것은 닫지 않는다.** `check`의 규칙 이름은 조직이 적는 자리라(B.6) enum이 아니고, `change.json`의 항목 이름은 §5.1이 정하지 않아 enum이 아니다. 추측으로 계약을 채우지 않는다(CLAUDE.md §7) — 대신 `x-jqradar-unresolved`에 무엇이 열려 있는지 적는다.
3. **하드룰은 구조로 막는다.** 설명으로만 적으면 지켜지지 않는다.
   - `event.schema.json`은 `additionalProperties: false`다 — 이름·이메일·핸들(D48·D108)도, 코드 상태·원장 상태(D55·D61)도 **스키마상 표현 불가**하다.
   - `verdict: "validated"`는 `validated_tree_id`·`validated_analysis_input_id`·`validated_head_sha`·`validation_scope`를 `if/then`으로 요구한다 — 이것이 없는 `validated`는 `validated`가 아니다(§6.3 5a, D89).
   - `campaign_mode: "target_driven"`은 `targets`를 요구한다(D78).
   - `changeItem`은 `verdict`·`severity`·`score`·`rank`·`grade`를 `not`으로 금지한다 — §5.1의 "판정 단어는 없다"를 기계로 옮긴 것이다.
4. **겉모양 패턴은 강제하지 않는다.** `sha256:<hex>` 같은 형식은 `description`에만 적는다. §7의 예시는 `"sha256:…"`·`"git-sha"` 같은 자리표시자를 쓰는데, 그것을 `pattern`으로 거부하면 **스키마가 자기 계약의 예시를 거부**하게 된다. 실제 픽스처(`contract/lens/sample-service/`)가 생기면 그쪽에서 실제 해시를 대조한다.

## 실행

```sh
python3 -m pip install -r schemas/requirements.txt

python3 schemas/validate_examples.py             # §7 예시가 스키마를 통과하는가
python3 schemas/validate_examples.py --negative  # 하드룰 변조본이 거부되는가
python3 schemas/validate_examples.py --dump out/ # 추출한 예시를 파일로
```

`--negative`가 있는 이유: 전부 통과하는 스키마는 아무것도 지키지 않는다. 첫 작성에서 §7 예시 다섯이 한 번에 통과했을 때 이 모드를 만들었고, 그 과정에서 `path_base_mapped`가 null을 못 받는 버그를 찾았다(진짜 새 발생은 BASE에 대응 경로가 없다).

## 변조가 하드룰을 겨누는가 (D124)

구조 오류만 잔뜩이면 스키마는 문법 검사이지 계약이 아니다. 그래서 변조마다 **kind·기구·근거 D번호**를 붙이고 `--negative`가 집계를 인쇄한다. 판정 기준은 하나다 — **계약을 모르는 사람이 §7 예시만 보고 스키마를 써도 잡혔을까?**

- `hard_rule` — 아니오. 거부하려면 특정 하드룰을 알고 구조를 넣었어야 한다(`additionalProperties: false` / `not` / `if-then` / `const`, 또는 **어휘 자체가 하드룰인** enum).
- `structural` — 예. 타입·범위·required·전사한 enum이라 계약을 몰라도 잡힌다.

집계는 `--negative`가 낸다. 스키마 하나라도 하드룰 변조가 0이면 그 줄에 `D124 미충족`이 찍힌다 — `gate.schema.json`이 실제로 그렇게 걸려서 D98(`context_changed`는 `nccd_increase` 전용)을 `if/then`으로 넣었다.

## 아직 스키마가 없는 §7 예시

**원장 뷰 한 행**(§5.5) — 저장되지 않고 파생되는 뷰라 산출물 스키마 7종에 들지 않는다. 게이트는 G2b이고(§0-15), `--at` 재구성 결정성(D79)을 검사하려면 그때 필요하다.

## 다음

긍정·변조 케이스는 `contract/schema/`로 옮겨 픽스처 루프(CLAUDE.md §4)가 돌게 해야 한다(§2.9 `schema/` 행, D124). 지금은 `validate_examples.py` 안에 있어 `contract/` 밖이다 — 후속 PR `g0/v377-alignment`.
