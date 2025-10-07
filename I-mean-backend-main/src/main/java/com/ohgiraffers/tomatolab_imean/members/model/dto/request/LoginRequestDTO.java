package com.ohgiraffers.tomatolab_imean.members.model.dto.request;

public class LoginRequestDTO {
    private String memberEmail;
    private String memberPass;
    
    // 생성자
    public LoginRequestDTO() {
    }
    
    public LoginRequestDTO(String memberEmail, String memberPass) {
        this.memberEmail = memberEmail;
        this.memberPass = memberPass;
    }
    
    // getter, setter
    public String getMemberEmail() {
        return memberEmail;
    }
    
    public void setMemberEmail(String memberEmail) {
        this.memberEmail = memberEmail;
    }
    
    public String getMemberPass() {
        return memberPass;
    }
    
    public void setMemberPass(String memberPass) {
        this.memberPass = memberPass;
    }
    

}