package io.jqradar.arch.violations;

import org.eclipse.jgit.lib.PersonIdent;

/** 규칙 1 위반 — 정책 게이트 밖에서 저자 정체를 만진다 (§2.7·D48). */
public final class LeaksAuthorIdentity {

    /** 이름·이메일을 그대로 산출물 문자열로 낸다. 정확히 D48이 막는 것이다. */
    public String authorLine(PersonIdent ident) {
        return ident.getName() + " <" + ident.getEmailAddress() + ">";
    }
}
