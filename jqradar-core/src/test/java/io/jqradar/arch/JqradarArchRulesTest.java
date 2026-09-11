package io.jqradar.arch;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

/**
 * 자체 ArchUnit 규칙이 (1) 우리 코드에서 통과하고 (2) <b>일부러 어긴 예제를 실제로 잡는지</b>를
 * 함께 본다 (CLAUDE.md §3.5).
 *
 * <p>둘째가 없으면 첫째는 아무것도 증명하지 않는다. G0의 모듈은 소스셋이 거의 비어 있어
 * 모든 규칙이 공집합에 대해 통과하기 때문이다 — 그 상태에서 "통과했다"는 말은
 * "아무것도 검사하지 않았다"와 구별되지 않는다. {@code contract/schema/}가 변조 케이스를
 * 요구하는 이유와 같다(D124).
 */
@DisplayName("자체 ArchUnit 규칙 (CLAUDE.md §3.5)")
class JqradarArchRulesTest {

    /** 우리 코드 전체. {@code jqradar-core}의 test 태스크가 모든 모듈의 main 출력을 넘긴다. */
    private static final JavaClasses OUR_MAIN_CLASSES = importMainClasses();

    /** 일부러 어긴 예제들. main이 아니라 이 test 소스셋에만 있다. */
    private static final JavaClasses VIOLATION_EXAMPLES =
            new ClassFileImporter().importPackages("io.jqradar.arch.violations");

    private static final String ALL_OURS = "io.jqradar..";
    private static final String VIOLATIONS = "io.jqradar.arch.violations..";
    private static final String PEOPLE_POLICY = "io.jqradar.core.people..";
    private static final String LEDGER = "io.jqradar.ledger..";

    /**
     * §4.1의 모듈 여섯의 main 출력을 경로로 읽는다. <b>컴파일 의존이 아니다</b> —
     * core가 cli·mcp를 의존하면 §4.1의 모듈 경계가 뒤집힌다.
     */
    private static JavaClasses importMainClasses() {
        String dirs = System.getProperty("jqradar.mainClassDirs", "");
        List<Path> paths = Arrays.stream(dirs.split(java.io.File.pathSeparator))
                .filter(s -> !s.isBlank())
                .map(Path::of)
                .filter(java.nio.file.Files::isDirectory)
                .collect(Collectors.toList());
        // test 클래스는 절대 섞지 않는다 — 위반 예제가 우리 코드로 둔갑한다.
        ImportOption noTests = location -> !location.contains("/test/");
        return new ClassFileImporter().withImportOption(noTests).importPaths(paths);
    }

    @Test
    @DisplayName("모든 모듈의 main 출력을 실제로 읽는다 — 빈 입력에 대한 통과를 통과로 세지 않기 위해")
    void importsEveryModuleMainOutput() {
        String dirs = System.getProperty("jqradar.mainClassDirs", "");
        assertThat(dirs)
                .as("jqradar-core의 test 태스크가 -Djqradar.mainClassDirs를 넘겨야 한다")
                .isNotBlank();

        // §4.1의 모듈 여섯이 **전부** 범위에 있어야 한다. 하나라도 빠지면 그 모듈은
        // 규칙 밖에 있게 되고, "통과했다"가 "검사하지 않았다"를 감춘다.
        assertThat(dirs).as("§4.1 모듈 여섯의 main 출력").contains(
                "jqradar-core", "jqradar-cli", "jqradar-gradle-plugin",
                "jqradar-ledger", "jqradar-mcp", "jqradar-remediation");

        // G0에서 main에 있는 것은 LedgerPaths 하나다(경로 상수 — 측정 코드가 아니다).
        // 비어 있으면 규칙 셋이 공집합에 대해 통과해 버린다.
        assertThat(OUR_MAIN_CLASSES).as("G0의 main 클래스").isNotEmpty();
    }

    @Nested
    @DisplayName("1. 저자 정체는 people 정책 밖으로 나가지 않는다 (§2.7·D48·D108)")
    class PersonIdentRule {

        @Test
        @DisplayName("우리 코드는 지킨다")
        void ourCodePasses() {
            JqradarArchRules
                    .personIdentOnlyBehindPeoplePolicy(PEOPLE_POLICY, ALL_OURS)
                    .allowEmptyShould(true)
                    .check(OUR_MAIN_CLASSES);
        }

        @Test
        @DisplayName("어기면 잡는다 — PersonIdent.getName()/getEmailAddress()를 그대로 낸다")
        void catchesViolation() {
            assertThatThrownBy(() -> JqradarArchRules
                    .personIdentOnlyBehindPeoplePolicy(PEOPLE_POLICY, VIOLATIONS)
                    .check(VIOLATION_EXAMPLES))
                    .isInstanceOf(AssertionError.class)
                    .hasMessageContaining("LeaksAuthorIdentity")
                    .hasMessageContaining("PersonIdent");
        }
    }

    @Nested
    @DisplayName("2. scan/change 경로에 blame이 없다 (§2.7·D18·D113)")
    class BlameRule {

        @Test
        @DisplayName("우리 코드는 지킨다")
        void ourCodePasses() {
            JqradarArchRules
                    .noBlameOnScanOrChangePath(ALL_OURS)
                    .allowEmptyShould(true)
                    .check(OUR_MAIN_CLASSES);
        }

        @Test
        @DisplayName("어기면 잡는다 — git.blame()")
        void catchesViolation() {
            assertThatThrownBy(() -> JqradarArchRules
                    .noBlameOnScanOrChangePath(VIOLATIONS)
                    .check(VIOLATION_EXAMPLES))
                    .isInstanceOf(AssertionError.class)
                    .hasMessageContaining("BlamesOnEveryScan")
                    .hasMessageContaining("BlameCommand");
        }
    }

    @Nested
    @DisplayName("3. .jqradar/ 쓰기는 jqradar-ledger만 (§5.5·D60·D61)")
    class LedgerWriteRule {

        @Test
        @DisplayName("우리 코드는 지킨다 — LedgerPaths는 원장 안에서만 쓰인다")
        void ourCodePasses() {
            JqradarArchRules
                    .dotJqradarWritesOnlyInLedger(LEDGER, ALL_OURS)
                    .allowEmptyShould(true)
                    .check(OUR_MAIN_CLASSES);
        }

        @Test
        @DisplayName("어기면 잡는다 — 원장 밖에서 LedgerPaths.resolve()")
        void catchesViolation() {
            assertThatThrownBy(() -> JqradarArchRules
                    .dotJqradarWritesOnlyInLedger(LEDGER, VIOLATIONS)
                    .check(VIOLATION_EXAMPLES))
                    .isInstanceOf(AssertionError.class)
                    .hasMessageContaining("WritesToLedgerDirectory")
                    .hasMessageContaining("LedgerPaths");
        }
    }

    @Nested
    @DisplayName("4. 측정·순위 경로에서 double·float 금지 (§2.5·D115·D121)")
    class BinaryFloatingPointRule {

        /**
         * G0에는 잡을 코드가 없다 — 측정 경로가 아직 비어 있다. 이 테스트가 지금 증명하는
         * 것은 "규칙이 공집합에서 통과한다"뿐이고, 규칙이 살아 있다는 증명은 아래
         * {@link #catchesViolation()}가 진다. G1에 core가 생기는 순간부터 실제로 돈다.
         */
        @Test
        @DisplayName("우리 코드는 지킨다 (G0에서는 공집합 — 규칙이 산다는 증명은 아래가 진다)")
        void ourCodePasses() {
            JqradarArchRules
                    .noBinaryFloatingPointOnMeasureOrRankPath(ALL_OURS)
                    .check(OUR_MAIN_CLASSES);
        }

        @Test
        @DisplayName("어기면 잡는다 — double 필드·반환 타입·박싱")
        void catchesViolation() {
            assertThatThrownBy(() -> JqradarArchRules
                    .noBinaryFloatingPointOnMeasureOrRankPath(VIOLATIONS)
                    .check(VIOLATION_EXAMPLES))
                    .isInstanceOf(AssertionError.class)
                    .hasMessageContaining("RanksWithBinaryFloatingPoint");
        }
    }

    @Test
    @DisplayName("위반 예제는 main 소스셋에 없다 — 반례가 우리 코드로 둔갑하면 안 된다")
    void violationExamplesNeverReachMain() {
        assertThat(OUR_MAIN_CLASSES.stream()
                .anyMatch(c -> c.getPackageName().startsWith("io.jqradar.arch.violations")))
                .as("io.jqradar.arch.violations는 test 소스셋에만 있어야 한다")
                .isFalse();
        assertThat(VIOLATION_EXAMPLES).as("반례 네 종 + package-info").isNotEmpty();
    }
}
