package com.ohgiraffers.tomatolab_imean.members.service;

import com.ohgiraffers.tomatolab_imean.members.model.common.MemberRole;
import com.ohgiraffers.tomatolab_imean.members.model.common.MemberStatus;
import com.ohgiraffers.tomatolab_imean.members.model.entity.Members;
import com.ohgiraffers.tomatolab_imean.members.repository.MemberRepository;
import jakarta.transaction.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.crossstore.ChangeSetPersister;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class MemberService {

    private final MemberRepository memberRepository;
    private final PasswordEncoder passwordEncoder;

    @Autowired
    public MemberService(MemberRepository memberRepository, PasswordEncoder passwordEncoder) {
        this.memberRepository = memberRepository;
        this.passwordEncoder = passwordEncoder;
    }
    
    /**
     * API용 회원 가입 메서드
     */
    @Transactional
    public Members register(String memberCode, String memberPass, String memberNickName,
                          String memberEmail, String memberPhone) {
        // 중복 검사
        if (memberRepository.existsByMemberCode(memberCode)) {
            throw new IllegalArgumentException("이미 사용 중인 회원 코드입니다.");
        }

        if (memberRepository.existsByMemberEmail(memberEmail)) {
            throw new IllegalArgumentException("이미 사용 중인 이메일입니다.");
        }

        if (memberRepository.existsByMemberPhone(memberPhone)) {
            throw new IllegalArgumentException("이미 사용 중인 전화번호입니다.");
        }

        // 회원 생성
        Members member = new Members();
        member.setMemberCode(memberCode);
        member.setMemberPass(passwordEncoder.encode(memberPass));
        member.setMemberNickName(memberNickName);
        member.setMemberEmail(memberEmail);
        member.setMemberPhone(memberPhone);
        member.setMemberRole(MemberRole.MEMBER);
        member.setMemberStatus(MemberStatus.ACTIVE);
        member.setMemberCreatedAt(LocalDateTime.now());

        return memberRepository.save(member);
    }
    
    /**
     * API용 프로필 업데이트 메서드
     */
    @Transactional
    public Members updateMemberProfile(Long memberId, String newPassword, String email, String phone) {
        Members member = memberRepository.findById(memberId)
                .orElseThrow(() -> new IllegalArgumentException("회원을 찾을 수 없습니다."));
        
        // 비밀번호 업데이트 (제공된 경우)
        if (newPassword != null && !newPassword.trim().isEmpty()) {
            member.setMemberPass(passwordEncoder.encode(newPassword));
        }
        
        // 이메일 및 전화번호 업데이트
        if (email != null && !email.equals(member.getMemberEmail())) {
            // 이메일 중복 확인
            if (memberRepository.existsByMemberEmail(email) &&
                !member.getMemberEmail().equals(email)) {
                throw new IllegalArgumentException("이미 사용 중인 이메일입니다.");
            }
            member.setMemberEmail(email);
        }
        
        if (phone != null && !phone.equals(member.getMemberPhone())) {
            // 전화번호 중복 확인
            if (memberRepository.existsByMemberPhone(phone) &&
                !member.getMemberPhone().equals(phone)) {
                throw new IllegalArgumentException("이미 사용 중인 전화번호입니다.");
            }
            member.setMemberPhone(phone);
        }
        
        // 업데이트 시간 설정
        member.setMemberUpdatedAt(LocalDateTime.now());
        
        return memberRepository.save(member);
    }

    /**
     * ID로 회원 조회 (트랜잭션 적용)
     */
    @Transactional
    public Members findById(Long id) {
        return memberRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("회원을 찾을 수 없습니다."));
    }

    /**
     * 회원 코드로 회원 검색 (트랜잭션 적용)
     */
    @Transactional
    public Members findByCode(String code) throws ChangeSetPersister.NotFoundException {
        return memberRepository.findByMemberCode(code)
                .orElseThrow(() -> new ChangeSetPersister.NotFoundException());
    }
    
    /**
     * 이메일로 회원 검색 (트랜잭션 적용)
     */
    @Transactional
    public Members findByEmail(String email) throws ChangeSetPersister.NotFoundException {
        return memberRepository.findByMemberEmail(email)
                .orElseThrow(() -> new ChangeSetPersister.NotFoundException());
    }

    /*
     * 중복되지 않는 회원 코드 생성
     */
    public String generateUniqueMemberCode() {
        String memberCode;
        int attempts = 0;
        int maxAttempts = 50; // 무한 루프 방지
        
        do {
            memberCode = generateRandomMemberCode();
            attempts++;
            
            if (attempts > maxAttempts) {
                throw new RuntimeException("고유한 회원 코드 생성에 실패했습니다. 다시 시도해주세요.");
            }
        } while (memberRepository.existsByMemberCode(memberCode));
        
        return memberCode;
    }
    
    /*
     * 랜덤 회원 코드 생성 (6자리)
     */
    private String generateRandomMemberCode() {
        StringBuilder sb = new StringBuilder();
        String characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        java.util.Random random = new java.util.Random();
        
        for (int i = 0; i < 6; i++) {
            int index = random.nextInt(characters.length());
            sb.append(characters.charAt(index));
        }
        
        return sb.toString();
    }

    /**
     * 회원 정보 저장
     */
    @Transactional
    public Members save(Members member) {
        return memberRepository.save(member);
    }
}