package com.ohgiraffers.tomatolab_imean.couple.model.dto.response;

import com.ohgiraffers.tomatolab_imean.couple.model.entity.Couple;

import java.time.LocalDateTime;

public class CoupleResponseDTO {
    private Long coupleId;
    private LocalDateTime createdAt;
    private String status;
    
    // 생성자
    public CoupleResponseDTO() {
    }
    
    public CoupleResponseDTO(Couple couple) {
        this.coupleId = couple.getCoupleId();
        this.createdAt = couple.getCreatedAt();
        this.status = couple.getStatus().name();
    }
    
    // getter, setter
    public Long getCoupleId() {
        return coupleId;
    }

    public void setCoupleId(Long coupleId) {
        this.coupleId = coupleId;
    }


    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }
}