package com.example.order;

public final class OrderPolicy {
    public boolean allows(int amount) {
        return amount >= 0 && amount < 10_000;
    }
}
