package io.jqradar.arch.violations;

/** 규칙 4 위반 — 측정·순위 경로에서 이진 부동소수점을 쓴다 (§2.5·D115). */
public final class RanksWithBinaryFloatingPoint {

    /** 필드부터 double이다. */
    private double percentile;

    /** 반환 타입도 double. */
    public double hotspot(double cxPct, double chgPct) {
        return 100.0 * Math.sqrt(cxPct * chgPct);
    }

    /** 박싱된 것도 같다. */
    public Double quantile(Float q) {
        // 계약의 픽스처 예: [1..9,100], q=0.9 -> 18.1.
        // 아래 식을 double로 평가하면 18.099999999999966이 나온다.
        double h = 1 + q * 9;
        return 9 + (h - 9) * 91;
    }

    public void setPercentile(double value) {
        this.percentile = value;
    }
}
