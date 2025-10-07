package com.ohgiraffers.tomatolab_imean.auth.service;

import com.ohgiraffers.tomatolab_imean.auth.model.AuthDetails;
import com.ohgiraffers.tomatolab_imean.members.model.common.MemberStatus;
import com.ohgiraffers.tomatolab_imean.members.model.entity.Members;
import com.ohgiraffers.tomatolab_imean.members.service.MemberService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.crossstore.ChangeSetPersister;
import org.springframework.security.authentication.LockedException;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import org.springframework.transaction.annotation.Transactional;

/**
 * 🆕 인증 서비스 (member_id 지원 개선 버전)
 */
@Service
@Transactional(readOnly = true)  // 🔧 모든 조회 메서드에 트랜잭션 적용
public class AuthService implements UserDetailsService {

    private final MemberService memberService;

    @Autowired
    public AuthService(MemberService memberService) {
        this.memberService = memberService;
    }

    /**
     * Spring Security 인증을 위한 사용자 정보 로드 메서드 (memberCode 기반)
     */
    @Override
    public UserDetails loadUserByUsername(String memberCode) throws UsernameNotFoundException {
        try {
            Members member = memberService.findByCode(memberCode);
            checkAccountStatus(member);
            return createAuthDetailsFromMember(member);
        } catch (ChangeSetPersister.NotFoundException e) {
            throw new UsernameNotFoundException("회원 정보가 존재하지 않습니다: " + memberCode);
        }
    }
    
    /**
     * 🆕 member_id로 사용자 정보 로드 메서드 (디버깅 로그 추가)
     */
    public UserDetails loadUserByMemberId(Long memberId) throws UsernameNotFoundException {

        try {
            Members member = memberService.findById(memberId);
            checkAccountStatus(member);
            AuthDetails authDetails = createAuthDetailsFromMember(member);
            return authDetails;
        } catch (IllegalArgumentException e) {
            throw new UsernameNotFoundException("회원 정보가 존재하지 않습니다: ID " + memberId);
        } catch (Exception e) {
            throw new UsernameNotFoundException("사용자 조회 실패: ID " + memberId);
        }
    }
    
    /**
     * 이메일로 사용자 인증 처리 (API 로그인용)
     */
    public UserDetails authenticateByEmail(String email, String password) {
        try {
            Members member = memberService.findByEmail(email);
            checkAccountStatus(member);
            return createAuthDetailsFromMember(member);
        } catch (ChangeSetPersister.NotFoundException e) {
            throw new UsernameNotFoundException("회원 정보가 존재하지 않습니다: " + email);
        }
    }
    
    /**
     * 🆕 member_id나 memberCode로 사용자 정보 조회 (통합 메서드) - Fallback 강화
     */
    public UserDetails loadUserByIdOrCode(Long memberId, String memberCode) throws UsernameNotFoundException {

        // 1차: member_id로 시도
        if (memberId != null) {
            try {
                UserDetails userDetails = loadUserByMemberId(memberId);
                return userDetails;
            } catch (UsernameNotFoundException e) {
                // member_id로 찾지 못한 경우 memberCode로 시도 (fallback)
                if (memberCode != null) {
                    try {
                        UserDetails userDetails = loadUserByUsername(memberCode);
                        return userDetails;
                    } catch (UsernameNotFoundException ex) {
                        throw new UsernameNotFoundException("회원 정보를 찾을 수 없습니다 - ID: " + memberId + ", Code: " + memberCode);
                    }
                }
                throw e;
            }
        } else if (memberCode != null) {
            // member_id가 없는 경우 memberCode로 조회
            return loadUserByUsername(memberCode);
        } else {
            throw new UsernameNotFoundException("회원 ID와 회원 코드가 모두 누락되었습니다");
        }
    }
    
    /**
     * 계정 상태 검증 헬퍼 메서드
     */
    private void checkAccountStatus(Members member) {
        MemberStatus status = member.getMemberStatus();
        
        if (!MemberStatus.ACTIVE.equals(status)) {
            switch (status) {
                case DORMANT:
                    throw new LockedException("휴면 계정입니다. 관리자에게 문의하세요.");
                case BLOCKED:
                    throw new LockedException("차단된 계정입니다. 관리자에게 문의하세요.");
                case DELETED:
                    throw new LockedException("삭제된 계정입니다. 관리자에게 문의하세요.");
                default:
                    throw new LockedException("비활성화된 계정입니다. 관리자에게 문의하세요.");
            }
        }
    }
    
    /**
     * 🆕 Members 엔티티에서 AuthDetails 객체 생성 헬퍼 메서드 (coupleId 포함)
     */
    private AuthDetails createAuthDetailsFromMember(Members member) {
        return new AuthDetails(
            member.getMemberId(),           // 회원 ID
            member.getMemberCode(),
            member.getMemberPass(),
            member.getMemberRole(),
            member.getMemberStatus(),
            member.getCoupleStatusString(), // 실시간 커플 상태
            member.getCoupleIdAsLong()      // 🆕 커플 ID (null 가능)
        );
    }
    
    /**
     * 🆕 사용자 존재 여부 확인 (member_id 기반)
     */
    public boolean existsByMemberId(Long memberId) {
        try {
            memberService.findById(memberId);
            return true;
        } catch (Exception e) {
            return false;
        }
    }
    
    /**
     * 🆕 사용자 존재 여부 확인 (memberCode 기반)
     */
    public boolean existsByMemberCode(String memberCode) {
        try {
            memberService.findByCode(memberCode);
            return true;
        } catch (Exception e) {
            return false;
        }
    }
    
    /**
     * 🆕 사용자의 최신 커플 상태 조회
     */
    public String getCurrentCoupleStatus(Long memberId) {
        try {
            Members member = memberService.findById(memberId);
            return member.getCoupleStatusString();
        } catch (Exception e) {
            return "SINGLE"; // 기본값
        }
    }
    
    /**
     * 🆕 사용자의 최신 권한 정보 조회
     */
    public UserDetails refreshUserDetails(Long memberId) throws UsernameNotFoundException {
        return loadUserByMemberId(memberId);
    }
}