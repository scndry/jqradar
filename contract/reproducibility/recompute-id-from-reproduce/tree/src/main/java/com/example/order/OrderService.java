package com.example.order;

public class OrderService {
    public int total(int[] lines) {
        int sum = 0;
        for (int line : lines) {
            if (line > 0) {
                sum += line;
            }
        }
        return sum;
    }
}
