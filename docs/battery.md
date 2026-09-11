# 배터리 리포 — 확정 (§9, G0 체크리스트 #7)

**나이·크기로만 고른다.** AI 사용 여부로 고르지 않는다 — 선택 효과가 들어간다(§9). 스타 수·인기도 역시 선정 기준이 아니고, 아래 표에서 후보를 찾을 때만 썼다.

**측정 시각**: 2026-09-11 · **측정 방법**: [`battery-measure.sh`](battery-measure.sh) (GitHub API만, clone 없음)

```sh
sh docs/battery-measure.sh apache/commons-lang spring-projects/spring-framework …
```

> **`loc`은 여기 없다.** §2.1의 `loc`은 NCSS이고 PMD만 계산할 수 있다. 아래의 **Java KB**는 GitHub languages API의 실측 바이트이고, LOC은 배터리 실행 시점에 도구 자신이 낸다. 지금 LOC을 적으면 그것은 재계산할 수 없는 숫자다(B.4).
>
> **머지 비율은 최근 100커밋 표본**이다. 리포 전체가 아니다 — 정책이 바뀐 리포는 옛 구간이 다를 수 있고, 그 차이 자체가 P2가 보려는 것이다.

---

## 확정 목록

### 노년 (15년+) — P5·P11·옛 커밋 빌드의 혹독한 시험대

| 리포 | 생성 | 나이 | 빌드 | 커밋 | 머지/100 | Java KB | Kotlin KB |
|---|---|---|---|---|---|---|---|
| `apache/commons-lang` | 2009-05-21 | 17.3년 | **Maven** | 9,796 | **0** | 8,388 | 0 |
| `spring-projects/spring-framework` | 2010-12-08 | 15.8년 | Gradle | 35,560 | **30** | 50,354 | 1,171 |
| `netty/netty` | 2010-11-09 | 15.8년 | **Maven** | 14,409 | **0** | 24,394 | 0 |
| `elastic/elasticsearch` | 2010-02-08 | 16.6년 | Gradle | 105,587 | **0** | 278,768 | 0 |

### 중년 (5–12년) — P2·스쿼시 정책 비교

| 리포 | 생성 | 나이 | 빌드 | 커밋 | 머지/100 | Java KB | Kotlin KB |
|---|---|---|---|---|---|---|---|
| `micronaut-projects/micronaut-core` | 2018-03-07 | 8.5년 | Gradle | 16,669 | 1 | 18,290 | 1,112 |
| `NationalSecurityAgency/ghidra` | 2019-03-01 | 7.5년 | Gradle | 18,399 | **48** | (Java 85%) | 0 |
| `halo-dev/halo` | 2018-03-21 | 8.5년 | Gradle | 6,305 | **0** | (Java 47%) | 0 |

### 청년 (≤3년) — §9의 선정 조건: GitHub 생성일 · Java · Gradle · 500+ 커밋

| 리포 | 생성 | 나이 | 빌드 | 커밋 | 머지/100 | 조건 충족 |
|---|---|---|---|---|---|---|
| `conductor-oss/conductor` | 2023-12-08 | 2.8년 | Gradle | 6,039 | 13 | 넷 다 ✅ |

### Kotlin 혼합 1개

| 리포 | 생성 | 나이 | 빌드 | 커밋 | 머지/100 | Java KB | Kotlin KB |
|---|---|---|---|---|---|---|---|
| `apple/pkl` | 2024-01-19 | 2.6년 | **Gradle(kts)** | 895 | 0 | 3,700 | 1,647 |

Kotlin 비중이 28%로 가장 실질적이다. `cx`가 들여쓰기 복잡도로 갈리고 백분위가 언어별 모집단으로 나뉘는 것(§2.5·D12), `smells`가 `null`이 되는 것(§4.4)을 실제로 밟는다. O11(언어별 `interpretation` 임계)의 관찰 대상이기도 하다.

### 스쿼시·선형 이력 리포 1개

`apache/commons-lang` — 최근 100커밋에 머지 **0**. 대조군은 `spring-projects/spring-framework`(머지 **30**)와 `NationalSecurityAgency/ghidra`(머지 **48**).

이 대비가 P2가 필요로 하는 것이다: §2.7이 머지 커밋을 제외하므로 선형 이력 리포에서는 `chg_commits`가 PR 단위가 아니라 커밋 단위가 되고, `chg_days`와의 관계도 달라진다. O4(스쿼시 리포 PR 그룹핑)의 자료다.

### 합성 리포 둘 — 우리가 만든다

| 리포 | 무엇 | 어디 | 언제 |
|---|---|---|---|
| 깊은 기업형 패키지 | `component.strategy=auto`가 최장 공통 접두어 아래에서 의미 있는 컴포넌트를 내는지(P8) | `contract/graph/` | G1 |
| 악성 픽스처 | L1′ 파서 방어와 L2 샌드박스 벡터(P9) | `contract/security/` | G3 |

둘 다 GitHub에서 고르지 않는다 — 조건을 정확히 갖춘 리포가 없고, 있어도 그 조건이 우리가 통제하는 변수여야 한다.

### 내부자 데이터 — 배터리가 아니다

**이 리포(`scndry/jqradar`)는 S1(§9 일정 G1) 이후 내부자 데이터로 병기한다.** 배터리를 대체하지 않는다(D84).

자기 적용은 필요하지만 충분하지 않다 — 자기 맹점은 자기 적용으로 드러나지 않는다(Thompson, Trusting Trust). 우리 리포의 수치는 P1a·P2 같은 검증에 증거로 쓰되 **"내부자 데이터"로 표시**하고, 배터리 리포의 자리를 채우는 데 쓰지 않는다.

---

## §9와 어긋난 것 — 측정이 분류를 뒤집었다

§9는 **Netty·Elasticsearch를 중년(5–12년)** 으로 적는다. 측정하면 아니다:

| 리포 | §9의 분류 | 측정한 나이 | 실제 |
|---|---|---|---|
| `netty/netty` | 중년(5–12년) | **15.8년** | 노년 |
| `elastic/elasticsearch` | 중년(5–12년) | **16.6년** | 노년 |
| `micronaut-projects/micronaut-core` | 중년(5–12년) | 8.5년 | ✅ 중년 |

두 리포가 2010년생이라 spring-framework(2010-12)와 같은 세대다. §9의 버킷이 쓰일 당시에는 맞았을 수 있으나 지금은 아니다.

**처치**: 둘을 노년으로 옮기고 중년 자리를 `ghidra`(7.5년)·`halo`(8.5년)로 채웠다. 둘 다 Gradle이고 커밋 수가 충분하며, 머지 정책이 48%와 0%로 갈려 P2의 대비를 중년 버킷 안에서도 만든다.

**이것은 계약 충돌이 아니라 문서의 노후다.** §9의 버킷 정의(나이 구간)는 그대로 두고 그 안의 이름만 측정에 맞췄다. `prd.md` 수정이 필요한지는 소유자의 판단이다 — 이 PR에서는 고치지 않았다.

또 하나: §9는 노년 후보로 commons-lang·spring-framework를 들지만 **`commons-lang`과 `netty`는 Maven이다.** §4.4가 "스캔·변경·원장은 Gradle·Maven 모두"라 배터리 자격에는 문제가 없고, **L2 검증(G3, P5)은 Gradle 1차**이므로 그 단계에서는 Gradle 리포만 대상이 된다(O12에서 Maven).

## 확정 요약

| 버킷 | 리포 | 빌드 |
|---|---|---|
| 노년 15년+ | commons-lang · spring-framework · netty · elasticsearch | Maven · Gradle · Maven · Gradle |
| 중년 5–12년 | micronaut-core · ghidra · halo | Gradle ×3 |
| 청년 ≤3년 | conductor | Gradle |
| Kotlin 혼합 | pkl | Gradle(kts) |
| 선형 이력 | commons-lang (대조: spring-framework, ghidra) | — |
| 합성 | 깊은 패키지(P8, G1) · 악성(P9, G3) | 우리가 만든다 |
| 내부자 | scndry/jqradar (S1 이후, 배터리 아님) | Gradle |

**빌드 가능 여부는 아직 확인하지 않았다.** 위 표의 "빌드"는 루트의 빌드 파일로 판정한 빌드 **시스템**이지 "우리 환경에서 빌드된다"가 아니다. 클래스 루트가 있어야 ArchUnit 렌즈가 돌므로(§2.2 `bytecode_scope`) 배터리 A(G1) 착수 전에 리포별로 실제 빌드를 확인하고 이 문서에 열을 추가한다. 옛 커밋 빌드는 노년 리포에서 특히 어렵고, 그것이 §9가 그 셋을 "P5·P11의 혹독한 시험대"라 부른 이유다.
