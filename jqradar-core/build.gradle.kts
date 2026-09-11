import java.io.File

// §4.1 jqradar-core — 측정(§2)·백분위(§2.5)·렌즈(§3)·변경 델타(§5.1)·재현 블록(§2.8)
// ·JSON 직렬화·인터랙티브 HTML 렌더러(§7.1)·적합성 픽스처 실행.
// **빌드 도구·IDE·LLM 무지.** 그래서 여기에는 gradleApi도 MCP도 없다.

dependencies {
    // 증인 셋(B.1). 네 번째 엔진을 추가하지 않는다(§11).
    api(libs.bundles.engines)

    // 규칙 3의 반례가 `LedgerPaths`를 참조해야 컴파일된다 — **test 전용** 의존이다.
    // main에서는 core가 ledger를 모른다(§4.1의 의존 방향: ledger -> core).
    testImplementation(project(":jqradar-ledger"))

    testImplementation(platform(libs.junit.bom))
    testImplementation(libs.junit.jupiter)
    testImplementation(libs.assertj)
    testRuntimeOnly(libs.junit.platform.launcher)
}

// d3는 Gradle 의존이 아니라 렌더러에 **인라인**되는 번들이다(§7.1 원칙 2:
// 자립형 단일 HTML, 네트워크 요청 0건). G2에 들어온다.

// 자체 ArchUnit 규칙(CLAUDE.md §3.5)이 **모든 모듈의 main 출력**을 훑는다.
// 컴파일 의존이 아니라 경로로 읽으므로 core가 다른 모듈을 의존하지 않는다.
val mainClassDirs = provider {
    rootProject.subprojects
        .mapNotNull { it.extensions.findByType<SourceSetContainer>()?.named("main")?.get() }
        .flatMap { it.output.classesDirs.files }
        .joinToString(File.pathSeparator) { it.absolutePath }
}

tasks.named<Test>("test") {
    dependsOn(rootProject.subprojects.map { "${it.path}:classes" })
    jvmArgumentProviders.add(CommandLineArgumentProvider {
        listOf("-Djqradar.mainClassDirs=" + mainClassDirs.get())
    })
}
