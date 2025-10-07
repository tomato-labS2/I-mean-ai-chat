package com.ohgiraffers.tomatolab_imean.common.ratelimit;

/**
 * Rate Limit 키 생성 방식을 정의하는 열거형
 */
public enum RateLimitKeyType {
    
    /**
     * IP 주소 기반 제한
     * 같은 IP에서 오는 모든 요청에 대해 제한 적용
     * 예: "192.168.1.100"
     */
    IP,
    
    /**
     * 사용자 기반 제한
     * 로그인한 사용자별로 제한 적용
     * 예: 회원 코드 "MEMBER_001"
     */
    USER,
    
    /**
     * IP + 사용자 조합 기반 제한
     * IP와 사용자를 조합하여 더 세밀한 제한
     * 예: "192.168.1.100:MEMBER_001"
     */
    IP_AND_USER,
    
    /**
     * 글로벌 제한
     * 모든 요청에 대해 전역적으로 제한 적용
     * 예: "GLOBAL"
     */
    GLOBAL
}
