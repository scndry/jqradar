// §4.1 jqradar-gradle-plugin — jqradarScan · jqradarChange · jqradarCheck(**유일하게
// 빌드를 깰 수 있음**) · jqradarReport · jqradarCampaign · jqradarLedger.
// 확장 블록 없음 — 태스크 옵션만(§4.3 제로 설정).

plugins {
    `java-gradle-plugin`
}

dependencies {
    implementation(project(":jqradar-core"))
    implementation(project(":jqradar-ledger"))

    testImplementation(platform(libs.junit.bom))
    testImplementation(libs.junit.jupiter)
    testImplementation(libs.assertj)
    testRuntimeOnly(libs.junit.platform.launcher)
}

gradlePlugin {
    plugins.register("jqradar") {
        id = "io.jqradar"
        // 구현은 G2(§9 일정 W8–10). configuration cache는 P10이 잰다.
        implementationClass = "io.jqradar.gradleplugin.JqradarPlugin"
    }
}
