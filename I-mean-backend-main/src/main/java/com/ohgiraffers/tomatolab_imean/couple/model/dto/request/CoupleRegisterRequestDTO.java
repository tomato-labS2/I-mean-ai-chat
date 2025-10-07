package com.ohgiraffers.tomatolab_imean.couple.model.dto.request;

public class CoupleRegisterRequestDTO {
    private String targetMemberCode;

    public CoupleRegisterRequestDTO() {
    }

    public CoupleRegisterRequestDTO(String targetMemberCode) {
        this.targetMemberCode = targetMemberCode;
    }

    public String getTargetMemberCode() {
        return targetMemberCode;
    }

    public void setTargetMemberCode(String targetMemberCode) {
        this.targetMemberCode = targetMemberCode;
    }
}