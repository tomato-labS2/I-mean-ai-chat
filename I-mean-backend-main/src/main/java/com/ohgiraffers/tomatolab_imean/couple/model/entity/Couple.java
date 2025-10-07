package com.ohgiraffers.tomatolab_imean.couple.model.entity;


import com.ohgiraffers.tomatolab_imean.couple.model.common.CoupleStatus;
import com.ohgiraffers.tomatolab_imean.members.model.entity.Members;
import jakarta.persistence.*;

import java.time.LocalDateTime;

@Entity
@Table(name = "couples")
public class Couple {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "couple_id")
    private Long coupleId;

    @ManyToOne
    @JoinColumn(name = "member_id_1")
    private Members member1;

    @ManyToOne
    @JoinColumn(name = "member_id_2")
    private Members member2;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Enumerated(EnumType.STRING)
    private CoupleStatus status = CoupleStatus.ACTIVE;
    
    // 기본 생성자
    public Couple() {
    }

    public Couple(Members member1, Members member2, String coupleCode, LocalDateTime createdAt, CoupleStatus status) {
        this.member1 = member1;
        this.member2 = member2;
        this.createdAt = createdAt;
        this.status = status;
    }

    public Long getCoupleId() {
        return coupleId;
    }

    public void setCoupleId(Long coupleId) {
        this.coupleId = coupleId;
    }

    public Members getMember1() {
        return member1;
    }

    public void setMember1(Members member1) {
        this.member1 = member1;
    }

    public Members getMember2() {
        return member2;
    }

    public void setMember2(Members member2) {
        this.member2 = member2;
    }


    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public CoupleStatus getStatus() {
        return status;
    }

    public void setStatus(CoupleStatus status) {
        this.status = status;
    }

    @Override
    public String toString() {
        return "Couple{" +
                "coupleId=" + coupleId +
                ", member1=" + member1 +
                ", member2=" + member2 + 
                ", createdAt=" + createdAt +
                ", status=" + status +
                '}';
    }
}