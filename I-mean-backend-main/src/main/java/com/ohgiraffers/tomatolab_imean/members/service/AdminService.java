package com.ohgiraffers.tomatolab_imean.members.service;

import com.ohgiraffers.tomatolab_imean.couple.model.dto.response.CoupleResponseDTO;
import com.ohgiraffers.tomatolab_imean.couple.model.entity.Couple;
import com.ohgiraffers.tomatolab_imean.couple.repository.CoupleRepository;
import com.ohgiraffers.tomatolab_imean.members.model.common.MemberStatus;
import com.ohgiraffers.tomatolab_imean.members.model.dto.request.AdminUpdateRequestDTO;
import com.ohgiraffers.tomatolab_imean.members.model.dto.response.AdminResponseDTO;
import com.ohgiraffers.tomatolab_imean.members.model.entity.Members;
import com.ohgiraffers.tomatolab_imean.members.repository.MemberRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.crossstore.ChangeSetPersister;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.StreamSupport;

@Service
@Transactional
public class AdminService {
    private final MemberRepository memberRepository;
    private final CoupleRepository coupleRepository;

    @Autowired
    public AdminService(MemberRepository memberRepository, CoupleRepository coupleRepository) {
        this.memberRepository = memberRepository;
        this.coupleRepository = coupleRepository;
    }

    /*
     * 모든 멤버 조회
     */
    @Transactional(readOnly = true)
    public List<AdminResponseDTO> getAllMembers() {
        Iterable<Members> allMembers = memberRepository.findAll();
        return StreamSupport.stream(allMembers.spliterator(), false)
                .map(this::convertToAdminResponseDTO)
                .collect(Collectors.toList());
    }

    /*
     * 멤버 ID로 특정 멤버 조회
     */
    @Transactional(readOnly = true)
    public Members findById(Long memberId) throws ChangeSetPersister.NotFoundException {
        return memberRepository.findById(memberId)
                .orElseThrow(() -> new ChangeSetPersister.NotFoundException());
    }

    /*
     * 멤버 ID로 특정 멤버 조회 (AdminResponseDTO로 변환)
     */
    @Transactional(readOnly = true)
    public AdminResponseDTO getMemberById(Long memberId) throws ChangeSetPersister.NotFoundException {
        Members member = findById(memberId);
        return convertToAdminResponseDTO(member);
    }

    /*
     * 멤버 정보 수정
     */
    public AdminResponseDTO updateMember(Long memberId, AdminUpdateRequestDTO updateRequest) throws ChangeSetPersister.NotFoundException {
        Members member = findById(memberId);
        
        // 수정할 필드들 업데이트
        if (updateRequest.getMemberNickName() != null && !updateRequest.getMemberNickName().isEmpty()) {
            member.setMemberNickName(updateRequest.getMemberNickName());
        }
        if (updateRequest.getMemberEmail() != null && !updateRequest.getMemberEmail().isEmpty()) {
            member.setMemberEmail(updateRequest.getMemberEmail());
        }
        if (updateRequest.getMemberPhone() != null && !updateRequest.getMemberPhone().isEmpty()) {
            member.setMemberPhone(updateRequest.getMemberPhone());
        }
        if (updateRequest.getMemberRole() != null) {
            member.setMemberRole(updateRequest.getMemberRole());
        }
        if (updateRequest.getMemberStatus() != null) {
            member.setMemberStatus(updateRequest.getMemberStatus());
        }
        
        member.setMemberUpdatedAt(LocalDateTime.now());
        Members updatedMember = memberRepository.save(member);
        
        return convertToAdminResponseDTO(updatedMember);
    }

    /*
     * 멤버 상태 변경
     */
    public AdminResponseDTO updateMemberStatus(Long memberId, MemberStatus newStatus) throws ChangeSetPersister.NotFoundException {
        Members member = findById(memberId);
        member.setMemberStatus(newStatus);
        member.setMemberUpdatedAt(LocalDateTime.now());
        
        // 삭제 상태로 변경하는 경우 삭제 시간 설정(소프트 삭제)s
        if (newStatus == MemberStatus.DELETED) {
            member.setMemberDeletedAt(LocalDateTime.now());
        }
        
        Members updatedMember = memberRepository.save(member);
        return convertToAdminResponseDTO(updatedMember);
    }

    /*
     * 멤버 물리적 삭제
     */
    public void deleteMember(Long memberId) throws ChangeSetPersister.NotFoundException {
        Members member = findById(memberId);
        memberRepository.delete(member);
    }

    /*
     * 모든 커플 조회
     */
    @Transactional(readOnly = true)
    public List<CoupleResponseDTO> getAllCouples() {
        List<Couple> allCouples = coupleRepository.findAll();
        return allCouples.stream()
                .map(CoupleResponseDTO::new)
                .collect(Collectors.toList());
    }
    /*
     * Members 엔티티를 AdminResponseDTO로 변환하는 헬퍼 메서드
     */
    private AdminResponseDTO convertToAdminResponseDTO(Members member) {
        Long coupleId = (member.getCoupleId() != null) ? member.getCoupleId().getCoupleId() : null;
        
        return new AdminResponseDTO(
                member.getMemberId(),
                member.getMemberCode(),
                member.getMemberNickName(),
                member.getMemberEmail(),
                member.getMemberPhone(),
                member.getMemberPass(),
                member.getMemberRole(),
                member.getMemberStatus(),
                coupleId,
                member.getMemberCreatedAt(),
                member.getMemberUpdatedAt(),
                member.getMemberDeletedAt()
        );
    }
}
