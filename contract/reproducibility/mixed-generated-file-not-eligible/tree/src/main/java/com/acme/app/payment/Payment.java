package com.acme.app.payment;

import javax.annotation.processing.Generated;

public class Payment {
    private final long amount;

    public Payment(long amount) {
        this.amount = amount;
    }

    @Generated("ide")
    @Override
    public int hashCode() {
        return Long.hashCode(amount);
    }
}
