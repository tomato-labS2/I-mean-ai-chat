package com.ohgiraffers.tomatolab_imean.auth.exception;

/**
 * 잘못된 JWT 토큰 예외 클래스
 * 토큰 형식이 올바르지 않거나 서명이 잘못되었을 때 발생
 */
public class InvalidTokenException extends JwtTokenException {
    
    /**
     * 기본 생성자
     */
    public InvalidTokenException() {
        super("유효하지 않은 토큰입니다.");
    }
    
    /**
     * 메시지를 포함한 생성자
     * @param message 예외 메시지
     */
    public InvalidTokenException(String message) {
        super(message);
    }
    
    /**
     * 메시지와 원인을 포함한 생성자
     * @param message 예외 메시지
     * @param cause 원인 예외
     */
    public InvalidTokenException(String message, Throwable cause) {
        super(message, cause);
    }
    
    /**
     * 원인만 포함한 생성자
     * @param cause 원인 예외
     */
    public InvalidTokenException(Throwable cause) {
        super("유효하지 않은 토큰입니다.", cause);
    }
    
    /**
     * 토큰 문제 타입을 명시하는 생성자
     * @param tokenProblem 토큰 문제 유형
     */
    public static InvalidTokenException malformedToken() {
        return new InvalidTokenException("토큰 형식이 올바르지 않습니다.");
    }
    
    public static InvalidTokenException invalidSignature() {
        return new InvalidTokenException("토큰 서명이 올바르지 않습니다.");
    }
    
    public static InvalidTokenException unsupportedToken() {
        return new InvalidTokenException("지원하지 않는 토큰 형식입니다.");
    }
    
    public static InvalidTokenException emptyToken() {
        return new InvalidTokenException("토큰이 비어있습니다.");
    }
}