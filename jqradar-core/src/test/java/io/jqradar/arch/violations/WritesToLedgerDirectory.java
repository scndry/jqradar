package io.jqradar.arch.violations;

import io.jqradar.ledger.LedgerPaths;
import java.nio.file.Path;

/** 규칙 3 위반 — 원장 모듈 밖에서 {@code .jqradar/} 경로를 만든다 (§5.5·D60·D61). */
public final class WritesToLedgerDirectory {

    /** scan 경로가 리포에 쓰기 시작하면 `.jqradar/`는 Terraform state가 된다(§12). */
    public Path eventFile(Path repositoryRoot) {
        return LedgerPaths.resolve(repositoryRoot, "events", "some-campaign");
    }
}
