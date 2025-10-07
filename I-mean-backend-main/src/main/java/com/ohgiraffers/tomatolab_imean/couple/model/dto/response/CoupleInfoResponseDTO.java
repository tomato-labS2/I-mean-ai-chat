package com.ohgiraffers.tomatolab_imean.couple.model.dto.response;

import com.ohgiraffers.tomatolab_imean.couple.model.entity.Couple;
import com.ohgiraffers.tomatolab_imean.members.model.dto.response.MemberResponseDTO;
import com.ohgiraffers.tomatolab_imean.members.model.entity.Members;

public class CoupleInfoResponseDTO {
    private CoupleResponseDTO coupleInfo;
    private MemberResponseDTO currentMember;
    private MemberResponseDTO partner;
    
    // 생성자
    public CoupleInfoResponseDTO() {
    }
    
    public CoupleInfoResponseDTO(Couple couple, Members currentMember, Members partner) {
        this.coupleInfo = new CoupleResponseDTO(couple);
        this.currentMember = new MemberResponseDTO(currentMember);
        this.partner = new MemberResponseDTO(partner);
    }
    
    // getter, setter
    public CoupleResponseDTO getCoupleInfo() {
        return coupleInfo;
    }

    public void setCoupleInfo(CoupleResponseDTO coupleInfo) {
        this.coupleInfo = coupleInfo;
    }

    public MemberResponseDTO getCurrentMember() {
        return currentMember;
    }

    public void setCurrentMember(MemberResponseDTO currentMember) {
        this.currentMember = currentMember;
    }

    public MemberResponseDTO getPartner() {
        return partner;
    }

    public void setPartner(MemberResponseDTO partner) {
        this.partner = partner;
    }
}