# `blame-forbidden-on-scan-change` — 주석과 문자열 리터럴을 어떻게 가르는가

§2.7·D18·D113. 이 케이스는 값을 대조하지 않고 **부재**를 본다: `scan`·`change` 경로에 blame이 없다.

## 결정 — 주석은 버리고 문자열 리터럴은 남긴다

소스를 훑기 전에 **주석을 제거하고 문자열 리터럴은 보존한다**(`split_java`). 둘을 같이 다루면 규칙이 둘 중 하나로 망가진다.

| 둘 다 보면 | 둘 다 안 보면 |
|---|---|
| `// 매 스냅 blame 금지(D18)` 같은 **계약 인용 주석**이 걸린다. 이 리포의 코드 스타일이 정확히 그것이라(`JqradarArchRules.java`도 `compute.py`도 계약 인용으로 가득하다) 규칙이 G1에 **"계약을 설명하는 주석 금지"**가 된다 | `new ProcessBuilder("git", "blame", "-p")`를 놓친다. 타입 의존이 없어 **자체 ArchUnit 규칙 2도 못 잡는** 경로다 |

코드 쪽에서는 리터럴을 `""`로 지운다 — 그래야 `.blame(`이 주석이나 문자열이 아니라 **호출**일 때만 걸린다.

`contract/judgment-vocabulary.json`이 `not_judgment` 절과 단어 경계로 오탐을 다루는 것과 같은 규율이다.

## 증거의 세 종류

| 종류 | 무엇 | 왜 |
|---|---|---|
| `code_token` | `BlameCommand` · `.blame(` — **주석을 뺀 코드**에서 | 타입과 호출 |
| `string_literal` | **명령 조각** 모양의 리터럴에서 토큰이 정확히 `blame` | ProcessBuilder 인자 |
| `corroborating_literal` | `--porcelain` — **blame 리터럴과 연접할 때만** | 단독으로는 증거가 아니다 |

### 리터럴이라고 다 증거는 아니다

명령 조각 모양일 때만 센다: 공백으로 쪼갠 토큰이 **전부 CLI 형태**(`[A-Za-z0-9._/=-]+`)이고 그중 하나가 **정확히** `blame`일 때. ProcessBuilder 인자는 정확한 토큰이고 산문은 아니다.

이 규칙은 실제 오탐에서 나왔다 — `JqradarArchRulesTest`의 `@DisplayName("어기면 잡는다 — git.blame()")`이 처음 판에 걸렸다. **이 리포에 있는 문장**이다.

### `--porcelain`은 단독으로 증거가 아니다

`git status --porcelain`·`git push --porcelain`이 흔하다. `blame`과 연접할 때만 센다.

## 왜 `must_not_be_caught`가 있어야 하는가

`schema/`가 긍정과 변조를 둘 다 요구하는 것과 같다(D124). 처음엔 `must_be_caught`만 있었고, 그래서 **오탐을 볼 방법이 없었다** — 마커가 넓어질수록 통과는 쉬워지고 규칙은 쓸모없어진다.

| 절 | 무엇을 지키나 |
|---|---|
| `must_be_caught` (4) | 규칙이 **무는지**. 하나라도 놓치면 `verdict: reject` |
| `must_not_be_caught` (5) | 규칙이 **너무 물지 않는지**. 하나라도 걸리면 `verdict: reject` |

## 검사에서 빼는 자리

**좁게** 둔다 — 넓게 빼면 검사가 공집합을 훑고 그 "통과"는 "검사하지 않았다"와 구별되지 않는다.

- `io/jqradar/ledger/` — §5.6의 유일한 예외(캠페인 생성 1회, D57)
- `io/jqradar/arch/violations/` — 자체 ArchUnit 규칙의 반례. 일부러 어기는 것이 존재 이유다

**테스트 소스 전체를 빼지 않는다.** 스캐너가 주석과 리터럴을 가르므로 계약을 인용하는 테스트 코드는 어차피 걸리지 않고, `scan`/`change`를 부르는 테스트는 걸려야 한다.

## ArchUnit 규칙 2와의 관계

겹치는 것이 아니라 **서로 다른 구멍**을 막는다.

| | 자체 ArchUnit 규칙 2 | 이 케이스 |
|---|---|---|
| 층 | 바이트코드 | 소스 |
| 잡는 것 | 타입 의존(`BlameCommand`) | 타입 + 호출 + **CLI 인자 리터럴** |
| 못 잡는 것 | `ProcessBuilder("git","blame")` — 타입 의존이 없다 | 리플렉션으로 부르는 경로 |
