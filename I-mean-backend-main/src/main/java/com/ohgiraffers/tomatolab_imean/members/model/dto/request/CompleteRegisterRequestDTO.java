package com.ohgiraffers.tomatolab_imean.members.model.dto.request;

/**
 * 원스텝 회원가입 요청 DTO
 * 모든 회원가입 정보를 한 번에 받는 DTO
 */
public class CompleteRegisterRequestDTO {
    
    private String memberEmail;     // 이메일
    private String memberPass;      // 비밀번호
    private String memberNickName;  // 닉네임
    private String memberPhone;     // 전화번호
    // 기본 생성자
    public CompleteRegisterRequestDTO() {
    }
    
    // 전체 필드 생성자
    public CompleteRegisterRequestDTO(String memberEmail, String memberPass, String memberNickName, String memberPhone) {
        this.memberEmail = memberEmail;
        this.memberPass = memberPass;
        this.memberNickName = memberNickName;
        this.memberPhone = memberPhone;
    }
    
    // Getter 메서드들
    public String getMemberEmail() {
        return memberEmail;
    }
    
    public String getMemberPass() {
        return memberPass;
    }
    
    public String getMemberNickName() {
        return memberNickName;
    }
    
    public String getMemberPhone() {
        return memberPhone;
    }
    
    // Setter 메서드들
    public void setMemberEmail(String memberEmail) {
        this.memberEmail = memberEmail;
    }
    
    public void setMemberPass(String memberPass) {
        this.memberPass = memberPass;
    }
    
    public void setMemberNickName(String memberNickName) {
        this.memberNickName = memberNickName;
    }
    
    public void setMemberPhone(String memberPhone) {
        this.memberPhone = memberPhone;
    }
    
    @Override
    public String toString() {
        return "CompleteRegisterRequestDTO{" +
                "memberEmail='" + memberEmail + '\'' +
                ", memberPass='[PROTECTED]'" +
                ", memberNickName='" + memberNickName + '\'' +
                ", memberPhone='" + memberPhone + '\'' +
                '}';
    }
}