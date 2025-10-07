package com.ohgiraffers.tomatolab_imean.members.model.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/**
 * Refresh Token 엔티티
 * JWT Refresh Token을 DB에 저장하여 관리
 */
@Entity
@Table(name = "refresh_tokens")
public class RefreshToken {
    
    @Id
    @Column(name = "token_id", length = 36)
    private String tokenId;          // UUID로 생성되는 고유 ID
    
    @Column(name = "member_code", nullable = false, length = 20)
    private String memberCode;       // 회원 코드 (Members와 연결)
    
    @Column(name = "token_value", nullable = false, length = 512)
    private String tokenValue;       // 실제 JWT Refresh Token 값
    
    @Column(name = "expires_at", nullable = false)
    private LocalDateTime expiresAt; // 토큰 만료 시간
    
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt; // 토큰 생성 시간
    
    @Column(name = "used_at")
    private LocalDateTime usedAt;    // 토큰 사용 시간 (갱신 시)
    
    @Column(name = "revoked", nullable = false)
    private boolean revoked = false; // 토큰 폐기 여부
    
    // 기본 생성자
    public RefreshToken() {
    }
    
    // 전체 생성자
    public RefreshToken(String tokenId, String memberCode, String tokenValue, LocalDateTime expiresAt) {
        this.tokenId = tokenId;
        this.memberCode = memberCode;
        this.tokenValue = tokenValue;
        this.expiresAt = expiresAt;
        this.createdAt = LocalDateTime.now();
        this.revoked = false;
    }
    
    // 편의 생성자
    public RefreshToken(String tokenId, String memberCode, String tokenValue, long expirationMs) {
        this(tokenId, memberCode, tokenValue, LocalDateTime.now().plusNanos(expirationMs * 1_000_000));
    }
    
    // Getter 메서드들
    public String getTokenId() {
        return tokenId;
    }
    
    public String getMemberCode() {
        return memberCode;
    }
    
    public String getTokenValue() {
        return tokenValue;
    }
    
    public LocalDateTime getExpiresAt() {
        return expiresAt;
    }
    
    public LocalDateTime getCreatedAt() {
        return createdAt;
    }
    
    public LocalDateTime getUsedAt() {
        return usedAt;
    }
    
    public boolean isRevoked() {
        return revoked;
    }
    
    // Setter 메서드들
    public void setTokenId(String tokenId) {
        this.tokenId = tokenId;
    }
    
    public void setMemberCode(String memberCode) {
        this.memberCode = memberCode;
    }
    
    public void setTokenValue(String tokenValue) {
        this.tokenValue = tokenValue;
    }
    
    public void setExpiresAt(LocalDateTime expiresAt) {
        this.expiresAt = expiresAt;
    }
    
    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
    
    public void setUsedAt(LocalDateTime usedAt) {
        this.usedAt = usedAt;
    }
    
    public void setRevoked(boolean revoked) {
        this.revoked = revoked;
    }
    
    // 비즈니스 메서드들
    
    /**
     * 토큰이 만료되었는지 확인
     */
    public boolean isExpired() {
        return LocalDateTime.now().isAfter(this.expiresAt);
    }
    
    /**
     * 토큰이 유효한지 확인 (만료되지 않고 폐기되지 않음)
     */
    public boolean isValid() {
        return !isExpired() && !isRevoked();
    }
    
    /**
     * 토큰 사용 처리 (갱신 시 호출)
     */
    public void markAsUsed() {
        this.usedAt = LocalDateTime.now();
    }
    
    /**
     * 토큰 폐기 처리
     */
    public void revoke() {
        this.revoked = true;
    }
    
    @Override
    public String toString() {
        return "RefreshToken{" +
                "tokenId='" + tokenId + '\'' +
                ", memberCode='" + memberCode + '\'' +
                ", expiresAt=" + expiresAt +
                ", createdAt=" + createdAt +
                ", usedAt=" + usedAt +
                ", revoked=" + revoked +
                '}';
    }
}