package com.ohgiraffers.tomatolab_imean.auth.config.handler;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ohgiraffers.tomatolab_imean.common.dto.response.ApiResponseDTO;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.stereotype.Component;

import java.io.IOException;

/**
 * JWT 인증 실패 시 처리하는 핸들러
 * 인증이 필요한 리소스에 접근할 때 JWT 토큰이 없거나 유효하지 않은 경우 실행
 */
@Component
public class JwtAuthenticationEntryPoint implements AuthenticationEntryPoint {
    
    private static final Logger logger = LoggerFactory.getLogger(JwtAuthenticationEntryPoint.class);
    
    private final ObjectMapper objectMapper;
    
    // JSON 변환을 위한 ObjectMapper 주입
    public JwtAuthenticationEntryPoint() {
        this.objectMapper = new ObjectMapper();
    }
    
    /**
     * 인증 실패 시 실행되는 메서드
     * 401 Unauthorized 응답을 JSON 형태로 반환
     * 
     * @param request HTTP 요청
     * @param response HTTP 응답
     * @param authException 인증 예외
     */
    @Override
    public void commence(
            HttpServletRequest request, 
            HttpServletResponse response,
            AuthenticationException authException) throws IOException, ServletException {
        
        logger.warn("인증되지 않은 요청: {} {}", request.getMethod(), request.getRequestURI());
        logger.warn("인증 실패 원인: {}", authException.getMessage());
        
        // 응답 설정
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED); // 401 상태 코드
        response.setContentType(MediaType.APPLICATION_JSON_VALUE); // JSON 타입
        response.setCharacterEncoding("UTF-8"); // UTF-8 인코딩
        
        // 에러 응답 DTO 생성
        ApiResponseDTO<Object> errorResponse = ApiResponseDTO.error(
            "인증이 필요합니다. 로그인 후 다시 시도해주세요."
        );
        
        // JSON으로 변환하여 응답 본문에 작성
        String jsonResponse = objectMapper.writeValueAsString(errorResponse);
        response.getWriter().write(jsonResponse);
        
        logger.debug("인증 실패 응답 전송: {}", jsonResponse);
    }
}