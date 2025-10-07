package com.ohgiraffers.tomatolab_imean.auth.exception;

/**
 * Refresh Token을 찾을 수 없을 때 발생하는 예외 클래스
 * 토큰 갱신 요청 시 유효한 Refresh Token이 없을 때 사용
 */
public class RefreshTokenNotFoundException extends JwtTokenException {
    
    /**
     * 기본 생성자
     */
    public RefreshTokenNotFoundException() {
        super("Refresh Token을 찾을 수 없습니다. 다시 로그인해주세요.");
    }
    
    /**
     * 메시지를 포함한 생성자
     * @param message 예외 메시지
     */
    public RefreshTokenNotFoundException(String message) {
        super(message);
    }
    
    /**
     * 메시지와 원인을 포함한 생성자
     * @param message 예외 메시지
     * @param cause 원인 예외
     */
    public RefreshTokenNotFoundException(String message, Throwable cause) {
        super(message, cause);
    }
    
    /**
     * 사용자 코드를 포함한 생성자
     * @param memberCode 회원 코드
     */
    public RefreshTokenNotFoundException(String memberCode, boolean includeCode) {
        super("회원(" + memberCode + ")의 Refresh Token을 찾을 수 없습니다.");
    }
}