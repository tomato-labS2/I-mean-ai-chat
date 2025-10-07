package com.ohgiraffers.tomatolab_imean.auth.model.dto.request;

/**
 * Refresh Token 갱신 요청 DTO
 */
public class RefreshTokenRequestDTO {
    
    private String refreshToken;    // JWT Refresh Token
    
    // 기본 생성자
    public RefreshTokenRequestDTO() {
    }
    
    // 생성자
    public RefreshTokenRequestDTO(String refreshToken) {
        this.refreshToken = refreshToken;
    }
    
    // Getter
    public String getRefreshToken() {
        return refreshToken;
    }
    
    // Setter
    public void setRefreshToken(String refreshToken) {
        this.refreshToken = refreshToken;
    }
    
    @Override
    public String toString() {
        return "RefreshTokenRequestDTO{" +
                "refreshToken='[PROTECTED]'" +
                '}';
    }
}