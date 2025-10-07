package com.ohgiraffers.tomatolab_imean.members.model.dto.request;


import com.ohgiraffers.tomatolab_imean.members.model.common.MemberRole;
import com.ohgiraffers.tomatolab_imean.members.model.common.MemberStatus;

public class AdminRequsetDTO {
    private String memberNickName;
    private String memberEmail;
    private String memberPhone;
    private MemberRole memberRole;
    private MemberStatus memberStatus;

    public AdminRequsetDTO(String memberNickName, String memberEmail, String memberPhone, MemberRole memberRole, MemberStatus memberStatus) {
        this.memberNickName = memberNickName;
        this.memberEmail = memberEmail;
        this.memberPhone = memberPhone;
        this.memberRole = memberRole;
        this.memberStatus = memberStatus;
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

    public String getMemberPhone() {
        return memberPhone;
    }

    public void setMemberPhone(String memberPhone) {
        this.memberPhone = memberPhone;
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

    @Override
    public String toString() {
        return "AdminRequsetDTO{" +
                "memberNickName='" + memberNickName + '\'' +
                ", memberEmail='" + memberEmail + '\'' +
                ", memberPhone='" + memberPhone + '\'' +
                ", memberRole=" + memberRole +
                ", memberStatus=" + memberStatus +
                '}';
    }
}
