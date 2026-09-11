# `graph/` — 컴포넌트·시스템 그래프 계약 (§2.2–2.3) · 게이트 **G0**

## 이 계약이 고정하는 것

**무엇이 노드이고 무엇이 간선인가**, 그리고 그 위의 Martin·Lakos 숫자. 지표 자체는 ArchUnit `ArchitectureMetrics`가 내므로(D3) 이 계약이 고정하는 것은 **그 앞의 전처리**다 — 무엇을 접고 무엇을 빼는가.

- **`bytecode_scope`** — 프로젝트 자체 모듈의 main 클래스만. 외부 타입 간선은 `external` 의사 노드로 **접어 기록하되** 지표에서는 **제외**한다.
- **`component.strategy`** — `module` / `auto` / `depth:<n>`. 결정 결과를 `reproduce`에 인쇄한다(D15).
- **순환** — Tarjan SCC. 크기 2 이상만 순환이다.
- **Lakos** — `CCD` = Σ(전이적 도달 컴포넌트 수, 자기 포함), `NCCD = CCD / ((N+1)·log₂(N+1) − N)`.

## 산술

`I`·`A`·`D`·`ACD`·`RACD`는 정확 유리수다. `NCCD`는 `log₂`가 무리수라 34자리에서 파생하고 **마지막에 한 번만** 반올림한다(§2.5 산술 계약, D115·D121) — 표시값끼리 나누면 갈린다.

## 최소 케이스 (§2.9)

| 케이스 | 무엇을 잡나 |
|---|---|
| [`external-edges/`](external-edges/) | §2.2가 **이름까지 지정한** 필수 케이스. 외부 간선을 기록하되 지표에서 뺀다 |
| [`auto-longest-common-prefix/`](auto-longest-common-prefix/) | `auto` 1/4 — 최장 공통 접두어 아래 첫 레벨 |
| [`auto-single-child-descends/`](auto-single-child-descends/) | `auto` 2/4 — 자식이 하나면 한 칸 내려간다 |
| [`auto-oversized-child-splits/`](auto-oversized-child-splits/) | `auto` 3/4 — 60% 초과 자식은 추가 분할 |
| [`auto-multiple-roots/`](auto-multiple-roots/) | `auto` 4/4 — 루트가 여럿이면 루트별로 |
| [`component-cycle/`](component-cycle/) | Tarjan SCC. 새 SCC는 게이트에서 1개라도 FAIL이다(§5.3) |
| [`nccd-cross-check/`](nccd-cross-check/) | §2.3 본문의 검산 — N=41, CCD=512 → 185.48 / 12.49 / 0.305 / **2.76** |
| [`deep-enterprise-packages/`](deep-enterprise-packages/) | **P8의 합성 리포**(§9) — 깊은 기업형 패키지에서 `auto`가 업무 영역을 내는가 |

`deep-enterprise-packages/`가 `docs/battery.md`가 예고한 P8 합성 리포다. 패키지가 6–7단계일 때 `auto`가 기술 계층(domain·adapter)이 아니라 업무 영역(orders·payments·shipping·shared)으로 접는지를 본다. P8은 이것을 아키텍트 2명의 블라인드 주석과 대조하고(inter-rater κ), 이 픽스처는 그 대조의 **입력**을 결정적으로 고정한다.

## 미해결 — 계약이 답하지 않는 것

**§2.2의 "60% 초과 자식"이 *무엇의* 60%인지 정하지 않는다.** 패키지 수로 세는 것과 클래스 수로 세는 것이 갈린다 — 패키지가 셋이고 클래스가 6:1:1이면 패키지 기준 33%, 클래스 기준 75%다. 이 계산기는 **클래스 수**로 읽는다: 규칙의 목적이 "한 자식이 코드 대부분을 쥐어 컴포넌트가 사실상 하나가 되는 것"을 막는 데 있고, 그 '대부분'은 패키지 개수가 아니라 코드의 양이기 때문이다. 계약이 정하면 따라간다 — `expected.json`이 바뀌면 `fixture_change {reason: contract_change}`가 필요하다.

## 실행

```sh
python3 contract/graph/compute.py --check
```
