package io.jqradar.ledger;

import java.nio.file.Path;

/**
 * {@code .jqradar/}가 스펠링되는 <b>유일한</b> 자리 (D60·D61).
 *
 * <p>원장의 사건 층만 리포에 쓴다. 일반 PR과 {@code scan}·{@code change}·{@code check}는
 * 아무것도 쓰지 않는다 — 그 성질이 깨지는 순간 {@code .jqradar/}는 Terraform state가 되고
 * 리포를 떠나야 한다(§5.5, §12).
 *
 * <p>이 타입이 존재하는 이유는 자체 ArchUnit 규칙이 붙을 자리를 주기 위해서다:
 * {@code io.jqradar.ledger} 밖의 어떤 클래스도 이것에 의존해서는 안 된다.
 * 문자열 리터럴은 ArchUnit이 볼 수 없지만 타입 의존은 볼 수 있다.
 *
 * <p>측정 코드가 아니다 — 경로 상수뿐이다(CLAUDE.md §3: G0 전에는 core 측정 코드를 쓰지 않는다).
 */
public final class LedgerPaths {

    /** 리포 안 원장 디렉터리. 커밋 대상이다(D60). */
    public static final String DIRECTORY = ".jqradar";

    private LedgerPaths() {
    }

    /** {@code .jqradar/} 아래 경로. 이 메서드를 부를 수 있는 것은 원장 모듈뿐이다. */
    public static Path resolve(Path repositoryRoot, String... segments) {
        Path path = repositoryRoot.resolve(DIRECTORY);
        for (String segment : segments) {
            path = path.resolve(segment);
        }
        return path;
    }
}
