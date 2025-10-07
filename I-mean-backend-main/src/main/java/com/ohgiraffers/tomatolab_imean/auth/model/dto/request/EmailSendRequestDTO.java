package com.ohgiraffers.tomatolab_imean.auth.model.dto.request;

/**
 * 이메일 발송 요청 DTO
 */
public class EmailSendRequestDTO {
    
    private String email;
    private String type; // "verification" or "password-reset"
    
    public EmailSendRequestDTO() {}
    
    public EmailSendRequestDTO(String email, String type) {
        this.email = email;
        this.type = type;
    }
    
    public String getEmail() {
        return email;
    }
    
    public void setEmail(String email) {
        this.email = email;
    }
    
    public String getType() {
        return type;
    }
    
    public void setType(String type) {
        this.type = type;
    }
    
    @Override
    public String toString() {
        return "EmailSendRequestDTO{" +
                "email='" + email + '\'' +
                ", type='" + type + '\'' +
                '}';
    }
}
