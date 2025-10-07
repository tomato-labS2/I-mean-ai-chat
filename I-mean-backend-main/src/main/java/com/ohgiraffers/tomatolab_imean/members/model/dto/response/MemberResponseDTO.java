package com.ohgiraffers.tomatolab_imean.members.model.dto.response;

import com.ohgiraffers.tomatolab_imean.members.model.entity.Members;

import java.time.LocalDateTime;

public class MemberResponseDTO {
    private Long memberId;           // 🆕 추가
    private String memberCode;
    private String memberNickName;
    private String memberEmail;
    private String memberRole;       // 🆕 추가
    private String coupleStatus;     // 🆕 추가
    private Long coupleId;           // 🆕 추가
    private LocalDateTime memberCreatedAt;
    
    // 생성자
    public MemberResponseDTO() {
    }
    
    public MemberResponseDTO(Members member) {
        this.memberId = member.getMemberId();                    // 🆕 추가
        this.memberCode = member.getMemberCode();
        this.memberNickName = member.getMemberNickName();
        this.memberEmail = member.getMemberEmail();
        this.memberRole = member.getMemberRole().name();         // 🆕 추가
        this.coupleStatus = member.getCoupleStatusString();      // 🆕 추가
        this.coupleId = member.getCoupleIdAsLong();              // 🆕 추가
        this.memberCreatedAt = member.getMemberCreatedAt();
    }
    
    // getter, setter
    public Long getMemberId() {        // 🆕 추가
        return memberId;
    }

    public void setMemberId(Long memberId) {   // 🆕 추가
        this.memberId = memberId;
    }

    public String getMemberCode() {
        return memberCode;
    }

    public void setMemberCode(String memberCode) {
        this.memberCode = memberCode;
    }

    public String getMemberNickName() {
        return memberNickName;
    }

    public void setMemberNickName(String memberNickName) {
        this.memberNickName = memberNickName;
    }

    public String getMemberEmail() {
        return memberEmail;
    }

    public void setMemberEmail(String memberEmail) {
        this.memberEmail = memberEmail;
    }

    public String getMemberRole() {    // 🆕 추가
        return memberRole;
    }

    public void setMemberRole(String memberRole) {  // 🆕 추가
        this.memberRole = memberRole;
    }

    public String getCoupleStatus() {  // 🆕 추가
        return coupleStatus;
    }

    public void setCoupleStatus(String coupleStatus) {  // 🆕 추가
        this.coupleStatus = coupleStatus;
    }

    public Long getCoupleId() {        // 🆕 추가
        return coupleId;
    }

    public void setCoupleId(Long coupleId) {    // 🆕 추가
        this.coupleId = coupleId;
    }

    public LocalDateTime getMemberCreatedAt() {
        return memberCreatedAt;
    }

    public void setMemberCreatedAt(LocalDateTime memberCreatedAt) {
        this.memberCreatedAt = memberCreatedAt;
    }
}