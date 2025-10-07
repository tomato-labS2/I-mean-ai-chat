package com.ohgiraffers.tomatolab_imean.auth.model.dto.response;

import com.ohgiraffers.tomatolab_imean.members.model.dto.response.MemberResponseDTO;

/**
 * JWT 로그인 성공 응답 DTO
 * Access Token, Refresh Token, 사용자 정보를 포함
 */
public class LoginResponseDTO {
    
    private String accessToken;         // JWT Access Token
    private String refreshToken;        // JWT Refresh Token  
    private String tokenType;           // 토큰 타입 (Bearer)
    private long expiresIn;             // Access Token 만료 시간 (초)
    private MemberResponseDTO memberInfo; // 사용자 정보
    
    // 기본 생성자
    public LoginResponseDTO() {
        this.tokenType = "Bearer";
    }
    
    // 전체 필드 생성자
    public LoginResponseDTO(String accessToken, String refreshToken, long expiresIn, MemberResponseDTO memberInfo) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        this.tokenType = "Bearer";
        this.expiresIn = expiresIn;
        this.memberInfo = memberInfo;
    }
    
    // 간단한 생성자 (만료시간 1시간 기본값)
    public LoginResponseDTO(String accessToken, String refreshToken, MemberResponseDTO memberInfo) {
        this(accessToken, refreshToken, 3600, memberInfo); // 1시간 = 3600초
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
    
    public MemberResponseDTO getMemberInfo() {
        return memberInfo;
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
    
    public void setMemberInfo(MemberResponseDTO memberInfo) {
        this.memberInfo = memberInfo;
    }
    
    @Override
    public String toString() {
        return "LoginResponseDTO{" +
                "accessToken='" + accessToken + '\'' +
                ", refreshToken='" + refreshToken + '\'' +
                ", tokenType='" + tokenType + '\'' +
                ", expiresIn=" + expiresIn +
                ", memberInfo=" + memberInfo +
                '}';
    }
}