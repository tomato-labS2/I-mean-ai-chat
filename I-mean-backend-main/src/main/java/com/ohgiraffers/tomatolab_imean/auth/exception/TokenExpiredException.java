package com.ohgiraffers.tomatolab_imean.auth.exception;

/**
 * JWT 토큰 만료 예외 클래스
 * Access Token 또는 Refresh Token이 만료되었을 때 발생
 */
public class TokenExpiredException extends JwtTokenException {
    
    /**
     * 기본 생성자
     */
    public TokenExpiredException() {
        super("토큰이 만료되었습니다.");
    }
    
    /**
     * 메시지를 포함한 생성자
     * @param message 예외 메시지
     */
    public TokenExpiredException(String message) {
        super(message);
    }
    
    /**
     * 메시지와 원인을 포함한 생성자
     * @param message 예외 메시지
     * @param cause 원인 예외
     */
    public TokenExpiredException(String message, Throwable cause) {
        super(message, cause);
    }
    
    /**
     * 토큰 타입을 명시하는 생성자
     * @param tokenType 토큰 타입 ("Access Token", "Refresh Token")
     */
    public TokenExpiredException(String tokenType, boolean isExpired) {
        super(tokenType + "이 만료되었습니다. 다시 로그인해주세요.");
    }
}