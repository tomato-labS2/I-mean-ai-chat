package com.ohgiraffers.tomatolab_imean.auth.jwt;

import com.ohgiraffers.tomatolab_imean.auth.exception.InvalidTokenException;
import com.ohgiraffers.tomatolab_imean.auth.exception.TokenExpiredException;
import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

/**
 * JWT 토큰 생성, 검증, 파싱을 담당하는 핵심 클래스 (member_id 포함 개선 버전)
 */
@Component
public class JwtTokenProvider {
    
    private static final Logger logger = LoggerFactory.getLogger(JwtTokenProvider.class);
    
    private final JwtProperties jwtProperties;
    
    public JwtTokenProvider(JwtProperties jwtProperties) {
        this.jwtProperties = jwtProperties;
    }
    
    /**
     * JWT 서명에 사용할 비밀키 생성
     */
    private SecretKey getSigningKey() {
        return Keys.hmacShaKeyFor(jwtProperties.getSecretKey().getBytes(StandardCharsets.UTF_8));
    }
    
    /**
     * Access Token 생성 (기존 버전 - 하위 호환)
     */
    @Deprecated
    public String createAccessToken(String memberCode) {
        Date now = new Date();
        Date expiry = new Date(now.getTime() + jwtProperties.getAccessTokenExpiration());
        
        return Jwts.builder()
                .setSubject(memberCode)
                .setIssuedAt(now)
                .setExpiration(expiry)
                .signWith(getSigningKey())
                .compact();
    }
    
    /**
     * Access Token 생성 (member_id + coupleId 포함 개선 버전)
     */
    public String createAccessToken(Long memberId, String memberCode, String coupleStatus, String memberRole, Long coupleId) {
        Date now = new Date();
        Date expiry = new Date(now.getTime() + jwtProperties.getAccessTokenExpiration());
        
        return Jwts.builder()
                .setSubject(memberCode)                 // 기존 호환성 유지
                .claim("memberId", memberId)            // 🆕 회원 ID
                .claim("coupleStatus", coupleStatus)    // SINGLE or COUPLED
                .claim("memberRole", memberRole)        // MEMBER, GENERAL_ADMIN, SUPER_ADMIN
                .claim("coupleId", coupleId)            // 🆕 커플 ID (null 가능)
                .setIssuedAt(now)
                .setExpiration(expiry)
                .signWith(getSigningKey())
                .compact();
    }
    
    /**
     * Access Token 생성 (기존 4개 매개변수 버전 - 호환성 유지)
     */
    public String createAccessToken(Long memberId, String memberCode, String coupleStatus, String memberRole) {
        return createAccessToken(memberId, memberCode, coupleStatus, memberRole, null);
    }
    
    /**
     * Access Token 생성 (기존 3개 매개변수 버전 - 호환성 유지)
     */
    public String createAccessToken(String memberCode, String coupleStatus, String memberRole) {
        // member_id 없이 호출된 경우를 위한 호환성 메서드
        logger.warn("createAccessToken 호출 시 memberId가 누락되었습니다. memberCode: {}", memberCode);
        Date now = new Date();
        Date expiry = new Date(now.getTime() + jwtProperties.getAccessTokenExpiration());
        
        return Jwts.builder()
                .setSubject(memberCode)
                .claim("coupleStatus", coupleStatus)
                .claim("memberRole", memberRole)
                .setIssuedAt(now)
                .setExpiration(expiry)
                .signWith(getSigningKey())
                .compact();
    }
    
    /**
     * Refresh Token 생성 (member_id 포함 개선 버전)
     */
    public String createRefreshToken(Long memberId, String memberCode) {
        Date now = new Date();
        Date expiry = new Date(now.getTime() + jwtProperties.getRefreshTokenExpiration());
        
        return Jwts.builder()
                .setSubject(memberCode)                 // 기존 호환성 유지
                .claim("memberId", memberId)            // 🆕 회원 ID 추가
                .claim("tokenType", "refresh")          // 토큰 타입 명시
                .setIssuedAt(now)
                .setExpiration(expiry)
                .signWith(getSigningKey())
                .compact();
    }
    
    /**
     * Refresh Token 생성 (기존 버전 - 호환성 유지)
     */
    public String createRefreshToken(String memberCode) {
        logger.warn("createRefreshToken 호출 시 memberId가 누락되었습니다. memberCode: {}", memberCode);
        Date now = new Date();
        Date expiry = new Date(now.getTime() + jwtProperties.getRefreshTokenExpiration());
        
        return Jwts.builder()
                .setSubject(memberCode)
                .setIssuedAt(now)
                .setExpiration(expiry)
                .signWith(getSigningKey())
                .compact();
    }
    
    /**
     * 🆕 토큰에서 회원 ID 추출
     */
    public Long getMemberIdFromToken(String token) {
        try {
            Claims claims = Jwts.parser()
                    .setSigningKey(getSigningKey())
                    .parseClaimsJws(token)
                    .getBody();
            
            Object memberIdClaim = claims.get("memberId");
            if (memberIdClaim == null) {
                logger.debug("토큰에 memberId 클레임이 없습니다 (구버전 토큰일 수 있음)");
                return null;
            }
            
            // Integer로 저장된 경우를 Long으로 변환
            if (memberIdClaim instanceof Integer) {
                return ((Integer) memberIdClaim).longValue();
            } else if (memberIdClaim instanceof Long) {
                return (Long) memberIdClaim;
            } else {
                logger.warn("memberId 클레임 타입이 예상과 다릅니다: {}", memberIdClaim.getClass());
                return Long.valueOf(memberIdClaim.toString());
            }
            
        } catch (ExpiredJwtException e) {
            logger.warn("만료된 토큰에서 회원 ID 추출 시도: {}", e.getMessage());
            throw new TokenExpiredException("Access Token", true);
        } catch (Exception e) {
            logger.error("토큰에서 회원 ID 추출 실패: {}", e.getMessage());
            throw new InvalidTokenException("토큰에서 회원 ID를 추출할 수 없습니다.", e);
        }
    }
    
    /**
     * 🆕 토큰에서 커플 ID 추출
     */
    public Long getCoupleIdFromToken(String token) {
        try {
            Claims claims = Jwts.parser()
                    .setSigningKey(getSigningKey())
                    .parseClaimsJws(token)
                    .getBody();
            
            Object coupleIdClaim = claims.get("coupleId");
            if (coupleIdClaim == null) {
                logger.debug("토큰에 coupleId 클레임이 없습니다 (구버전 토큰이거나 싱글 사용자)");
                return null;
            }
            
            // Integer로 저장된 경우를 Long으로 변환
            if (coupleIdClaim instanceof Integer) {
                return ((Integer) coupleIdClaim).longValue();
            } else if (coupleIdClaim instanceof Long) {
                return (Long) coupleIdClaim;
            } else {
                logger.warn("coupleId 클레임 타입이 예상과 다릅니다: {}", coupleIdClaim.getClass());
                return Long.valueOf(coupleIdClaim.toString());
            }
            
        } catch (ExpiredJwtException e) {
            logger.warn("만료된 토큰에서 커플 ID 추출 시도: {}", e.getMessage());
            throw new TokenExpiredException("Access Token", true);
        } catch (Exception e) {
            logger.debug("토큰에서 커플 ID 추출 실패 (구버전 토큰일 수 있음): {}", e.getMessage());
            return null; // 기본값으로 null 반환
        }
    }
    
    /**
     * 토큰에서 회원 코드 추출 (기존 유지)
     */
    public String getMemberCodeFromToken(String token) {
        try {
            Claims claims = Jwts.parser()
                    .setSigningKey(getSigningKey())
                    .parseClaimsJws(token)
                    .getBody();
            
            return claims.getSubject();
        } catch (ExpiredJwtException e) {
            logger.warn("만료된 토큰에서 정보 추출 시도: {}", e.getMessage());
            throw new TokenExpiredException("Access Token", true);
        } catch (Exception e) {
            logger.error("토큰에서 회원 코드 추출 실패: {}", e.getMessage());
            throw new InvalidTokenException("토큰에서 사용자 정보를 추출할 수 없습니다.", e);
        }
    }
    
    /**
     * 토큰에서 커플 상태 추출 (기존 유지)
     */
    public String getCoupleStatusFromToken(String token) {
        try {
            Claims claims = Jwts.parser()
                    .setSigningKey(getSigningKey())
                    .parseClaimsJws(token)
                    .getBody();
            
            return claims.get("coupleStatus", String.class);
        } catch (ExpiredJwtException e) {
            logger.warn("만료된 토큰에서 커플 상태 추출 시도: {}", e.getMessage());
            throw new TokenExpiredException("Access Token", true);
        } catch (Exception e) {
            logger.debug("토큰에서 커플 상태 추출 실패 (구버전 토큰일 수 있음): {}", e.getMessage());
            return "SINGLE"; // 기본값으로 SINGLE 반환
        }
    }
    
    /**
     * 토큰에서 회원 역할 추출 (기존 유지)
     */
    public String getMemberRoleFromToken(String token) {
        try {
            Claims claims = Jwts.parser()
                    .setSigningKey(getSigningKey())
                    .parseClaimsJws(token)
                    .getBody();
            
            return claims.get("memberRole", String.class);
        } catch (ExpiredJwtException e) {
            logger.warn("만료된 토큰에서 회원 역할 추출 시도: {}", e.getMessage());
            throw new TokenExpiredException("Access Token", true);
        } catch (Exception e) {
            logger.debug("토큰에서 회원 역할 추출 실패 (구버전 토큰일 수 있음): {}", e.getMessage());
            return "MEMBER"; // 기본값으로 MEMBER 반환
        }
    }
    
    /**
     * 🆕 토큰에서 모든 사용자 정보 추출 (편의 메서드)
     */
    public TokenUserInfo getUserInfoFromToken(String token) {
        try {
            Claims claims = Jwts.parser()
                    .setSigningKey(getSigningKey())
                    .parseClaimsJws(token)
                    .getBody();
            
            String memberCode = claims.getSubject();
            Long memberId = getMemberIdFromToken(token);
            String coupleStatus = claims.get("coupleStatus", String.class);
            String memberRole = claims.get("memberRole", String.class);
            Long coupleId = getCoupleIdFromToken(token);
            
            return new TokenUserInfo(memberId, memberCode, coupleStatus, memberRole, coupleId);
        } catch (Exception e) {
            logger.error("토큰에서 사용자 정보 추출 실패: {}", e.getMessage());
            throw new InvalidTokenException("토큰에서 사용자 정보를 추출할 수 없습니다.", e);
        }
    }
    
    /**
     * 토큰 유효성 검증 (디버깅 로그 추가)
     */
    public boolean validateToken(String token) {
        try {
            logger.debug("🔍 토큰 유효성 검증 시작...");
            Jwts.parser()
                    .setSigningKey(getSigningKey())
                    .parseClaimsJws(token);
            logger.debug("✅ 토큰 유효성 검증 성공");
            return true;
        } catch (ExpiredJwtException e) {
            logger.warn("❌ 만료된 토큰입니다: {}", e.getMessage());
            throw new TokenExpiredException("Access Token", true);
        } catch (UnsupportedJwtException e) {
            logger.warn("❌ 지원하지 않는 토큰입니다: {}", e.getMessage());
            throw InvalidTokenException.unsupportedToken();
        } catch (MalformedJwtException e) {
            logger.warn("❌ 잘못된 형식의 토큰입니다: {}", e.getMessage());
            throw InvalidTokenException.malformedToken();
        } catch (SignatureException e) {
            logger.warn("❌ 잘못된 서명의 토큰입니다: {}", e.getMessage());
            throw InvalidTokenException.invalidSignature();
        } catch (IllegalArgumentException e) {
            logger.warn("❌ 빈 토큰입니다: {}", e.getMessage());
            throw InvalidTokenException.emptyToken();
        } catch (Exception e) {
            logger.error("❌ 토큰 검증 중 예상치 못한 오류: {}", e.getMessage(), e);
            throw new InvalidTokenException("토큰 검증 실패", e);
        }
    }
    
    /**
     * 토큰 만료 시간 확인
     */
    public Date getExpirationFromToken(String token) {
        try {
            Claims claims = Jwts.parser()
                    .setSigningKey(getSigningKey())
                    .parseClaimsJws(token)
                    .getBody();
            
            return claims.getExpiration();
        } catch (Exception e) {
            logger.error("토큰 만료 시간 확인 실패: {}", e.getMessage());
            throw new InvalidTokenException("토큰 만료 시간을 확인할 수 없습니다.", e);
        }
    }
    
    /**
     * 토큰이 곧 만료되는지 확인 (30분 이내)
     */
    public boolean isTokenExpiringSoon(String token) {
        try {
            Date expiration = getExpirationFromToken(token);
            Date now = new Date();
            long timeDiff = expiration.getTime() - now.getTime();
            return timeDiff < (30 * 60 * 1000); // 30분 이내면 true
        } catch (Exception e) {
            logger.warn("토큰 만료 시간 확인 중 오류: {}", e.getMessage());
            return true; // 오류가 발생하면 만료된 것으로 간주
        }
    }
    
    // Getter 메서드
    public JwtProperties getJwtProperties() {
        return jwtProperties;
    }
    
    /**
     * 🆕 토큰에서 추출한 사용자 정보를 담는 내부 클래스
     */
    public static class TokenUserInfo {
        private final Long memberId;
        private final String memberCode;
        private final String coupleStatus;
        private final String memberRole;
        private final Long coupleId;        // 🆕 커플 ID 추가
        
        public TokenUserInfo(Long memberId, String memberCode, String coupleStatus, String memberRole, Long coupleId) {
            this.memberId = memberId;
            this.memberCode = memberCode;
            this.coupleStatus = coupleStatus;
            this.memberRole = memberRole;
            this.coupleId = coupleId;
        }
        
        // Getters
        public Long getMemberId() { return memberId; }
        public String getMemberCode() { return memberCode; }
        public String getCoupleStatus() { return coupleStatus; }
        public String getMemberRole() { return memberRole; }
        public Long getCoupleId() { return coupleId; }  // 🆕 커플 ID getter
        
        @Override
        public String toString() {
            return String.format("TokenUserInfo{memberId=%d, memberCode='%s', coupleStatus='%s', memberRole='%s', coupleId=%s}", 
                    memberId, memberCode, coupleStatus, memberRole, coupleId);
        }
    }
}