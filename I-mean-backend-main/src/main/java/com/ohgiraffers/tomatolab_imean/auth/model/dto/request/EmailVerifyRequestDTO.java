package com.ohgiraffers.tomatolab_imean.auth.model.dto.request;

/**
 * 이메일 인증 코드 검증 요청 DTO
 */
public class EmailVerifyRequestDTO {
    
    private String email;
    private String code;
    private String type; // "verification" or "password-reset"
    
    public EmailVerifyRequestDTO() {}
    
    public EmailVerifyRequestDTO(String email, String code, String type) {
        this.email = email;
        this.code = code;
        this.type = type;
    }
    
    public String getEmail() {
        return email;
    }
    
    public void setEmail(String email) {
        this.email = email;
    }
    
    public String getCode() {
        return code;
    }
    
    public void setCode(String code) {
        this.code = code;
    }
    
    public String getType() {
        return type;
    }
    
    public void setType(String type) {
        this.type = type;
    }
    
    @Override
    public String toString() {
        return "EmailVerifyRequestDTO{" +
                "email='" + email + '\'' +
                ", code='" + "[PROTECTED]" + '\'' +  // 보안상 코드는 로그에 노출하지 않음
                ", type='" + type + '\'' +
                '}';
    }
}
