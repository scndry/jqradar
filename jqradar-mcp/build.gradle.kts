// §4.1 jqradar-mcp — MCP 서버 = Claude 플러그인. 툴 7종(§6.2).
// LLM에는 발견 관련 소스 **조각**·지표·컴포넌트 맥락만(§6.6 신뢰 경계).
// PR 토큰은 이 서버가 보유하며 권한은 브랜치 생성 + PR 생성만(최소 권한).

dependencies {
    implementation(project(":jqradar-core"))
    implementation(project(":jqradar-ledger"))
    implementation(project(":jqradar-remediation"))

    testImplementation(platform(libs.junit.bom))
    testImplementation(libs.junit.jupiter)
    testImplementation(libs.assertj)
    testRuntimeOnly(libs.junit.platform.launcher)
}
