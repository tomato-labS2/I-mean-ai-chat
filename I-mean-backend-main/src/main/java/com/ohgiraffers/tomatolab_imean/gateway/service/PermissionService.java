package com.ohgiraffers.tomatolab_imean.gateway.service;

import com.ohgiraffers.tomatolab_imean.couple.repository.CoupleRepository;
import com.ohgiraffers.tomatolab_imean.members.repository.MemberRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.stereotype.Service;

import java.util.Collection;

/**
 * Gateway 권한 확인 서비스
 * 
 * 이 서비스는 Gateway 레이어에서 사용자의 기능별 접근 권한을 검증합니다.
 * Spring Security의 기본 인증/인가와 연계하여 추가적인 비즈니스 로직 기반의
 * 권한 확인을 수행합니다.
 * 
 * 주요 기능:
 * - 채팅 기능 접근 권한 확인 (커플 관계 필요)
 * - AI 기능 접근 권한 확인 (인증된 사용자)
 * - 특정 채팅방 접근 권한 확인
 * - 관리자 권한 확인
 * - 사용자 식별 정보 추출
 * 
 * 권한 체계:
 * - COUPLE_COUPLED: 커플 관계가 성립된 사용자
 * - ROLE_GENERAL_ADMIN: 일반 관리자
 * - ROLE_SUPER_ADMIN: 최고 관리자
 * 
 * @author TomatoLab
 * @version 1.0
 */
@Service
public class PermissionService {
    
    /** 로깅을 위한 Logger 인스턴스 */
    private static final Logger logger = LoggerFactory.getLogger(PermissionService.class);
    
    /** 회원 정보 조회를 위한 Repository */
    private final MemberRepository memberRepository;
    
    /** 커플 정보 조회를 위한 Repository */
    private final CoupleRepository coupleRepository;
    
    /**
     * 생성자 주입을 통한 의존성 주입
     * 
     * @param memberRepository 회원 정보 저장소
     * @param coupleRepository 커플 정보 저장소
     */
    @Autowired
    public PermissionService(MemberRepository memberRepository, CoupleRepository coupleRepository) {
        this.memberRepository = memberRepository;
        this.coupleRepository = coupleRepository;
    }
    
    /**
     * 채팅 기능 접근 권한 확인
     * 
     * 채팅 기능은 커플 관계가 성립된 사용자만 사용할 수 있습니다.
     * 단순히 회원가입만 한 사용자는 채팅 기능을 사용할 수 없고,
     * 반드시 다른 사용자와 커플 매칭이 완료되어야 합니다.
     * 
     * 검증 단계:
     * 1. Spring Security 권한 확인 (COUPLE_COUPLED)
     * 2. 회원 존재 여부 확인
     * 3. 추가 비즈니스 로직 검증 (필요시)
     * 
     * @param authentication 현재 인증된 사용자 정보
     * @return 채팅 기능 접근 가능 시 true, 불가능 시 false
     */
    public boolean canAccessChat(Authentication authentication) {
        try {
            // 1단계: Spring Security 권한 확인
            if (!hasAuthority(authentication, "COUPLE_COUPLED")) {
                logger.warn("채팅 접근 거부 - 커플 권한 없음: {}", authentication.getName());
                return false;
            }
            
            // 2단계: 추가 비즈니스 로직 권한 확인
            String memberCode = authentication.getName();
            
            // 회원 존재 확인 - DB에서 실제 회원 정보 검증
            if (!memberRepository.existsByMemberCode(memberCode)) {
                logger.warn("채팅 접근 거부 - 회원 없음: {}", memberCode);
                return false;
            }
            
            // 성공적인 권한 확인
            logger.debug("채팅 접근 허용: {}", memberCode);
            return true;
            
        } catch (Exception e) {
            // 예외 발생 시 안전하게 접근 거부
            logger.error("채팅 권한 확인 중 오류: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * AI 기능 접근 권한 확인
     * 
     * AI 기능은 인증된 모든 사용자가 사용할 수 있습니다.
     * 커플 관계가 성립되지 않은 사용자도 AI 기능은 자유롭게 이용 가능합니다.
     * 
     * 검증 단계:
     * 1. 사용자 인증 상태 확인
     * 2. 회원 존재 여부 확인
     * 3. 추가 제약사항 확인 (필요시)
     * 
     * @param authentication 현재 인증된 사용자 정보
     * @return AI 기능 접근 가능 시 true, 불가능 시 false
     */
    public boolean canAccessAi(Authentication authentication) {
        try {
            // 1단계: 기본 인증 상태 확인
            if (authentication == null || !authentication.isAuthenticated()) {
                logger.warn("AI 접근 거부 - 인증 없음");
                return false;
            }
            
            String memberCode = authentication.getName();
            
            // 2단계: 회원 존재 확인 - DB에서 실제 회원 정보 검증
            if (!memberRepository.existsByMemberCode(memberCode)) {
                logger.warn("AI 접근 거부 - 회원 없음: {}", memberCode);
                return false;
            }
            
            // 성공적인 권한 확인
            logger.debug("AI 접근 허용: {}", memberCode);
            return true;
            
        } catch (Exception e) {
            // 예외 발생 시 안전하게 접근 거부
            logger.error("AI 권한 확인 중 오류: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * 특정 채팅방 접근 권한 확인
     * 
     * 특정 채팅방에 대한 세부적인 접근 권한을 확인합니다.
     * 현재는 기본적인 채팅 권한 확인만 수행하지만,
     * 향후 채팅방별 세부 권한 로직을 확장할 수 있습니다.
     * 
     * 미래 확장 계획:
     * - 개인 채팅방 vs 그룹 채팅방 구분
     * - 채팅방 초대 권한 확인
     * - 채팅방 관리자 권한 확인
     * - 비공개 채팅방 접근 권한 확인
     * 
     * @param authentication 현재 인증된 사용자 정보
     * @param chatroomId 접근하려는 채팅방의 고유 식별자
     * @return 채팅방 접근 가능 시 true, 불가능 시 false
     */
    public boolean canAccessChatroom(Authentication authentication, String chatroomId) {
        try {
            // 1단계: 기본 채팅 권한 확인
            if (!canAccessChat(authentication)) {
                return false;
            }
            
            // 2단계: 채팅방별 세부 권한 확인 (향후 확장)
            // TODO: 채팅방 테이블 생성 후 구현 예정
            // 구현 예정 내용:
            // - 채팅방 존재 여부 확인
            // - 사용자의 해당 채팅방 멤버십 확인
            // - 커플 전용 채팅방인 경우 커플 관계 확인
            // - 그룹 채팅방인 경우 초대 여부 확인
            // - 채팅방 상태 확인 (활성/비활성/삭제됨 등)
            
            logger.debug("채팅방 접근 허용: {} -> {}", authentication.getName(), chatroomId);
            return true;
            
        } catch (Exception e) {
            // 예외 발생 시 안전하게 접근 거부
            logger.error("채팅방 권한 확인 중 오류: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * 관리자 권한 확인
     * 
     * 일반 관리자 또는 최고 관리자 권한을 가진 사용자인지 확인합니다.
     * 시스템 관리, 모니터링, 설정 변경 등의 기능에 사용됩니다.
     * 
     * @param authentication 현재 인증된 사용자 정보
     * @return 관리자 권한 보유 시 true, 미보유 시 false
     */
    public boolean isAdmin(Authentication authentication) {
        return hasAnyAuthority(authentication, "ROLE_GENERAL_ADMIN", "ROLE_SUPER_ADMIN");
    }
    
    /**
     * 특정 권한 보유 여부 확인
     * 
     * 사용자가 지정된 권한을 가지고 있는지 확인하는 내부 헬퍼 메서드입니다.
     * Spring Security의 GrantedAuthority 컬렉션을 검사합니다.
     * 
     * @param authentication 사용자 인증 정보
     * @param authority 확인할 권한 문자열
     * @return 해당 권한 보유 시 true, 미보유 시 false
     */
    private boolean hasAuthority(Authentication authentication, String authority) {
        if (authentication == null) {
            return false;
        }
        
        Collection<? extends GrantedAuthority> authorities = authentication.getAuthorities();
        return authorities.stream()
                .anyMatch(grantedAuthority -> authority.equals(grantedAuthority.getAuthority()));
    }
    
    /**
     * 여러 권한 중 하나라도 보유 여부 확인
     * 
     * 사용자가 지정된 권한들 중 하나라도 가지고 있는지 확인하는 내부 헬퍼 메서드입니다.
     * OR 조건으로 권한을 확인할 때 사용됩니다.
     * 
     * @param authentication 사용자 인증 정보
     * @param authorities 확인할 권한 문자열 배열
     * @return 권한 중 하나라도 보유 시 true, 모두 미보유 시 false
     */
    private boolean hasAnyAuthority(Authentication authentication, String... authorities) {
        if (authentication == null) {
            return false;
        }
        
        Collection<? extends GrantedAuthority> userAuthorities = authentication.getAuthorities();
        for (String authority : authorities) {
            if (userAuthorities.stream()
                    .anyMatch(grantedAuthority -> authority.equals(grantedAuthority.getAuthority()))) {
                return true;
            }
        }
        return false;
    }
    
    /**
     * 사용자 ID 추출 (회원 코드 기반)
     * 
     * Authentication 객체에서 사용자의 고유 식별자를 추출합니다.
     * 이 시스템에서는 회원 코드(memberCode)를 사용자 ID로 사용합니다.
     * 
     * @param authentication 사용자 인증 정보
     * @return 사용자 ID (회원 코드), 인증 정보가 없으면 null
     */
    public String extractUserId(Authentication authentication) {
        return authentication != null ? authentication.getName() : null;
    }
}
