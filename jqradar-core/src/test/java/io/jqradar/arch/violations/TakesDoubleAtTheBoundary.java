package io.jqradar.arch.violations;

import java.math.BigDecimal;

/**
 * 규칙 4 위반 — <b>경계로 들어오는</b> 이진 부동소수점 (§2.5·D115).
 *
 * <p>필드도 아니고 반환 타입도 아니고 박싱 클래스 의존도 아니다. 원시 {@code double}
 * 파라미터와 생성자 — 측정 경로에서 가장 흔한 경로다. 값이 이미 double로 들어오면
 * 안에서 {@code BigDecimal}로 감싸도 정밀도는 돌아오지 않는다.
 */
public final class TakesDoubleAtTheBoundary {

    /** 생성자 파라미터. {@code methods()}에는 잡히지 않는다. */
    public TakesDoubleAtTheBoundary(double seed) {
        // 계약은 정확 유리수를 요구한다. 여기서 이미 늦었다.
    }

    /** 반환은 BigDecimal인데 입력이 double이다. */
    public BigDecimal hotspot(double cxPct, double chgPct) {
        return BigDecimal.valueOf(100).multiply(
                BigDecimal.valueOf(Math.sqrt(cxPct * chgPct)));
    }

    /** float도 같다. */
    public BigDecimal quantile(float q) {
        return BigDecimal.valueOf(q);
    }
}
