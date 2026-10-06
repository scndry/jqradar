package io.jqradar.arch.violations;

import com.tngtech.archunit.library.metrics.ComponentDependencyMetrics;
import java.math.BigDecimal;

/**
 * 규칙 4 위반 — ArchUnit {@code ArchitectureMetrics}의 {@code double} 반환 메서드를 호출한다 (D179).
 *
 * <p>시그니처에도 필드에도 {@code double}이 없다 — {@code BigDecimal}로 감싸 돌려준다. 그래서
 * 규칙 4의 앞 세 부분(필드·시그니처·박싱 의존)은 이 클래스를 통과시킨다. 정밀도는 이미
 * 라이브러리 안에서 잃었다: ArchUnit은 {@code Ce/(Ca+Ce)}를 {@code double}로 나누고 0/0에
 * 1.0을 준다. 받아야 할 것은 정수(Ca·Ce)이고 비율은 우리 산술이다(§2.2, D179·D180).
 */
public final class CallsArchUnitDoubleMetrics {

    /** 반환은 BigDecimal인데 안에서 double 반환 메서드를 호출한다. */
    public BigDecimal instability(ComponentDependencyMetrics metrics, String component) {
        return BigDecimal.valueOf(metrics.getInstability(component));
    }
}
