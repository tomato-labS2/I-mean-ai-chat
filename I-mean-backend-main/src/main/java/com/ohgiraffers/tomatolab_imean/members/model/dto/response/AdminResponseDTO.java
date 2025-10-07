package com.ohgiraffers.tomatolab_imean.members.model.dto.response;

import com.ohgiraffers.tomatolab_imean.members.model.common.MemberRole;
import com.ohgiraffers.tomatolab_imean.members.model.common.MemberStatus;

import java.time.LocalDateTime;

public class AdminResponseDTO {

    private Long memberId;
    private String memberCode;
    private String memberName;
    private String memberEmail;
    private String memberPhone;
    private String memberPass;
    private MemberRole memberRole;
    private MemberStatus memberStatus;
    private Long CoupleId;
    private LocalDateTime memberCreatedAt;
    private LocalDateTime memberUpdatedAt;
    private LocalDateTime memberDeletedAt;

    public AdminResponseDTO(Long memberId, String memberCode, String memberName, String memberEmail, String memberPhone, String memberPass, MemberRole memberRole, MemberStatus memberStatus, Long coupleId, LocalDateTime memberCreatedAt, LocalDateTime memberUpdatedAt, LocalDateTime memberDeletedAt) {
        this.memberId = memberId;
        this.memberCode = memberCode;
        this.memberName = memberName;
        this.memberEmail = memberEmail;
        this.memberPhone = memberPhone;
        this.memberPass = memberPass;
        this.memberRole = memberRole;
        this.memberStatus = memberStatus;
        CoupleId = coupleId;
        this.memberCreatedAt = memberCreatedAt;
        this.memberUpdatedAt = memberUpdatedAt;
        this.memberDeletedAt = memberDeletedAt;
    }

    public Long getMemberId() {
        return memberId;
    }

    public void setMemberId(Long memberId) {
        this.memberId = memberId;
    }

    public String getMemberCode() {
        return memberCode;
    }

    public void setMemberCode(String memberCode) {
        this.memberCode = memberCode;
    }

    public String getMemberName() {
        return memberName;
    }

    public void setMemberName(String memberName) {
        this.memberName = memberName;
    }

    public String getMemberEmail() {
        return memberEmail;
    }

    public void setMemberEmail(String memberEmail) {
        this.memberEmail = memberEmail;
    }

    public String getMemberPhone() {
        return memberPhone;
    }

    public void setMemberPhone(String memberPhone) {
        this.memberPhone = memberPhone;
    }

    public String getMemberPass() {
        return memberPass;
    }

    public void setMemberPass(String memberPass) {
        this.memberPass = memberPass;
    }

    public MemberRole getMemberRole() {
        return memberRole;
    }

    public void setMemberRole(MemberRole memberRole) {
        this.memberRole = memberRole;
    }

    public MemberStatus getMemberStatus() {
        return memberStatus;
    }

    public void setMemberStatus(MemberStatus memberStatus) {
        this.memberStatus = memberStatus;
    }

    public Long getCoupleId() {
        return CoupleId;
    }

    public void setCoupleId(Long coupleId) {
        CoupleId = coupleId;
    }

    public LocalDateTime getMemberCreatedAt() {
        return memberCreatedAt;
    }

    public void setMemberCreatedAt(LocalDateTime memberCreatedAt) {
        this.memberCreatedAt = memberCreatedAt;
    }

    public LocalDateTime getMemberUpdatedAt() {
        return memberUpdatedAt;
    }

    public void setMemberUpdatedAt(LocalDateTime memberUpdatedAt) {
        this.memberUpdatedAt = memberUpdatedAt;
    }

    public LocalDateTime getMemberDeletedAt() {
        return memberDeletedAt;
    }

    public void setMemberDeletedAt(LocalDateTime memberDeletedAt) {
        this.memberDeletedAt = memberDeletedAt;
    }

    @Override
    public String toString() {
        return "AdminResponseDTO{" +
                "memberId=" + memberId +
                ", memberCode='" + memberCode + '\'' +
                ", memberName='" + memberName + '\'' +
                ", memberEmail='" + memberEmail + '\'' +
                ", memberPhone='" + memberPhone + '\'' +
                ", memberPass='" + memberPass + '\'' +
                ", memberRole=" + memberRole +
                ", memberStatus=" + memberStatus +
                ", CoupleId=" + CoupleId +
                ", memberCreatedAt=" + memberCreatedAt +
                ", memberUpdatedAt=" + memberUpdatedAt +
                ", memberDeletedAt=" + memberDeletedAt +
                '}';
    }
}
