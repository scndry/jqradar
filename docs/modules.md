# 모듈 골격 (§4.1) — G0 상태

**빈 소스셋과 의존만.** G0 전에는 core 측정 코드를 쓰지 않는다(CLAUDE.md §3) — 계약과 픽스처가 먼저이고, v3.1·v3.2의 산술 오류와 v3.3의 계약 충돌이 그 순서의 이유다.

```
jqradar/
  settings.gradle.kts          모듈 여섯. 더 늘리지 않는다
  build.gradle.kts             공통 규약(Java 21 툴체인, -parameters, 재현 가능한 아카이브)
  gradle/libs.versions.toml    버전 고정 — §2.8 environment가 인쇄하는 값의 원본
  gradle/wrapper/              Gradle 9.7.1 — classes_reproduction_inputs.gradle
```

## 모듈 여섯과 의존 (§4.1)

| 모듈 | 의존 | G0에 있는 것 |
|---|---|---|
| `jqradar-core` | 증인 셋(pmd-java·pmd-kotlin·pmd-core·archunit·jgit) | 자체 ArchUnit 규칙(test) |
| `jqradar-ledger` | core, jgit | `LedgerPaths` — `.jqradar/`가 스펠링되는 유일한 자리 |
| `jqradar-cli` | core, ledger | 비어 있음 |
| `jqradar-gradle-plugin` | core, ledger, gradleApi | 플러그인 id 등록만(구현은 G2) |
| `jqradar-mcp` | core, ledger, remediation | 비어 있음 |
| `jqradar-remediation` | core, rewrite-java | 비어 있음 |

의존 방향이 §4.1 그대로다: **core는 아무도 의존하지 않는다.** `core`가 `ledger`를 참조하는 자리는 test 소스셋 하나뿐이고(규칙 3의 반례가 `LedgerPaths`를 참조해야 컴파일된다) main에서는 모른다.

**의존에 없는 것들과 그 이유**

- **d3** — Gradle 의존이 아니다. 렌더러에 **인라인**되는 번들이고 네트워크 요청 0건이 계약이다(§7.1 원칙 2). G2에 들어온다.
- **jacoco** — 일시(transient)로 붙는 런타임이지 컴파일 의존이 아니다(D16). G3.
- **컨테이너 런타임** — L2 샌드박스의 실행 환경이다(§6.6). G3.
- **네 번째 엔진** — 없다. 임베딩·이슈 트래커·런타임은 비목표다(§11).

## 버전 고정 (§2.8)

`gradle/libs.versions.toml` 한 곳. `environment`에 인쇄되는 셋은 `pmd`·`archunit`·`jgit`이고, **JGit만 아티팩트 좌표에 빌드 한정자가 붙는다**(`7.3.0.202506031305-r`) — 인쇄하는 값은 major.minor.patch(`7.3.0`)이고 카탈로그가 둘을 나눠 갖는다.

버전이 바뀌면 `analysis_input_id`가 바뀌어야 하고(D87), 픽스처 기대값이 움직이면 `fixture_change {reason: library_behavior_change}`가 필요하다(§2.9, P11).

## 자체 ArchUnit 규칙 (CLAUDE.md §3.5)

`jqradar-core/src/test/java/io/jqradar/arch/`. 규칙은 **우리 코드에만** 걸린다 — 대상 코드를 재는 렌즈(§3)가 아니다.

| # | 규칙 | 근거 | 지금 무엇을 잡나 |
|---|---|---|---|
| 1 | `PersonIdent`는 `people` 정책 패키지 밖에서 만지지 않는다 | §2.7·D48·D108 | 반례만(정책 패키지가 아직 없다) |
| 2 | `scan`/`change` 경로에 `BlameCommand` 없음 | §2.7·D18·D113 | 반례만 |
| 3 | `LedgerPaths` 의존은 `io.jqradar.ledger..`만 | §5.5·D60·D61 | **실제로 돈다** — `LedgerPaths`가 main에 있다 |
| 4 | 측정·순위 경로에서 `double`·`float` 금지 | §2.5·D115·D121 | 반례만 |

**규칙 4는 아직 잡을 코드가 없다.** 측정 경로가 비어 있어 공집합에 대해 통과한다 — 그 상태의 "통과"는 "아무것도 검사하지 않았다"와 구별되지 않는다. **G1에 core가 생기는 순간부터 실제로 돈다.** 규칙 1·2도 같은 처지다(정책·스캔 패키지가 아직 없다).

그래서 규칙마다 **일부러 어긴 반례**를 함께 둔다(`io.jqradar.arch.violations`). 테스트는 규칙마다 둘을 단언한다:

1. 우리 main 클래스에 걸면 통과한다
2. 반례 패키지에 걸면 **반드시 실패한다** — 실패 메시지에 반례 클래스 이름과 금지된 타입이 들어 있는지까지 본다

둘째가 없으면 첫째는 아무것도 증명하지 않는다. `contract/schema/`가 변조 케이스를 요구하는 논리와 같다(D124).

반례는 test 소스셋에만 있고, 그 사실 자체를 테스트가 단언한다(`violationExamplesNeverReachMain`) — 반례가 main으로 새면 우리 코드가 하드룰을 어긴 것이 된다.

## 범위 확인

규칙은 **모듈 여섯 전부**의 main 출력을 훑는다. `jqradar-core`의 test 태스크가 `-Djqradar.mainClassDirs`로 여섯 경로를 넘기고(컴파일 의존이 아니라 경로다 — 그래야 core가 cli·mcp를 의존하지 않는다), 테스트가 여섯이 모두 들어왔는지 단언한다. 하나라도 빠지면 그 모듈은 규칙 밖에 있게 되고 "통과했다"가 "검사하지 않았다"를 감춘다.

## 실행

```sh
./gradlew build          # 전체 — 컴파일 + ArchUnit 규칙 10개 테스트
./gradlew :jqradar-core:test
```
