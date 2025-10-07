package com.ohgiraffers.tomatolab_imean.auth.controller;

import com.ohgiraffers.tomatolab_imean.auth.exception.RefreshTokenNotFoundException;
import com.ohgiraffers.tomatolab_imean.auth.jwt.JwtTokenProvider;
import com.ohgiraffers.tomatolab_imean.auth.model.AuthDetails;
import com.ohgiraffers.tomatolab_imean.auth.model.dto.request.EmailSendRequestDTO;
import com.ohgiraffers.tomatolab_imean.auth.model.dto.request.EmailVerifyRequestDTO;
import com.ohgiraffers.tomatolab_imean.auth.model.dto.request.RefreshTokenRequestDTO;
import com.ohgiraffers.tomatolab_imean.auth.model.dto.response.TokenResponseDTO;
import com.ohgiraffers.tomatolab_imean.auth.service.EmailService;
import com.ohgiraffers.tomatolab_imean.auth.service.RefreshTokenService;
import com.ohgiraffers.tomatolab_imean.auth.service.VerificationCodeService;
import com.ohgiraffers.tomatolab_imean.common.dto.response.ApiResponseDTO;
import com.ohgiraffers.tomatolab_imean.common.ratelimit.RateLimit;
import com.ohgiraffers.tomatolab_imean.common.ratelimit.RateLimitKeyType;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

/**
 * JWT 인증 관련 컨트롤러
 * 토큰 갱신, 인증 상태 확인, 로그아웃 등
 */
@RestController
@RequestMapping("/api/auth")
public class AuthController {
    
    private final JwtTokenProvider jwtTokenProvider;
    private final RefreshTokenService refreshTokenService;
    private final EmailService emailService;
    private final VerificationCodeService verificationCodeService;
    private final com.ohgiraffers.tomatolab_imean.members.service.MemberService memberService;
    
    public AuthController(JwtTokenProvider jwtTokenProvider, RefreshTokenService refreshTokenService,
                         EmailService emailService, VerificationCodeService verificationCodeService,
                         com.ohgiraffers.tomatolab_imean.members.service.MemberService memberService) {
        this.jwtTokenProvider = jwtTokenProvider;
        this.refreshTokenService = refreshTokenService;
        this.emailService = emailService;
        this.verificationCodeService = verificationCodeService;
        this.memberService = memberService;
    }
    
    /**
     * 현재 인증 상태 확인
     * JWT 토큰이 유효한지 확인
     */
    @GetMapping("/check")
    public ResponseEntity<ApiResponseDTO<Object>> checkAuthStatus(Authentication authentication) {
        if (authentication != null && authentication.isAuthenticated()) {
            return ResponseEntity.ok(ApiResponseDTO.success("인증되었습니다.", null));
        } else {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponseDTO.error("인증이 필요합니다."));
        }
    }
    
    /**
     * Refresh Token으로 새로운 Access Token 발급
     * Access Token 만료 시 사용
     * Rate Limit: 1분에 10회 (적당한 제한)
     */
    @RateLimit(requests = 10, window = "1m", keyType = RateLimitKeyType.IP,
               message = "토큰 갱신 요청이 너무 많습니다. 1분 후 다시 시도해주세요.")
    @PostMapping("/refresh")
    public ResponseEntity<ApiResponseDTO<TokenResponseDTO>> refreshToken(@RequestBody RefreshTokenRequestDTO request) {
        try {
            String refreshToken = request.getRefreshToken();

            if (refreshToken == null || refreshToken.trim().isEmpty()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(ApiResponseDTO.error("Refresh Token이 필요합니다."));
            }
            
            // 토큰에서 회원 코드 추출
            String memberCode = jwtTokenProvider.getMemberCodeFromToken(refreshToken);
            
            // 회원 정보 조회해서 현재 커플 상태 확인
            try {
                com.ohgiraffers.tomatolab_imean.members.model.entity.Members member = 
                    memberService.findByCode(memberCode);
                
                // 새로운 Access Token 생성 (현재 커플 상태 포함)
                String newAccessToken = jwtTokenProvider.createAccessToken(
                    member.getMemberId(),            // 🆕 회원 ID 추가
                    member.getMemberCode(),
                    member.getCoupleStatusString(),
                    member.getMemberRole().name(),
                    member.getCoupleIdAsLong()       // 🆕 커플 ID 추가
                );
                
                long expiresIn = jwtTokenProvider.getJwtProperties().getAccessTokenExpiration() / 1000;
                
                // 응답 생성
                TokenResponseDTO tokenResponse = new TokenResponseDTO(newAccessToken, expiresIn);
                
                return ResponseEntity.ok(ApiResponseDTO.success("토큰 갱신 성공", tokenResponse));
                
            } catch (org.springframework.data.crossstore.ChangeSetPersister.NotFoundException e) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(ApiResponseDTO.error("사용자 정보를 찾을 수 없습니다"));
            }
            
        } catch (RefreshTokenNotFoundException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponseDTO.error(e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponseDTO.error("토큰 갱신 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }
    
    /**
     * Access Token과 Refresh Token 모두 갱신 (토큰 로테이션)
     * 보안성을 높이기 위해 Refresh Token도 함께 갱신
     * Rate Limit: 1분에 5회 (보안상 더 엄격)
     */
    @RateLimit(requests = 5, window = "1m", keyType = RateLimitKeyType.IP,
               message = "토큰 로테이션 요청이 너무 많습니다. 1분 후 다시 시도해주세요.")
    @PostMapping("/refresh-rotate")
    public ResponseEntity<ApiResponseDTO<TokenResponseDTO>> refreshWithRotation(@RequestBody RefreshTokenRequestDTO request) {
        try {
            String refreshToken = request.getRefreshToken();
            
            // Refresh Token 유효성 검사
            if (refreshToken == null || refreshToken.trim().isEmpty()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(ApiResponseDTO.error("Refresh Token이 필요합니다."));
            }
            
            // 토큰에서 회원 코드 추출
            String memberCode = jwtTokenProvider.getMemberCodeFromToken(refreshToken);
            
            // 회원 정보 조회해서 현재 커플 상태 확인
            try {
                com.ohgiraffers.tomatolab_imean.members.model.entity.Members member = 
                    memberService.findByCode(memberCode);
                
                // 토큰 로테이션 수행
                String[] newTokens = refreshTokenService.rotateTokens(refreshToken);
                String newAccessToken = jwtTokenProvider.createAccessToken(
                    member.getMemberId(),            // 🆕 회원 ID 추가
                    member.getMemberCode(),
                    member.getCoupleStatusString(),
                    member.getMemberRole().name(),
                    member.getCoupleIdAsLong()       // 🆕 커플 ID 추가
                );
                String newRefreshToken = newTokens[1];
                
                long expiresIn = jwtTokenProvider.getJwtProperties().getAccessTokenExpiration() / 1000;
                
                // 응답 생성 (새로운 Refresh Token 포함)
                TokenResponseDTO tokenResponse = new TokenResponseDTO(newAccessToken, newRefreshToken, expiresIn);
                
                return ResponseEntity.ok(ApiResponseDTO.success("토큰 로테이션 성공", tokenResponse));
                
            } catch (org.springframework.data.crossstore.ChangeSetPersister.NotFoundException e) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(ApiResponseDTO.error("사용자 정보를 찾을 수 없습니다"));
            }
            
        } catch (RefreshTokenNotFoundException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponseDTO.error(e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponseDTO.error("토큰 로테이션 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }
    
    /**
     * 로그아웃 (Refresh Token만 삭제, 회원 정보는 보존)
     * 사용자의 모든 디바이스에서 로그아웃 처리하되, 회원 정보는 절대 삭제하지 않음
     */
    @PostMapping("/logout")
    public ResponseEntity<ApiResponseDTO<Object>> logout(Authentication authentication) {
        try {
            if (authentication != null && authentication.isAuthenticated()) {
                // 현재 인증된 사용자의 정보 추출 (회원 정보는 조회만 함)
                AuthDetails authDetails = (AuthDetails) authentication.getPrincipal();
                String memberCode = authDetails.getMemberCode();
                
                // ⚠️ 중요: 회원 정보는 절대 삭제하지 않고, 오직 토큰만 삭제
                // 회원 정보 보존을 위한 로깅

                // 🔑 토큰만 완전히 삭제 (회원 정보는 건드리지 않음)
                refreshTokenService.deleteAllUserTokens(memberCode);
                
                // 로그아웃 완료 로깅

                return ResponseEntity.ok(ApiResponseDTO.success(
                    "로그아웃되었습니다. 모든 디바이스에서 로그아웃 처리되었습니다. 회원 정보는 안전하게 보존됩니다.", 
                    null
                ));
            } else {
                return ResponseEntity.ok(ApiResponseDTO.success(
                    "로그아웃되었습니다. 클라이언트에서 토큰을 삭제해주세요.", 
                    null
                ));
            }
        } catch (Exception e) {
            // 로그아웃 실패 시에도 클라이언트에서 토큰 삭제하도록 안내
         return ResponseEntity.ok(ApiResponseDTO.success(
                "로그아웃되었습니다. 클라이언트에서 토큰을 삭제해주세요. 회원 정보는 안전하게 보존됩니다.", 
                null
            ));
        }
    }
    
    /**
     * 특정 Refresh Token만 폐기 (개별 디바이스 로그아웃)
     */
    @PostMapping("/logout-device")
    public ResponseEntity<ApiResponseDTO<Object>> logoutDevice(@RequestBody RefreshTokenRequestDTO request) {
        try {
            String refreshToken = request.getRefreshToken();
            
            if (refreshToken == null || refreshToken.trim().isEmpty()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(ApiResponseDTO.error("Refresh Token이 필요합니다."));
            }
            
            // 특정 Refresh Token만 폐기
            refreshTokenService.revokeRefreshToken(refreshToken);
            
            return ResponseEntity.ok(ApiResponseDTO.success(
                "해당 디바이스에서 로그아웃되었습니다.", 
                null
            ));
            
        } catch (RefreshTokenNotFoundException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(ApiResponseDTO.error(e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponseDTO.error("로그아웃 처리 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }
    
    /**
     * 이메일 발송 API
     * 회원가입 인증코드 또는 비밀번호 재설정 코드 발송
     * Rate Limit: 1분에 3회 (스팸 방지)
     */
    @RateLimit(requests = 3, window = "1m", keyType = RateLimitKeyType.IP,
               message = "이메일 발송 요청이 너무 많습니다. 1분 후 다시 시도해주세요.")
    @PostMapping("/email/send")
    public ResponseEntity<ApiResponseDTO<Object>> sendEmail(@RequestBody EmailSendRequestDTO request) {
        try {
            // 입력값 검증
            if (request.getEmail() == null || request.getEmail().trim().isEmpty()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(ApiResponseDTO.error("이메일 주소가 필요합니다."));
            }
            
            if (request.getType() == null || request.getType().trim().isEmpty()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(ApiResponseDTO.error("이메일 타입이 필요합니다. (verification 또는 password-reset)"));
            }
            
            // 이메일 형식 검증
            if (!isValidEmail(request.getEmail())) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(ApiResponseDTO.error("올바른 이메일 형식이 아닙니다."));
            }
            
            String email = request.getEmail().trim();
            String type = request.getType().trim().toLowerCase();
            
            switch (type) {
                case "verification":
                    // 🆕 회원가입 인증 코드 발송 전 이메일 중복 체크
                    try {
                        memberService.findByEmail(email);
                        // 이메일이 이미 존재하면 에러 반환
                        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                                .body(ApiResponseDTO.error("이미 사용 중인 이메일입니다. 다른 이메일을 사용해주세요."));
                    } catch (org.springframework.data.crossstore.ChangeSetPersister.NotFoundException e) {
                        // 중복되지 않음 - 정상적으로 진행
                    }
                    
                    String verificationCode = emailService.generateVerificationCode();
                    emailService.sendVerificationEmail(email, verificationCode);
                    
                    // 인증 코드를 메모리에 저장 (5분 유효)
                    verificationCodeService.saveVerificationCode(email, verificationCode, "verification");
                    
                    return ResponseEntity.ok(ApiResponseDTO.success(
                            "인증 코드가 이메일로 발송되었습니다. 5분 내에 입력해주세요.", 
                            null));
                    
                case "password-reset":
                    // 비밀번호 재설정 코드 발송
                    try {
                        // 이메일이 존재하는지 확인
                        memberService.findByEmail(email);
                        
                        String resetCode = emailService.generateVerificationCode();
                        emailService.sendPasswordResetEmail(email, resetCode);
                        
                        // 재설정 코드를 메모리에 저장 (10분 유효)
                        verificationCodeService.saveVerificationCode(email, resetCode, "password-reset");
                        
                        return ResponseEntity.ok(ApiResponseDTO.success(
                                "비밀번호 재설정 코드가 이메일로 발송되었습니다. 10분 내에 입력해주세요.", 
                                null));
                        
                    } catch (org.springframework.data.crossstore.ChangeSetPersister.NotFoundException e) {
                        // 보안상 이유로 이메일이 존재하지 않아도 성공 메시지 반환
                        return ResponseEntity.ok(ApiResponseDTO.success(
                                "해당 이메일로 비밀번호 재설정 코드가 발송되었습니다.", 
                                null));
                    }
                    
                default:
                    return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                            .body(ApiResponseDTO.error("지원하지 않는 이메일 타입입니다. (verification 또는 password-reset만 지원)"));
            }
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponseDTO.error("이메일 발송 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }
    
    /**
     * 이메일 인증 코드 검증 API
     * 회원가입 시 이메일 인증 또는 비밀번호 재설정 시 사용
     */
    @PostMapping("/email/verify")
    public ResponseEntity<ApiResponseDTO<Object>> verifyEmailCode(@RequestBody EmailVerifyRequestDTO request) {
        try {
            // 입력값 검증
            if (request.getEmail() == null || request.getEmail().trim().isEmpty()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(ApiResponseDTO.error("이메일 주소가 필요합니다."));
            }
            
            if (request.getCode() == null || request.getCode().trim().isEmpty()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(ApiResponseDTO.error("인증 코드가 필요합니다."));
            }
            
            if (request.getType() == null || request.getType().trim().isEmpty()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(ApiResponseDTO.error("인증 타입이 필요합니다."));
            }
            
            // 이메일 형식 검증
            if (!isValidEmail(request.getEmail())) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(ApiResponseDTO.error("올바른 이메일 형식이 아닙니다."));
            }
            
            // 인증 코드 검증
            boolean isValid = verificationCodeService.verifyCode(
                request.getEmail().trim(), 
                request.getCode().trim(), 
                request.getType().trim().toLowerCase()
            );
            
            if (isValid) {
                // 검증 성공 시 해당 코드 삭제 (재사용 방지)
                verificationCodeService.removeVerificationCode(request.getEmail().trim());
                
                return ResponseEntity.ok(ApiResponseDTO.success(
                    "인증이 완료되었습니다.", 
                    null
                ));
            } else {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(ApiResponseDTO.error("인증 코드가 올바르지 않거나 만료되었습니다."));
            }
            
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponseDTO.error("인증 코드 검증 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }
    
    /**
     * 이메일 형식 검증 헬퍼 메서드
     */
    private boolean isValidEmail(String email) {
        String emailRegex = "^[a-zA-Z0-9_+&*-]+(?:\\.[a-zA-Z0-9_+&*-]+)*@(?:[a-zA-Z0-9-]+\\.)+[a-zA-Z]{2,7}$";
        return email.matches(emailRegex);
    }
}
