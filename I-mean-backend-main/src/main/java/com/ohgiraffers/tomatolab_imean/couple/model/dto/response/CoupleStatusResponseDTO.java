package com.ohgiraffers.tomatolab_imean.couple.model.dto.response;

/**
 * 커플 상태 조회 응답 DTO (Polling용)
 */
public class CoupleStatusResponseDTO {
    
    private boolean matched;
    private Long partnerId;
    private String partnerCode;
    private String partnerNickname;
    
    public CoupleStatusResponseDTO() {
    }
    
    public CoupleStatusResponseDTO(boolean matched, Long partnerId, String partnerCode, String partnerNickname) {
        this.matched = matched;
        this.partnerId = partnerId;
        this.partnerCode = partnerCode;
        this.partnerNickname = partnerNickname;
    }
    
    // 매칭되지 않은 경우 생성자
    public static CoupleStatusResponseDTO notMatched() {
        return new CoupleStatusResponseDTO(false, null, null, null);
    }
    
    // 매칭된 경우 생성자
    public static CoupleStatusResponseDTO matched(Long partnerId, String partnerCode, String partnerNickname) {
        return new CoupleStatusResponseDTO(true, partnerId, partnerCode, partnerNickname);
    }
    
    public boolean isMatched() {
        return matched;
    }
    
    public void setMatched(boolean matched) {
        this.matched = matched;
    }
    
    public Long getPartnerId() {
        return partnerId;
    }
    
    public void setPartnerId(Long partnerId) {
        this.partnerId = partnerId;
    }
    
    public String getPartnerCode() {
        return partnerCode;
    }
    
    public void setPartnerCode(String partnerCode) {
        this.partnerCode = partnerCode;
    }
    
    public String getPartnerNickname() {
        return partnerNickname;
    }
    
    public void setPartnerNickname(String partnerNickname) {
        this.partnerNickname = partnerNickname;
    }
    
    @Override
    public String toString() {
        return "CoupleStatusResponseDTO{" +
                "matched=" + matched +
                ", partnerId=" + partnerId +
                ", partnerCode='" + partnerCode + '\'' +
                ", partnerNickname='" + partnerNickname + '\'' +
                '}';
    }
}
