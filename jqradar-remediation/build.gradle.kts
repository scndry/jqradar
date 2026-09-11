// §4.1 jqradar-remediation — propose · apply · validate(§6.3).
// **L2 샌드박스 안에서만 실행된다**(§6.6). 컨테이너 런타임과 일시 jacoco는
// 런타임 환경이지 컴파일 의존이 아니다 — G3(§9 일정 W12–15)에 들어온다.

dependencies {
    implementation(project(":jqradar-core"))
    implementation(libs.rewrite.java)

    testImplementation(platform(libs.junit.bom))
    testImplementation(libs.junit.jupiter)
    testImplementation(libs.assertj)
    testRuntimeOnly(libs.junit.platform.launcher)
}
