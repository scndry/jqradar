rootProject.name = "jqradar"

// §4.1의 모듈 여섯. 더 늘리지 않는다 — 책임이 늘면 §4.1을 먼저 고친다.
include(
    "jqradar-core",
    "jqradar-cli",
    "jqradar-gradle-plugin",
    "jqradar-ledger",
    "jqradar-mcp",
    "jqradar-remediation",
)

dependencyResolutionManagement {
    repositories { mavenCentral() }
}
