package io.jqradar.arch;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.fields;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.methods;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.lang.CompositeArchRule;

/**
 * 자체 ArchUnit 규칙 — <b>우리 코드에만</b> 적용된다 (CLAUDE.md §3.5).
 *
 * <p>이것은 대상 코드를 재는 렌즈(§3)가 아니라 우리 자신의 하드룰(§2)을 구조로 막는 장치다.
 * jQRadar는 jQRadar로 만든다(B.7) — 남에게 요구하는 비용을 우리가 먼저 낸다.
 *
 * <p><b>규칙마다 적용 범위를 인자로 받는다.</b> 그래야 같은 규칙을 (1) 우리 main 클래스에
 * 걸어 통과를 보이고 (2) 일부러 위반하는 예제 패키지에 걸어 <i>실제로 잡는지</i>를 보일 수
 * 있다. 통과만 하는 규칙은 아무것도 지키지 않는다 — {@code contract/schema/}의 변조 케이스와
 * 같은 논리다(D124).
 *
 * <p>ArchUnit의 동결(freeze)을 쓰지 않는다. 동결은 기존 위반을 등록해 두고 늘지만 않게
 * 하는 장치인데, 우리에겐 등록할 기존 위반이 없고(코드가 아직 없다) 브라운필드 등록은
 * 우리 도구가 캠페인으로 하는 일이다(§5.4) — 빌드 도구가 대신할 자리가 아니다.
 */
public final class JqradarArchRules {

    private JqradarArchRules() {
    }

    // ------------------------------------------------------------------
    // 1. 정체는 산출물로 나가지 않는다 (D48·D108, §2.7)
    // ------------------------------------------------------------------

    /**
     * {@code PersonIdent}의 이름·이메일은 {@code people} 정책이 사는 패키지 안에서만 읽는다.
     *
     * <p>§2.7: 저자 필드는 <i>읽되 정체는 프로세스 밖으로 내지 않는다.</i> 기본
     * ({@code people.attribution=off})은 메모리에서 해시로 세어 익명 집계만 내고 해시도
     * 저장하지 않는다. {@code individual}일 때만 저자 사실이 실행 산출물에 나가며, 그
     * 판단은 조직의 정책이다(B.6, D11).
     *
     * <p>구조로 옮기면: 정책 게이트가 사는 한 패키지 밖에서는 {@code PersonIdent}를 아예
     * 만지지 않는다. 게이트를 우회할 경로를 남기지 않기 위해서다.
     *
     * @param peoplePolicyPackage 정책 게이트가 사는 패키지 (예: {@code io.jqradar.core.people..})
     * @param scope               규칙을 적용할 범위
     */
    public static ArchRule personIdentOnlyBehindPeoplePolicy(
            String peoplePolicyPackage, String... scope) {
        return noClasses()
                .that().resideInAnyPackage(scope)
                .and().resideOutsideOfPackage(peoplePolicyPackage)
                .should().dependOnClassesThat()
                .haveFullyQualifiedName("org.eclipse.jgit.lib.PersonIdent")
                .because("§2.7·D48 — 저자 정체는 " + peoplePolicyPackage
                        + " 의 정책 게이트를 거치지 않고는 산출물로 나갈 수 없다. "
                        + "AI/사람 추론 금지와 개인 순위 표면 금지도 같은 선이다");
    }

    // ------------------------------------------------------------------
    // 2. 매 스캔 blame 금지 (D18·D113, §2.7)
    // ------------------------------------------------------------------

    /**
     * {@code scan}·{@code change} 경로에 {@code BlameCommand}가 없다.
     *
     * <p>blame의 유일한 예외는 캠페인 생성 시 1회, 원장 finding 영역에 한정해서다(§5.6, D57).
     * "한 번만"이 "가끔"이 되고 "매 스캔"이 되는 압력은 §12가 명시한 위험이고, 이 규칙이
     * 그 선이다. 같은 선을 {@code contract/history/}의 픽스처가 값 쪽에서 지킨다(D113).
     */
    public static ArchRule noBlameOnScanOrChangePath(String... scope) {
        return noClasses()
                .that().resideInAnyPackage(scope)
                .should().dependOnClassesThat()
                .haveFullyQualifiedName("org.eclipse.jgit.api.BlameCommand")
                .because("§2.7·D18 — 매 스캔 blame은 P7 예산을 깨고, 예외는 캠페인 생성 1회뿐이다(§5.6·D57)");
    }

    // ------------------------------------------------------------------
    // 3. .jqradar/ 쓰기는 jqradar-ledger만 (D60·D61)
    // ------------------------------------------------------------------

    /**
     * {@code .jqradar/} 경로를 만드는 자리는 {@code LedgerPaths} 하나뿐이고, 그것에
     * 의존할 수 있는 것은 원장 모듈뿐이다.
     *
     * <p>ArchUnit은 문자열 리터럴을 보지 못하므로 경로를 <b>타입</b>으로 봉한다 —
     * {@code LedgerPaths}가 존재하는 이유가 그것이다. 일반 PR과 {@code scan}·
     * {@code change}·{@code check}는 아무것도 쓰지 않는다(D61): 그 성질(작고, 머지 뒤
     * 불변, PR당 하나)이 깨지는 순간 {@code .jqradar/}는 Terraform state가 되고 리포를
     * 떠나야 한다(§5.5, §12).
     */
    public static ArchRule dotJqradarWritesOnlyInLedger(String ledgerPackage, String... scope) {
        return noClasses()
                .that().resideInAnyPackage(scope)
                .and().resideOutsideOfPackage(ledgerPackage)
                .should().dependOnClassesThat()
                .haveFullyQualifiedName("io.jqradar.ledger.LedgerPaths")
                .because("§5.5·D60·D61 — 리포에 쓰는 것은 캠페인 관리와 finding을 겨눈 수정 PR뿐이고, "
                        + "그 쓰기는 " + ledgerPackage + " 안에서만 일어난다");
    }

    // ------------------------------------------------------------------
    // 4. 측정·순위 경로에서 double·float 금지 (D115·D121, §2.5 산술 계약)
    // ------------------------------------------------------------------

    /**
     * 측정·순위 경로에 이진 부동소수점이 없다.
     *
     * <p>§2.5 산술 계약: 순위·분위·모든 임계 비교는 <b>반올림 전 정확값</b>으로 판정한다
     * (Java: {@code BigInteger} 분수 또는 유한 {@code BigDecimal}). 이유는 계약 자신의
     * 픽스처가 증명한다 — {@code [1..9,100]}의 P90은 계약이 {@code 18.1}이라 적었는데
     * IEEE-754 {@code double}로 같은 식을 평가하면 {@code 18.099999999999966}이 나온다.
     *
     * <p>무리수는 <b>크기 출력에만</b>: 렌즈의 {@code sqrt}는 유리수로 닫히지 않으므로
     * 순위는 {@code pct × pct}의 정확 비교로 내고, {@code √}는 표시할 값에만
     * {@code BigDecimal.sqrt(MathContext(34, HALF_EVEN))}으로 계산한다. composite는
     * {@code √}를 산술 입력으로 쓰므로 34자리 값으로 가중합한 뒤 <b>한 번만</b> 반올림한다(D121).
     *
     * <p><b>지금은 잡을 코드가 없다.</b> G0의 모듈은 소스셋이 비어 있어 이 규칙은 공집합에
     * 대해 통과한다. 아래 위반 예제가 규칙이 살아 있음을 보이고, G1에 core가 생기는 순간부터
     * 실제로 돈다.
     */
    public static ArchRule noBinaryFloatingPointOnMeasureOrRankPath(String... scope) {
        String why = "§2.5·D115 — 순위·분위·임계 비교는 정확 유리수로. "
                + "IEEE-754는 계약 자신의 픽스처(P90 = 18.1)를 재현하지 못한다";

        ArchRule noFields = fields()
                .that().areDeclaredInClassesThat().resideInAnyPackage(scope)
                .should().notHaveRawType(double.class)
                .andShould().notHaveRawType(float.class)
                .andShould().notHaveRawType(Double.class)
                .andShould().notHaveRawType(Float.class)
                .because(why)
                .allowEmptyShould(true);

        ArchRule noReturns = methods()
                .that().areDeclaredInClassesThat().resideInAnyPackage(scope)
                .should().notHaveRawReturnType(double.class)
                .andShould().notHaveRawReturnType(float.class)
                .andShould().notHaveRawReturnType(Double.class)
                .andShould().notHaveRawReturnType(Float.class)
                .because(why)
                .allowEmptyShould(true);

        ArchRule noBoxedDependency = noClasses()
                .that().resideInAnyPackage(scope)
                .should().dependOnClassesThat().belongToAnyOf(Double.class, Float.class)
                .because(why)
                .allowEmptyShould(true);

        return CompositeArchRule.of(noFields).and(noReturns).and(noBoxedDependency);
    }
}
