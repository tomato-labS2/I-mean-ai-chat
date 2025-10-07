package com.ohgiraffers.tomatolab_imean.auth.exception;

/**
 * JWT 토큰 관련 기본 예외 클래스
 * 모든 JWT 관련 예외의 부모 클래스
 */
public class JwtTokenException extends RuntimeException {
    
    /**
     * 기본 생성자
     */
    public JwtTokenException() {
        super();
    }
    
    /**
     * 메시지를 포함한 생성자
     * @param message 예외 메시지
     */
    public JwtTokenException(String message) {
        super(message);
    }
    
    /**
     * 메시지와 원인을 포함한 생성자
     * @param message 예외 메시지
     * @param cause 원인 예외
     */
    public JwtTokenException(String message, Throwable cause) {
        super(message, cause);
    }
    
    /**
     * 원인만 포함한 생성자
     * @param cause 원인 예외
     */
    public JwtTokenException(Throwable cause) {
        super(cause);
    }
}