package com.ohgiraffers.tomatolab_imean.auth.model;

import com.ohgiraffers.tomatolab_imean.members.model.common.MemberRole;
import com.ohgiraffers.tomatolab_imean.members.model.common.MemberStatus;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

/**
 * Spring Security에서 사용자 인증 정보를 담는 클래스 (member_id 포함 개선 버전)
 */
public class AuthDetails implements UserDetails {

    private Long memberId;           // 🆕 회원 ID 추가
    private String memberCode;
    private String memberPass;
    private MemberRole memberRole;
    private MemberStatus memberStatus;
    private String coupleStatus;     // SINGLE or COUPLED
    private Long coupleId;           // 🆕 커플 ID 추가 (null 가능)

    /**
     * 🆕 생성자 (member_id + coupleId 포함 버전)
     */
    public AuthDetails(Long memberId, String memberCode, String memberPass,
                       MemberRole memberRole, MemberStatus memberStatus, String coupleStatus, Long coupleId) {
        this.memberId = memberId;
        this.memberCode = memberCode;
        this.memberPass = memberPass;
        this.memberRole = memberRole;
        this.memberStatus = memberStatus;
        this.coupleStatus = coupleStatus;
        this.coupleId = coupleId;
    }

    /**
     * 생성자 (coupleId 없는 버전 - 호환성 유지)
     */
    public AuthDetails(Long memberId, String memberCode, String memberPass,
                       MemberRole memberRole, MemberStatus memberStatus, String coupleStatus) {
        this(memberId, memberCode, memberPass, memberRole, memberStatus, coupleStatus, null);
    }

    /**
     * 생성자 (기존 버전 - 하위 호환성, member_id 없음)
     */
    @Deprecated
    public AuthDetails(Long memberId, String memberCode, String memberPass,
                       MemberRole memberRole, MemberStatus memberStatus) {
        this.memberId = memberId;
        this.memberCode = memberCode;
        this.memberPass = memberPass;
        this.memberRole = memberRole;
        this.memberStatus = memberStatus;
        this.coupleStatus = "SINGLE"; // 기본값
    }
    
    /**
     * 🆕 Members 엔티티로부터 AuthDetails 생성하는 팩토리 메서드
     */
    public static AuthDetails from(com.ohgiraffers.tomatolab_imean.members.model.entity.Members member) {
        return new AuthDetails(
            member.getMemberId(),
            member.getMemberCode(),
            member.getMemberPass(),
            member.getMemberRole(),
            member.getMemberStatus(),
            member.getCoupleStatusString(),
            member.getCoupleIdAsLong()      // 🆕 커플 ID 포함
        );
    }

    /**
     * 권한 정보 반환
     */
    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        List<GrantedAuthority> authorities = new ArrayList<>();

        // 역할 기반 권한 추가 (ROLE_ 접두사 필요)
        authorities.add(new SimpleGrantedAuthority("ROLE_" + memberRole.name()));
        
        // 상태 기반 권한 추가
        authorities.add(new SimpleGrantedAuthority("STATUS_" + memberStatus.name()));
        
        // 커플 상태 기반 권한 추가
        authorities.add(new SimpleGrantedAuthority("COUPLE_" + coupleStatus));

        return authorities;
    }

    /**
     * 비밀번호 반환
     */
    @Override
    public String getPassword() {
        return memberPass;
    }

    /**
     * 사용자 식별자 반환
     */
    @Override
    public String getUsername() {
        return memberCode; // 로그인 식별자로 memberCode 사용
    }

    /**
     * 계정 만료 여부
     */
    @Override
    public boolean isAccountNonExpired() {
        return true; // 계정 만료 기능 사용하지 않음
    }

    /**
     * 계정 잠금 여부
     */
    @Override
    public boolean isAccountNonLocked() {
        return MemberStatus.ACTIVE.equals(memberStatus);
    }

    /**
     * 자격 증명(비밀번호) 만료 여부
     */
    @Override
    public boolean isCredentialsNonExpired() {
        return true; // 비밀번호 만료 기능 사용하지 않음
    }

    /**
     * 계정 활성화 여부
     */
    @Override
    public boolean isEnabled() {
        return MemberStatus.ACTIVE.equals(memberStatus);
    }

    // Getter 메서드
    public Long getMemberId() {
        return memberId;
    }

    public String getMemberCode() {
        return memberCode;
    }
    
    public MemberRole getMemberRole() {
        return memberRole;
    }
    
    public MemberStatus getMemberStatus() {
        return memberStatus;
    }
    
    public String getCoupleStatus() {
        return coupleStatus;
    }
    
    /**
     * 🆕 커플 ID 반환
     */
    public Long getCoupleId() {
        return coupleId;
    }
    
    /**
     * 커플 관계에 있는지 확인
     */
    public boolean isInCouple() {
        return "COUPLED".equals(coupleStatus);
    }
    
    /**
     * 싱글 상태인지 확인
     */
    public boolean isSingle() {
        return "SINGLE".equals(coupleStatus);
    }
    
    /**
     * 🆕 관리자 권한 확인
     */
    public boolean isAdmin() {
        return memberRole == MemberRole.GENERAL_ADMIN || memberRole == MemberRole.SUPER_ADMIN;
    }
    
    /**
     * 🆕 최고 관리자 권한 확인
     */
    public boolean isSuperAdmin() {
        return memberRole == MemberRole.SUPER_ADMIN;
    }
    
    @Override
    public String toString() {
        return String.format("AuthDetails{memberId=%d, memberCode='%s', memberRole=%s, coupleStatus='%s', coupleId=%s}", 
                memberId, memberCode, memberRole, coupleStatus, coupleId);
    }
}