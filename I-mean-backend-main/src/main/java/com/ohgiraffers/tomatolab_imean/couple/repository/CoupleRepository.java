package com.ohgiraffers.tomatolab_imean.couple.repository;


import com.ohgiraffers.tomatolab_imean.couple.model.entity.Couple;
import com.ohgiraffers.tomatolab_imean.members.model.entity.Members;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface CoupleRepository extends JpaRepository<Couple, Long> {
    Optional<Couple> findByMember1OrMember2(Members member1, Members member2);
    boolean existsByMember1OrMember2(Members member1, Members member2);
    
    // Polling API용 - 가벼운 조회를 위한 메서드
    Optional<Couple> findByMember1_MemberIdOrMember2_MemberId(Long memberId1, Long memberId2);
    
}