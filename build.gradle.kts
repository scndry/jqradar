// 루트는 공통 규약만 진다. 측정 코드는 G0에서 쓰지 않는다(CLAUDE.md §3).

plugins {
    base
}

subprojects {
    apply(plugin = "java-library")

    group = "io.jqradar"
    version = "0.0.0-G0"

    extensions.configure<JavaPluginExtension> {
        toolchain {
            // CLAUDE.md §4 — Java 21. `classes_reproduction_inputs.jdk`가 이 값을 인쇄한다(§2.8).
            languageVersion.set(JavaLanguageVersion.of(21))
        }
    }

    tasks.withType<JavaCompile>().configureEach {
        // -parameters는 §7 예시의 classes_reproduction_inputs.compiler_args와 같다.
        options.compilerArgs.addAll(listOf("-parameters", "-Xlint:all"))
        options.encoding = "UTF-8"
    }

    tasks.withType<Test>().configureEach {
        useJUnitPlatform()
        testLogging { events("failed") }
    }

    tasks.withType<AbstractArchiveTask>().configureEach {
        // 재현 가능한 빌드 — 같은 입력이면 같은 바이트(§2.9 reproducibility/).
        isPreserveFileTimestamps = false
        isReproducibleFileOrder = true
    }
}
