package com.ohgiraffers.tomatolab_imean.common.ratelimit;

import java.lang.annotation.*;

/**
 * Rate Limiting 어노테이션
 * API 요청 횟수를 제한하여 브루트포스 공격과 서버 과부하를 방지합니다.
 * 
 * 사용 예시:
 * @RateLimit(requests = 5, window = "1m")  // 1분에 5번
 * @RateLimit(requests = 100, window = "1h") // 1시간에 100번
 */
@Target({ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface RateLimit {
    
    /**
     * 허용되는 최대 요청 횟수
     * @return 요청 횟수 (기본값: 10)
     */
    int requests() default 10;
    
    /**
     * 시간 윈도우 (기간)
     * 형식: 숫자 + 단위 (s: 초, m: 분, h: 시간, d: 일)
     * 예: "30s", "5m", "1h", "1d"
     * @return 시간 윈도우 문자열 (기본값: 1분)
     */
    String window() default "1m";
    
    /**
     * Rate Limit 키 생성 방식
     * @return RateLimitKeyType (기본값: IP 주소)
     */
    RateLimitKeyType keyType() default RateLimitKeyType.IP;
    
    /**
     * 제한 초과 시 반환할 오류 메시지
     * @return 오류 메시지
     */
    String message() default "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.";
    
    /**
     * Rate Limit 활성화 여부
     * 개발/테스트 환경에서 비활성화할 때 사용
     * @return true: 활성화, false: 비활성화 (기본값: true)
     */
    boolean enabled() default true;
}
