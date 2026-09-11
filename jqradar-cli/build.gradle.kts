// §4.1 jqradar-cli — .git 상향 탐색, 소스·클래스 루트 자동 발견,
// scan · change · check · report · campaign · ledger. exit: scan/change 0/2, check 0/1/2.

dependencies {
    implementation(project(":jqradar-core"))
    implementation(project(":jqradar-ledger"))

    testImplementation(platform(libs.junit.bom))
    testImplementation(libs.junit.jupiter)
    testImplementation(libs.assertj)
    testRuntimeOnly(libs.junit.platform.launcher)
}
