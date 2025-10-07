package com.ohgiraffers.tomatolab_imean.members.model.dto.request;

public class RegisterRequestDTO {
    private String memberCode;
    private String memberPass;
    private String memberNickName;
    private String memberEmail;
    private String memberPhone;
    
    // 생성자
    public RegisterRequestDTO() {
    }
    
    public RegisterRequestDTO(String memberCode, String memberPass, String memberNickName,
                              String memberEmail, String memberPhone) {
        this.memberCode = memberCode;
        this.memberPass = memberPass;
        this.memberNickName = memberNickName;
        this.memberEmail = memberEmail;
        this.memberPhone = memberPhone;
    }
    
    // getter, setter
    public String getMemberCode() {
        return memberCode;
    }

    public void setMemberCode(String memberCode) {
        this.memberCode = memberCode;
    }

    public String getMemberPass() {
        return memberPass;
    }

    public void setMemberPass(String memberPass) {
        this.memberPass = memberPass;
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
}