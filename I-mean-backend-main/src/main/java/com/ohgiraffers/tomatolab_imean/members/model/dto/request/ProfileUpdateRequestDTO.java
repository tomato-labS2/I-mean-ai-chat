package com.ohgiraffers.tomatolab_imean.members.model.dto.request;

public class ProfileUpdateRequestDTO {
    private String currentPassword; // 현재 비밀번호 (변경 시 필요)
    private String newPassword;     // 새 비밀번호 (선택적)
    private String memberEmail;
    private String memberPhone;
    
    // 생성자
    public ProfileUpdateRequestDTO() {
    }
    
    public ProfileUpdateRequestDTO(String currentPassword, String newPassword,
                                   String memberEmail, String memberPhone) {
        this.currentPassword = currentPassword;
        this.newPassword = newPassword;
        this.memberEmail = memberEmail;
        this.memberPhone = memberPhone;
    }
    
    // getter, setter
    public String getCurrentPassword() {
        return currentPassword;
    }

    public void setCurrentPassword(String currentPassword) {
        this.currentPassword = currentPassword;
    }

    public String getNewPassword() {
        return newPassword;
    }

    public void setNewPassword(String newPassword) {
        this.newPassword = newPassword;
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