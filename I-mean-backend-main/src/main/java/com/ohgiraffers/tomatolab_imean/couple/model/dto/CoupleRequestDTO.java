package com.ohgiraffers.tomatolab_imean.couple.model.dto;

public class CoupleRequestDTO {
    private String targetMemberCode;

    public CoupleRequestDTO() {
    }

    public CoupleRequestDTO(String targetUserCode) {
        this.targetMemberCode = targetMemberCode;
    }

    public String getTargetMemberCode() {
        return targetMemberCode;
    }

    public void setTargetMemberCode(String targetUserCode) {
        this.targetMemberCode = targetMemberCode;
    }
}