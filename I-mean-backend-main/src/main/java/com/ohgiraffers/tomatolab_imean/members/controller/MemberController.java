package com.ohgiraffers.tomatolab_imean.members.controller;

import com.ohgiraffers.tomatolab_imean.auth.jwt.JwtTokenProvider;
import com.ohgiraffers.tomatolab_imean.auth.model.AuthDetails;
import com.ohgiraffers.tomatolab_imean.auth.model.dto.response.LoginResponseDTO;
import com.ohgiraffers.tomatolab_imean.auth.service.AuthService;
import com.ohgiraffers.tomatolab_imean.auth.service.RefreshTokenService;
import com.ohgiraffers.tomatolab_imean.common.dto.response.ApiResponseDTO;
import com.ohgiraffers.tomatolab_imean.common.exception.UnauthorizedException;
import com.ohgiraffers.tomatolab_imean.common.ratelimit.RateLimit;
import com.ohgiraffers.tomatolab_imean.common.ratelimit.RateLimitKeyType;
import com.ohgiraffers.tomatolab_imean.members.model.common.MemberStatus;
import com.ohgiraffers.tomatolab_imean.members.model.dto.request.CompleteRegisterRequestDTO;
import com.ohgiraffers.tomatolab_imean.members.model.dto.request.LoginRequestDTO;
import com.ohgiraffers.tomatolab_imean.members.model.dto.request.ProfileUpdateRequestDTO;
import com.ohgiraffers.tomatolab_imean.members.model.dto.response.MemberResponseDTO;
import com.ohgiraffers.tomatolab_imean.members.model.entity.Members;
import com.ohgiraffers.tomatolab_imean.members.model.entity.RefreshToken;
import com.ohgiraffers.tomatolab_imean.members.repository.RefreshTokenRepository;
import com.ohgiraffers.tomatolab_imean.members.service.MemberService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.crossstore.ChangeSetPersister;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.Random;

/**
 * JWT 기반 회원 관리 컨트롤러
 * 세션을 사용하지 않는 Stateless 방식으로 구현
 */
@RestController
@RequestMapping("/api/member")
public class MemberController {
    
    private final MemberService memberService;
    private final AuthService authService;
    private final AuthenticationManager authenticationManager;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final RefreshTokenService refreshTokenService;
    private final RefreshTokenRepository refreshTokenRepository;
    
    @Autowired
    public MemberController(
            MemberService memberService,
            AuthService authService,
            AuthenticationManager authenticationManager,
            PasswordEncoder passwordEncoder,
            JwtTokenProvider jwtTokenProvider,
            RefreshTokenService refreshTokenService,RefreshTokenRepository refreshTokenRepository ) {
        this.memberService = memberService;
        this.authService = authService;
        this.authenticationManager = authenticationManager;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenProvider = jwtTokenProvider;
        this.refreshTokenService = refreshTokenService;
        this.refreshTokenRepository = refreshTokenRepository;
    }
    
    /**
     * JWT 기반 로그인 처리
     * 성공 시 Access Token과 Refresh Token 반환
     * Rate Limit: 1분에 5회 (브루트포스 공격 방어)
     */
    @RateLimit(requests = 3, window = "1m", keyType = RateLimitKeyType.IP, 
               message = "로그인 시도가 너무 많습니다. 1분 후 다시 시도해주세요.")
    @PostMapping("/login")
    public ResponseEntity<ApiResponseDTO<LoginResponseDTO>> login(@RequestBody LoginRequestDTO request) {
        try {
            // 이메일로 사용자 찾기
            Members member;
            try {
                member = memberService.findByEmail(request.getMemberEmail());
            } catch (ChangeSetPersister.NotFoundException e) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(ApiResponseDTO.error("로그인 실패: 이메일 또는 비밀번호가 일치하지 않습니다."));
            }
            
            // 계정 상태 확인
            if (member.getMemberStatus() != MemberStatus.ACTIVE) {
                return ResponseEntity.status(HttpStatus.FORBIDDEN)
                        .body(ApiResponseDTO.error("계정이 활성화 상태가 아닙니다. 관리자에게 문의하세요."));
            }
            
            // 비밀번호 검증 (클라이언트에서 해시된 비밀번호 처리)
            String clientHashedPassword = request.getMemberPass();
            boolean isPasswordValid = false;
            
            // 클라이언트 해시 비밀번호 검증
            if (clientHashedPassword.contains(":")) {
                // 클라이언트에서 해시된 비밀번호인 경우
                String[] parts = clientHashedPassword.split(":");
                if (parts.length == 2) {
                    String salt = parts[0];
                    String clientHash = parts[1];
                    // 서버에서 재계산하여 검증
                    String serverHash = java.security.MessageDigest.getInstance("SHA-256")
                        .digest((member.getMemberPass() + salt).getBytes())
                        .toString();
                    isPasswordValid = serverHash.equals(clientHash);
                }
            } else {
                // 기존 방식 (서버에서 직접 검증)
                isPasswordValid = passwordEncoder.matches(request.getMemberPass(), member.getMemberPass());
            }
            
            if (!isPasswordValid) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(ApiResponseDTO.error("로그인 실패: 이메일 또는 비밀번호가 일치하지 않습니다."));
            }
            
            // Spring Security 인증 (비밀번호 검증 완료 후)
            Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(member.getMemberCode(), member.getMemberPass())
            );
            
            // 🆕 JWT 토큰 생성 (member_id + coupleId 포함)
            String accessToken = jwtTokenProvider.createAccessToken(
                member.getMemberId(),           // 회원 ID
                member.getMemberCode(), 
                member.getCoupleStatusString(), 
                member.getMemberRole().name(),
                member.getCoupleIdAsLong()      // 🆕 커플 ID (null 가능)
            );
            
            // 🆕 Refresh Token 생성 (member_id 포함)
            // 로그인 시 기존 토큰 모두 삭제 후 새로 생성 (보안 강화)
            refreshTokenService.deleteAllUserTokens(member.getMemberCode());
            String refreshToken = refreshTokenService.createAndSaveRefreshToken(
                member.getMemberId(),           // 🆕 member_id 추가
                member.getMemberCode()
            );

//            refreshTokenRepository.save(refreshToken);
            
            // 토큰 만료 시간 계산 (밀리초를 초로 변환)
            long expiresIn = jwtTokenProvider.getJwtProperties().getAccessTokenExpiration() / 1000;
            
            // 사용자 정보 생성
            MemberResponseDTO memberInfo = new MemberResponseDTO(member);
            
            // 응답 DTO 생성
            LoginResponseDTO loginResponse = new LoginResponseDTO(
                accessToken, 
                refreshToken, 
                expiresIn, 
                memberInfo
            );
            
            return ResponseEntity.ok(ApiResponseDTO.success("로그인 성공", loginResponse));
            
        } catch (AuthenticationException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponseDTO.error("로그인 실패: 이메일 또는 비밀번호가 일치하지 않습니다."));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponseDTO.error("서버 오류가 발생했습니다: " + e.getMessage()));
        }
    }
    
    /**
     * 원스텝 회원가입 (JWT 방식)
     * 모든 정보를 한 번에 받아서 처리
     * Rate Limit: 10분에 3회 (스팸 가입 방지)
     */
    @RateLimit(requests = 3, window = "10m", keyType = RateLimitKeyType.IP,
               message = "회원가입 시도가 너무 많습니다. 10분 후 다시 시도해주세요.")
    @PostMapping("/register")
    public ResponseEntity<ApiResponseDTO<LoginResponseDTO>> register(@RequestBody CompleteRegisterRequestDTO request) {
        try {
            // 1. 입력값 검증
            if (!isValidRegisterRequest(request)) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(ApiResponseDTO.error("필수 정보가 누락되었습니다. 모든 필드를 입력해주세요."));
            }
            
            // 2. 이메일 중복 체크
            try {
                memberService.findByEmail(request.getMemberEmail());
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(ApiResponseDTO.error("이미 사용 중인 이메일입니다."));
            } catch (ChangeSetPersister.NotFoundException e) {
                // 중복되지 않음 - 정상
            }
            
            // 3. 회원 코드 생성 (중복 체크 포함)
            String memberCode = memberService.generateUniqueMemberCode();
            
            // 4. 회원 등록
            Members newMember = memberService.register(
                memberCode,
                request.getMemberPass(),
                request.getMemberNickName(),
                request.getMemberEmail(),
                request.getMemberPhone()
            );
            
            // 🆕 5. JWT 토큰 생성 (member_id + coupleId 포함)
            String accessToken = jwtTokenProvider.createAccessToken(
                newMember.getMemberId(),        // 회원 ID
                newMember.getMemberCode(), 
                newMember.getCoupleStatusString(), 
                newMember.getMemberRole().name(),
                newMember.getCoupleIdAsLong()   // 🆕 커플 ID (회원가입 시는 null)
            );
            
            // 🆕 Refresh Token 생성 (member_id 포함)
            String refreshToken = refreshTokenService.createAndSaveRefreshToken(
                newMember.getMemberId(),        // 🆕 member_id 추가
                newMember.getMemberCode()
            );
            
            // 6. 토큰 만료 시간 계산
            long expiresIn = jwtTokenProvider.getJwtProperties().getAccessTokenExpiration() / 1000;
            
            // 7. 응답 생성
            MemberResponseDTO memberInfo = new MemberResponseDTO(newMember);
            LoginResponseDTO loginResponse = new LoginResponseDTO(
                accessToken, 
                refreshToken, 
                expiresIn, 
                memberInfo
            );
            
            return ResponseEntity.ok(ApiResponseDTO.success("회원가입 성공", loginResponse));
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponseDTO.error("회원가입 실패: " + e.getMessage()));
        }
    }
    
    /**
     * 이메일 중복 체크 API
     * 회원가입 전 이메일 유효성 검사용
     * Rate Limit: 1분에 10회 (적당한 제한)
     */
    @RateLimit(requests = 10, window = "1m", keyType = RateLimitKeyType.IP,
               message = "이메일 중복 체크 요청이 너무 많습니다. 1분 후 다시 시도해주세요.")
    @PostMapping("/check-email")
    public ResponseEntity<ApiResponseDTO<Boolean>> checkEmailAvailability(@RequestBody String email) {
        try {
            memberService.findByEmail(email);
            // 이메일이 존재하면 사용 불가
            return ResponseEntity.ok(ApiResponseDTO.success("이메일 중복 체크 완료", false));
        } catch (ChangeSetPersister.NotFoundException e) {
            // 이메일이 존재하지 않으면 사용 가능
            return ResponseEntity.ok(ApiResponseDTO.success("이메일 중복 체크 완료", true));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponseDTO.error("서버 오류: " + e.getMessage()));
        }
    }
    
    /**
     * 회원 프로필 조회 (JWT 인증 필요)
     */
    @GetMapping("/profile")
    public ResponseEntity<ApiResponseDTO<MemberResponseDTO>> getProfile(Authentication authentication) {
        try {
            Members member = getCurrentMember(authentication);
            
            if (member.getMemberStatus() != MemberStatus.ACTIVE) {
                return ResponseEntity.status(HttpStatus.FORBIDDEN)
                        .body(ApiResponseDTO.error("계정이 활성화 상태가 아닙니다"));
            }
            
            MemberResponseDTO responseDTO = new MemberResponseDTO(member);
            return ResponseEntity.ok(ApiResponseDTO.success("프로필 조회 성공", responseDTO));
        } catch (UnauthorizedException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponseDTO.error(e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponseDTO.error("서버 오류: " + e.getMessage()));
        }
    }
    
    /**
     * 비밀번호 확인
     */
    @PostMapping("/verify-password")
    public ResponseEntity<ApiResponseDTO<Boolean>> verifyPassword(
            Authentication authentication, 
            @RequestBody ProfileUpdateRequestDTO request) {
        try {
            Members member = getCurrentMember(authentication);
            
            if (member.getMemberStatus() != MemberStatus.ACTIVE) {
                return ResponseEntity.status(HttpStatus.FORBIDDEN)
                        .body(ApiResponseDTO.error("계정이 활성화 상태가 아닙니다"));
            }
            
            boolean isValid = passwordEncoder.matches(request.getCurrentPassword(), member.getMemberPass());
            
            if (isValid) {
                return ResponseEntity.ok(ApiResponseDTO.success("비밀번호 확인 성공", true));
            } else {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(ApiResponseDTO.error("비밀번호가 일치하지 않습니다"));
            }
        } catch (UnauthorizedException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponseDTO.error(e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponseDTO.error("서버 오류: " + e.getMessage()));
        }
    }
    
    /*
     * 프로필 업데이트
     */
    @PutMapping("/profile")
    public ResponseEntity<ApiResponseDTO<MemberResponseDTO>> updateProfile(
            Authentication authentication,
            @RequestBody ProfileUpdateRequestDTO request) {
        try {
            Members member = getCurrentMember(authentication);
            
            if (member.getMemberStatus() != MemberStatus.ACTIVE) {
                return ResponseEntity.status(HttpStatus.FORBIDDEN)
                        .body(ApiResponseDTO.error("계정이 활성화 상태가 아닙니다"));
            }
            
            // 현재 비밀번호 확인 (비밀번호 변경 시에만)
            if (request.getNewPassword() != null && !request.getNewPassword().isEmpty()) {
                if (request.getCurrentPassword() == null || 
                    !passwordEncoder.matches(request.getCurrentPassword(), member.getMemberPass())) {
                    return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                            .body(ApiResponseDTO.error("현재 비밀번호가 일치하지 않습니다"));
                }
            }
            
            // 업데이트 처리
            Members updatedMember = memberService.updateMemberProfile(
                member.getMemberId(),
                request.getNewPassword(),
                request.getMemberEmail(),
                request.getMemberPhone()
            );
            
            MemberResponseDTO responseDTO = new MemberResponseDTO(updatedMember);
            
            // 비밀번호 변경한 경우 토큰 재발급 알림
            if (request.getNewPassword() != null && !request.getNewPassword().isEmpty()) {
                return ResponseEntity.ok(ApiResponseDTO.success(
                        "프로필 업데이트 성공. 비밀번호가 변경되었습니다. 보안을 위해 다시 로그인해주세요.", 
                        responseDTO));
            } else {
                return ResponseEntity.ok(ApiResponseDTO.success("프로필 업데이트 성공", responseDTO));
            }
        } catch (UnauthorizedException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponseDTO.error(e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponseDTO.error("서버 오류: " + e.getMessage()));
        }
    }
    
    // ========== 헬퍼 메서드들 ==========
    
    /**
     * 🆕 현재 인증된 회원 정보 조회 헬퍼 메서드 (member_id 지원)
     */
    private Members getCurrentMember(Authentication authentication) {
        if (authentication == null || !authentication.isAuthenticated()) {
            throw new UnauthorizedException("인증이 필요합니다");
        }
        
        try {
            AuthDetails authDetails = (AuthDetails) authentication.getPrincipal();
            
            // 🆕 member_id가 있으면 ID로 조회, 없으면 Code로 조회 (하위 호환성)
            if (authDetails.getMemberId() != null) {
                return memberService.findById(authDetails.getMemberId());
            } else {
                return memberService.findByCode(authDetails.getMemberCode());
            }
        } catch (ChangeSetPersister.NotFoundException e) {
            throw new UnauthorizedException("회원 정보를 찾을 수 없습니다");
        }
    }
    
    /*
     * 회원가입 요청 유효성 검사
     */
    private boolean isValidRegisterRequest(CompleteRegisterRequestDTO request) {
        return request.getMemberEmail() != null && !request.getMemberEmail().trim().isEmpty() &&
               request.getMemberPass() != null && !request.getMemberPass().trim().isEmpty() &&
               request.getMemberNickName() != null && !request.getMemberNickName().trim().isEmpty() &&
               request.getMemberPhone() != null && !request.getMemberPhone().trim().isEmpty();
    }
}