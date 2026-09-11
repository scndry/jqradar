// §4.1 jqradar-ledger — 얇은 모듈. campaign create|close|reanchor, claim,
// 원장 뷰 = 파생(앵커·HEAD 스캔) ⊕ 사건(.jqradar/events/), 한정 blame 1회(§5.6).
// **코드 상태는 저장하지 않는다**(D55). `.jqradar/`에 쓰는 **유일한** 모듈이다(D60·D61).

dependencies {
    api(project(":jqradar-core"))
    api(libs.jgit)

    testImplementation(platform(libs.junit.bom))
    testImplementation(libs.junit.jupiter)
    testImplementation(libs.assertj)
    testRuntimeOnly(libs.junit.platform.launcher)
}
