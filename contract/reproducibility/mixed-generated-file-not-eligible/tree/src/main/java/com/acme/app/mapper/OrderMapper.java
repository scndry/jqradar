package com.acme.app.mapper;

import com.acme.app.order.Order;
import javax.annotation.processing.Generated;

public class OrderMapper {
    public OrderDto toDto(Order order) {
        return new OrderDtoImpl(order.id());
    }
}

@Generated("mapstruct")
final class OrderDtoImpl implements OrderDto {
    private final long id;

    OrderDtoImpl(long id) {
        this.id = id;
    }

    public long id() {
        return id;
    }
}

interface OrderDto {
    long id();
}
