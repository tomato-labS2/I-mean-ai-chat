package com.ohgiraffers.tomatolab_imean.auth.jwt;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
/**
 * JWT 관련 설정 프로퍼티 클래스
 * application.yml의 jwt.* 설정들을 자동으로 매핑
 */
@ConfigurationProperties(prefix = "jwt") // application.yml의 jwt: 하위 설정들을 매핑
@Configuration
public class JwtProperties {

    /**
     * JWT 토큰 생성/검증에 사용할 비밀키
     * application.yml의 jwt.secret-key 값이 자동 주입됨
     */
    private String secretKey;

    private long accessTokenExpiration;
    private long refreshTokenExpiration;

    public JwtProperties() {}

    public JwtProperties(String secretKey, long accessTokenExpiration, long refreshTokenExpiration) {
        this.secretKey = secretKey;
        this.accessTokenExpiration = accessTokenExpiration;
        this.refreshTokenExpiration = refreshTokenExpiration;
    }

    public String getSecretKey() {
        return secretKey;
    }

    public void setSecretKey(String secretKey) {
        this.secretKey = secretKey;
    }

    public long getAccessTokenExpiration() {
        return accessTokenExpiration;
    }

    public void setAccessTokenExpiration(long accessTokenExpiration) {
        this.accessTokenExpiration = accessTokenExpiration;
    }

    public long getRefreshTokenExpiration() {
        return refreshTokenExpiration;
    }

    public void setRefreshTokenExpiration(long refreshTokenExpiration) {
        this.refreshTokenExpiration = refreshTokenExpiration;
    }

}