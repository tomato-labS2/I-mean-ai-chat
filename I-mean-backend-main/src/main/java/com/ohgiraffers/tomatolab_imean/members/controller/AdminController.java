package com.ohgiraffers.tomatolab_imean.members.controller;

import com.ohgiraffers.tomatolab_imean.common.dto.response.ApiResponseDTO;
import com.ohgiraffers.tomatolab_imean.couple.model.dto.response.CoupleResponseDTO;
import com.ohgiraffers.tomatolab_imean.members.model.common.MemberStatus;
import com.ohgiraffers.tomatolab_imean.members.model.dto.request.AdminUpdateRequestDTO;
import com.ohgiraffers.tomatolab_imean.members.model.dto.response.AdminResponseDTO;
import com.ohgiraffers.tomatolab_imean.members.model.dto.response.PageResponseDTO;
import com.ohgiraffers.tomatolab_imean.members.service.AdminService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.crossstore.ChangeSetPersister;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/admin")
public class AdminController {
    private final AdminService adminService;

    @Autowired
    public AdminController(AdminService adminService) {
        this.adminService = adminService;
    }

    /*
        멤버 상세조회
     */
    @GetMapping("/member/{memberId}")
    public ResponseEntity<ApiResponseDTO<AdminResponseDTO>> getMember(@PathVariable Long memberId) {
        try {
            AdminResponseDTO member = adminService.getMemberById(memberId);
            return ResponseEntity.ok(new ApiResponseDTO<>(true, "멤버 조회 성공", member));
        } catch (ChangeSetPersister.NotFoundException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(new ApiResponseDTO<>(false, "멤버를 찾을 수 없습니다.", null));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ApiResponseDTO<>(false, "서버 오류가 발생했습니다.", null));
        }
    }

    /*
    멤버 전체 조회
     */
    @GetMapping("/members")
    public ResponseEntity<ApiResponseDTO<List<AdminResponseDTO>>> getAllMembers() {
        try {
            List<AdminResponseDTO> members = adminService.getAllMembers();
            return ResponseEntity.ok(new ApiResponseDTO<>(true, "멤버 전체 조회 성공", members));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ApiResponseDTO<>(false, "서버 오류가 발생했습니다.", null));
        }
    }

    /*
    멤버 수정
     */
    @PutMapping("/member/{memberId}")
    public ResponseEntity<ApiResponseDTO<AdminResponseDTO>> updateMember(
            @PathVariable Long memberId,
            @RequestBody AdminUpdateRequestDTO updateRequest) {
        try {
            AdminResponseDTO updatedMember = adminService.updateMember(memberId, updateRequest);
            return ResponseEntity.ok(new ApiResponseDTO<>(true, "멤버 수정 성공", updatedMember));
        } catch (ChangeSetPersister.NotFoundException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(new ApiResponseDTO<>(false, "멤버를 찾을 수 없습니다.", null));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ApiResponseDTO<>(false, "서버 오류가 발생했습니다.", null));
        }
    }

    /*
    멤버 상태 변경
     */
    @PatchMapping("/member/{memberId}/status")
    public ResponseEntity<ApiResponseDTO<AdminResponseDTO>> updateMemberStatus(
            @PathVariable Long memberId,
            @RequestParam MemberStatus status) {
        try {
            AdminResponseDTO updatedMember = adminService.updateMemberStatus(memberId, status);
            return ResponseEntity.ok(new ApiResponseDTO<>(true, "멤버 상태 변경 성공", updatedMember));
        } catch (ChangeSetPersister.NotFoundException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(new ApiResponseDTO<>(false, "멤버를 찾을 수 없습니다.", null));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ApiResponseDTO<>(false, "서버 오류가 발생했습니다.", null));
        }
    }

    /*
    멤버 삭제(물리적)
     */
    @DeleteMapping("/member/{memberId}")
    public ResponseEntity<ApiResponseDTO<String>> deleteMember(@PathVariable Long memberId) {
        try {
            adminService.deleteMember(memberId);
            return ResponseEntity.ok(new ApiResponseDTO<>(true, "멤버 삭제 성공", "멤버가 성공적으로 삭제되었습니다."));
        } catch (ChangeSetPersister.NotFoundException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(new ApiResponseDTO<>(false, "멤버를 찾을 수 없습니다.", null));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ApiResponseDTO<>(false, "서버 오류가 발생했습니다.", null));
        }
    }

    /*
    커플 조회
     */
    @GetMapping("/couples")
    public ResponseEntity<ApiResponseDTO<List<CoupleResponseDTO>>> getAllCouples() {
        try {
            List<CoupleResponseDTO> couples = adminService.getAllCouples();
            return ResponseEntity.ok(new ApiResponseDTO<>(true, "커플 전체 조회 성공", couples));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ApiResponseDTO<>(false, "서버 오류가 발생했습니다.", null));
        }
    }
}
