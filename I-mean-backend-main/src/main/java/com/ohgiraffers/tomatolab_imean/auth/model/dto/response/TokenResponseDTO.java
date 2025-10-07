package com.ohgiraffers.tomatolab_imean.auth.model.dto.response;

/**
 * 토큰 갱신 응답 DTO
 */
public class TokenResponseDTO {
    
    private String accessToken;     // 새로운 Access Token
    private String refreshToken;    // 새로운 Refresh Token (토큰 로테이션 시)
    private String tokenType;       // 토큰 타입 (Bearer)
    private long expiresIn;         // Access Token 만료 시간 (초)
    
    // 기본 생성자
    public TokenResponseDTO() {
        this.tokenType = "Bearer";
    }
    
    // Access Token만 갱신하는 경우
    public TokenResponseDTO(String accessToken, long expiresIn) {
        this.accessToken = accessToken;
        this.tokenType = "Bearer";
        this.expiresIn = expiresIn;
    }
    
    // 토큰 로테이션 (모든 토큰 갱신)
    public TokenResponseDTO(String accessToken, String refreshToken, long expiresIn) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        this.tokenType = "Bearer";
        this.expiresIn = expiresIn;
    }
    
    // Getter 메서드들
    public String getAccessToken() {
        return accessToken;
    }
    
    public String getRefreshToken() {
        return refreshToken;
    }
    
    public String getTokenType() {
        return tokenType;
    }
    
    public long getExpiresIn() {
        return expiresIn;
    }
    
    // Setter 메서드들
    public void setAccessToken(String accessToken) {
        this.accessToken = accessToken;
    }
    
    public void setRefreshToken(String refreshToken) {
        this.refreshToken = refreshToken;
    }
    
    public void setTokenType(String tokenType) {
        this.tokenType = tokenType;
    }
    
    public void setExpiresIn(long expiresIn) {
        this.expiresIn = expiresIn;
    }
    
    @Override
    public String toString() {
        return "TokenResponseDTO{" +
                "accessToken='[PROTECTED]'" +
                ", refreshToken='" + (refreshToken != null ? "[PROTECTED]" : "null") + '\'' +
                ", tokenType='" + tokenType + '\'' +
                ", expiresIn=" + expiresIn +
                '}';
    }
}