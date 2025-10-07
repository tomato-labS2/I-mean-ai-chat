package com.ohgiraffers.tomatolab_imean.couple.service;


import com.ohgiraffers.tomatolab_imean.couple.model.common.CoupleStatus;
import com.ohgiraffers.tomatolab_imean.couple.model.dto.response.CoupleStatusResponseDTO;
import com.ohgiraffers.tomatolab_imean.couple.model.entity.Couple;
import com.ohgiraffers.tomatolab_imean.couple.repository.CoupleRepository;
import com.ohgiraffers.tomatolab_imean.members.model.entity.Members;
import com.ohgiraffers.tomatolab_imean.members.service.MemberService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.crossstore.ChangeSetPersister.NotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.Random;

@Service
public class CoupleService {

    private final CoupleRepository coupleRepository;
    private final MemberService memberService;

    @Autowired
    public CoupleService(CoupleRepository coupleRepository, MemberService memberService) {
        this.coupleRepository = coupleRepository;
        this.memberService = memberService;
    }

    /**
     * 현재 멤버가 커플인지 확인
     */
    public boolean isAlreadyInCouple(Members member) {
        return coupleRepository.existsByMember1OrMember2(member, member);
    }



    /**
     * 멤버 ID로 커플 정보 조회
     */
    public Optional<Couple> findCoupleByMember(Members member) {
        return coupleRepository.findByMember1OrMember2(member, member);
    }

    public  Optional<Couple> findCoupleId(Long CoupleId) {
        return coupleRepository.findById(CoupleId);
    }

    /**
     * 커플 등록 처리
     */
    @Transactional
    public Couple registerCouple(Members currentMember, String targetMemberCode) throws NotFoundException {
        // 대상 멤버 조회
        Members targetMember = memberService.findByCode(targetMemberCode);
        
        // 자기 자신인지 확인
        if (currentMember.getMemberId().equals(targetMember.getMemberId())) {
            throw new IllegalArgumentException("자신의 코드는 입력할 수 없습니다.");
        }
        
        // 이미 커플인지 확인
        if (isAlreadyInCouple(currentMember)) {
            throw new IllegalStateException("이미 커플 관계가 존재합니다.");
        }
        
        // 상대방이 이미 커플인지 확인
        if (isAlreadyInCouple(targetMember)) {
            throw new IllegalStateException("상대방이 이미 커플 관계에 있습니다.");
        }
        
        // 커플 코드 생성
//        String coupleCode = generateCoupleCode();
        
        // 새 커플 생성
        Couple newCouple = new Couple();
        newCouple.setMember1(currentMember);
        newCouple.setMember2(targetMember);

        newCouple.setCreatedAt(LocalDateTime.now());
        newCouple.setStatus(CoupleStatus.ACTIVE);

        // 커플 저장
        Couple savedCouple = coupleRepository.save(newCouple);
        
        // 회원 정보 업데이트 - 각 멤버에 커플 ID 설정
        currentMember.setCoupleId(savedCouple);
        targetMember.setCoupleId(savedCouple);
        
        // 멤버 정보 저장
        memberService.save(currentMember);
        memberService.save(targetMember);
        
        return savedCouple;
    }

    /**
     * 커플 해제 처리
     */
    @Transactional
    public void breakCouple(Members currentMember) throws NotFoundException {
        // 현재 사용자의 커플 관계 조회
        Optional<Couple> coupleOptional = findCoupleByMember(currentMember);
        
        if (coupleOptional.isEmpty()) {
            throw new IllegalStateException("현재 커플 관계가 존재하지 않습니다.");
        }
        
        Couple couple = coupleOptional.get();
        
        // 상대방 조회
        Members partner = getPartner(couple, currentMember);
        
        // 커플 상태를 ENDED로 변경
        couple.setStatus(CoupleStatus.ENDED);
        coupleRepository.save(couple);
        
        // 두 멤버의 coupleId를 null로 설정
        currentMember.setCoupleId(null);
        partner.setCoupleId(null);
        
        // 멤버 정보 저장
        memberService.save(currentMember);
        memberService.save(partner);
        
        System.out.println("커플 해제 완료: " + currentMember.getMemberCode() + " <-> " + partner.getMemberCode());
    }

    /**
     * Polling API용 - 가벼운 커플 상태 확인 (memberID로)
     * 빠른 응답을 위해 최소한의 정보만 조회
     */
    public CoupleStatusResponseDTO getCoupleStatusByMemberID(Long memberID) {
        Optional<Couple> coupleOptional = coupleRepository.findByMember1_MemberIdOrMember2_MemberId(memberID, memberID);
        
        if (coupleOptional.isEmpty()) {
            return CoupleStatusResponseDTO.notMatched();
        }
        
        Couple couple = coupleOptional.get();
        
        // 커플 상태가 ACTIVE인지 확인
        if (couple.getStatus() != CoupleStatus.ACTIVE) {
            return CoupleStatusResponseDTO.notMatched();
        }
        
        // 파트너 정보 확인
        Members partner;
        if (couple.getMember1().getMemberId().equals(memberID)) {
            partner = couple.getMember2();
        } else {
            partner = couple.getMember1();
        }
        
        return CoupleStatusResponseDTO.matched(
            partner.getMemberId(),
            partner.getMemberCode(),
            partner.getMemberNickName()
        );
    }

    /**
     * 커플의 파트너 찾기
     */
    public Members getPartner(Couple couple, Members currentMember) {
        if (couple.getMember1().getMemberId().equals(currentMember.getMemberId())) {
            return couple.getMember2();
        } else {
            return couple.getMember1();
        }
    }
}
