package io.jqradar.arch.violations;

import org.eclipse.jgit.api.BlameCommand;
import org.eclipse.jgit.api.Git;

/** 규칙 2 위반 — scan 경로에서 blame을 부른다 (§2.7·D18). */
public final class BlamesOnEveryScan {

    /** 매 스캔 blame. P7 예산을 깨고 D18이 막는 자리다. */
    public BlameCommand blameFor(Git git, String path) {
        return git.blame().setFilePath(path);
    }
}
