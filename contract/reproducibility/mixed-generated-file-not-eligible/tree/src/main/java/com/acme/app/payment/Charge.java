package com.acme.app.payment;

// @javax.annotation.Generated 아님 — 손으로 쓴 파일이다.
/** {@code @javax.annotation.processing.Generated}가 붙은 클래스와 짝을 이루지 않는다. */
public class Charge {
    static final String NOTE = "@javax.annotation.Generated";

    public long fee(long amount) {
        return amount / 100;
    }
}
