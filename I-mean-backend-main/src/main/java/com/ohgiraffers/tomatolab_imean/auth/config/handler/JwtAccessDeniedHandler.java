package com.ohgiraffers.tomatolab_imean.auth.config.handler;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ohgiraffers.tomatolab_imean.common.dto.response.ApiResponseDTO;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.stereotype.Component;

import java.io.IOException;

/**
 * JWT 인증은 성공했지만 권한이 부족한 경우 처리하는 핸들러
 * 예: USER 권한인데 ADMIN 전용 API에 접근할 때
 */
@Component
public class JwtAccessDeniedHandler implements AccessDeniedHandler {
    
    private static final Logger logger = LoggerFactory.getLogger(JwtAccessDeniedHandler.class);
    
    private final ObjectMapper objectMapper;
    
    // JSON 변환을 위한 ObjectMapper 주입
    public JwtAccessDeniedHandler() {
        this.objectMapper = new ObjectMapper();
    }
    
    /**
     * 권한 부족 시 실행되는 메서드
     * 403 Forbidden 응답을 JSON 형태로 반환
     * 
     * @param request HTTP 요청
     * @param response HTTP 응답
     * @param accessDeniedException 접근 거부 예외
     */
    @Override
    public void handle(
            HttpServletRequest request, 
            HttpServletResponse response,
            AccessDeniedException accessDeniedException) throws IOException, ServletException {
        
        // 현재 인증된 사용자 정보 가져오기
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String username = (authentication != null) ? authentication.getName() : "익명";
        
        logger.warn("권한 부족으로 접근 거부: {} {} - 사용자: {}", 
                request.getMethod(), request.getRequestURI(), username);
        logger.warn("접근 거부 원인: {}", accessDeniedException.getMessage());
        
        // 응답 설정
        response.setStatus(HttpServletResponse.SC_FORBIDDEN); // 403 상태 코드
        response.setContentType(MediaType.APPLICATION_JSON_VALUE); // JSON 타입
        response.setCharacterEncoding("UTF-8"); // UTF-8 인코딩
        
        // 에러 응답 DTO 생성
        ApiResponseDTO<Object> errorResponse = ApiResponseDTO.error(
            "접근 권한이 없습니다. 필요한 권한을 확인해주세요."
        );
        
        // JSON으로 변환하여 응답 본문에 작성
        String jsonResponse = objectMapper.writeValueAsString(errorResponse);
        response.getWriter().write(jsonResponse);
        
        logger.debug("권한 거부 응답 전송: {}", jsonResponse);
    }
}