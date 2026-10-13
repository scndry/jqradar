package com.acme.app.order;

public class Order {
    private final long id;

    public Order(long id) {
        this.id = id;
    }

    public long id() {
        return id;
    }
}
