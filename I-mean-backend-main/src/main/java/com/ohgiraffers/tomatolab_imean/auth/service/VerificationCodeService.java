package com.ohgiraffers.tomatolab_imean.auth.service;

import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 이메일 인증 코드 관리 서비스
 * 메모리 기반으로 인증 코드를 임시 저장하고 검증
 * TODO: 추후 Redis로 변경하여 분산 환경 지원
 */
@Service
public class VerificationCodeService {
    
    // 인증 코드 저장용 맵 (이메일 -> 인증 정보)
    private final Map<String, VerificationInfo> verificationCodes = new ConcurrentHashMap<>();
    
    // 인증 코드 유효시간 (분)
    private static final int VERIFICATION_CODE_EXPIRY_MINUTES = 5;
    private static final int PASSWORD_RESET_CODE_EXPIRY_MINUTES = 10;
    
    /**
     * 이메일 인증 코드 저장
     */
    public void saveVerificationCode(String email, String code, String type) {
        LocalDateTime expiredAt = LocalDateTime.now().plusMinutes(
            "password-reset".equals(type) ? PASSWORD_RESET_CODE_EXPIRY_MINUTES : VERIFICATION_CODE_EXPIRY_MINUTES
        );
        
        VerificationInfo info = new VerificationInfo(code, type, expiredAt, false);
        verificationCodes.put(email.toLowerCase(), info);
        
        // 메모리 누수 방지를 위한 정리 작업 실행
        cleanupExpiredCodes();
    }
    
    /**
     * 인증 코드 검증
     */
    public boolean verifyCode(String email, String code, String type) {
        VerificationInfo info = verificationCodes.get(email.toLowerCase());
        
        if (info == null) {
            return false; // 코드가 존재하지 않음
        }
        
        if (info.isUsed()) {
            return false; // 이미 사용된 코드
        }
        
        if (LocalDateTime.now().isAfter(info.getExpiredAt())) {
            verificationCodes.remove(email.toLowerCase());
            return false; // 만료된 코드
        }
        
        if (!info.getType().equals(type)) {
            return false; // 타입이 맞지 않음
        }
        
        if (!info.getCode().equals(code)) {
            return false; // 코드가 일치하지 않음
        }
        
        // 검증 성공 - 코드를 사용됨으로 표시
        info.setUsed(true);
        return true;
    }
    
    /**
     * 특정 이메일의 인증 코드 삭제
     */
    public void removeVerificationCode(String email) {
        verificationCodes.remove(email.toLowerCase());
    }
    
    /**
     * 만료된 인증 코드 정리
     */
    private void cleanupExpiredCodes() {
        LocalDateTime now = LocalDateTime.now();
        verificationCodes.entrySet().removeIf(entry -> 
            now.isAfter(entry.getValue().getExpiredAt()) || entry.getValue().isUsed()
        );
    }
    
    /**
     * 인증 코드 정보를 담는 내부 클래스
     */
    private static class VerificationInfo {
        private final String code;
        private final String type;
        private final LocalDateTime expiredAt;
        private boolean used;
        
        public VerificationInfo(String code, String type, LocalDateTime expiredAt, boolean used) {
            this.code = code;
            this.type = type;
            this.expiredAt = expiredAt;
            this.used = used;
        }
        
        public String getCode() {
            return code;
        }
        
        public String getType() {
            return type;
        }
        
        public LocalDateTime getExpiredAt() {
            return expiredAt;
        }
        
        public boolean isUsed() {
            return used;
        }
        
        public void setUsed(boolean used) {
            this.used = used;
        }
    }
}
