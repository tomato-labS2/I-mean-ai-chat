package com.ohgiraffers.tomatolab_imean.members.repository;

import com.ohgiraffers.tomatolab_imean.members.model.entity.RefreshToken;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * Refresh Token 레포지토리
 * Refresh Token의 CRUD 및 관리 기능 제공
 */
@Repository
public interface RefreshTokenRepository extends JpaRepository<RefreshToken, String> {
    
    /**
     * 토큰 값으로 Refresh Token 조회
     * @param tokenValue JWT Refresh Token 값
     * @return RefreshToken 엔티티 (Optional)
     */
    Optional<RefreshToken> findByTokenValue(String tokenValue);
    
    /**
     * 회원 코드로 유효한 Refresh Token 목록 조회
     * @param memberCode 회원 코드
     * @return 유효한 RefreshToken 목록
     */
    @Query("SELECT rt FROM RefreshToken rt WHERE rt.memberCode = :memberCode " +
           "AND rt.revoked = false AND rt.expiresAt > :now")
    List<RefreshToken> findValidTokensByMemberCode(
        @Param("memberCode") String memberCode, 
        @Param("now") LocalDateTime now
    );
    
    /**
     * 회원 코드로 모든 Refresh Token 조회 (만료/폐기 포함)
     * @param memberCode 회원 코드
     * @return 모든 RefreshToken 목록
     */
    List<RefreshToken> findByMemberCode(String memberCode);
    
    /**
     * 회원의 모든 Refresh Token 폐기
     * @param memberCode 회원 코드
     * @return 업데이트된 행 수
     */
    @Modifying
    @Query("UPDATE RefreshToken rt SET rt.revoked = true WHERE rt.memberCode = :memberCode")
    int revokeAllTokensByMemberCode(@Param("memberCode") String memberCode);
    
    /**
     * 만료된 Refresh Token 삭제
     * @param now 현재 시간
     * @return 삭제된 행 수
     */
    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.expiresAt < :now")
    int deleteExpiredTokens(@Param("now") LocalDateTime now);
    
    /**
     * 폐기된 Refresh Token 삭제
     * @return 삭제된 행 수
     */
    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.revoked = true")
    int deleteRevokedTokens();
    
    /**
     * 특정 회원의 최신 N개 토큰 ID 조회 (MySQL LIMIT 문제 해결용)
     * @param memberCode 회원 코드
     * @param pageable 페이징 정보 (크기는 keepCount)
     * @return 유지할 토큰 ID 목록
     */
    @Query("SELECT rt.tokenId FROM RefreshToken rt WHERE rt.memberCode = :memberCode " +
           "ORDER BY rt.createdAt DESC")
    List<String> findRecentTokenIdsByMemberCode(
        @Param("memberCode") String memberCode, 
        Pageable pageable
    );
    
    /**
     * 특정 토큰 ID를 제외하고 회원의 토큰 삭제
     * @param memberCode 회원 코드
     * @param keepTokenIds 유지할 토큰 ID 목록
     * @return 삭제된 행 수
     */
    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.memberCode = :memberCode " +
           "AND rt.tokenId NOT IN :keepTokenIds")
    int deleteTokensExcept(
        @Param("memberCode") String memberCode, 
        @Param("keepTokenIds") List<String> keepTokenIds
    );
    
    /**
     * 회원의 모든 토큰 삭제
     * @param memberCode 회원 코드
     * @return 삭제된 행 수
     */
    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.memberCode = :memberCode")
    int deleteAllTokensByMemberCode(@Param("memberCode") String memberCode);
    
    /**
     * 토큰 값으로 유효한 Refresh Token 조회
     * @param tokenValue 토큰 값
     * @param now 현재 시간
     * @return 유효한 RefreshToken (Optional)
     */
    @Query("SELECT rt FROM RefreshToken rt WHERE rt.tokenValue = :tokenValue " +
           "AND rt.revoked = false AND rt.expiresAt > :now")
    Optional<RefreshToken> findValidTokenByValue(
        @Param("tokenValue") String tokenValue, 
        @Param("now") LocalDateTime now
    );
    
    /**
     * 회원별 유효한 토큰 개수 조회
     * @param memberCode 회원 코드
     * @param now 현재 시간
     * @return 유효한 토큰 개수
     */
    @Query("SELECT COUNT(rt) FROM RefreshToken rt WHERE rt.memberCode = :memberCode " +
           "AND rt.revoked = false AND rt.expiresAt > :now")
    long countValidTokensByMemberCode(
        @Param("memberCode") String memberCode, 
        @Param("now") LocalDateTime now
    );
    
    /**
     * 전체 유효한 토큰 개수 조회
     * @param now 현재 시간
     * @return 전체 유효한 토큰 개수
     */
    @Query("SELECT COUNT(rt) FROM RefreshToken rt WHERE rt.revoked = false AND rt.expiresAt > :now")
    long countValidTokens(@Param("now") LocalDateTime now);
}