package com.ohgiraffers.tomatolab_imean.common.config;

import com.ohgiraffers.tomatolab_imean.common.ratelimit.RateLimitInterceptor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Spring MVC 설정
 * 인터셉터, CORS, 리소스 핸들러 등을 구성합니다.
 */
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {
    
    private final RateLimitInterceptor rateLimitInterceptor;
    
    public WebMvcConfig(RateLimitInterceptor rateLimitInterceptor) {
        this.rateLimitInterceptor = rateLimitInterceptor;
    }
    
    /**
     * 인터셉터 등록
     * Rate Limiting 인터셉터를 모든 API 경로에 적용
     */
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(rateLimitInterceptor)
                .addPathPatterns("/api/**")  // API 경로에만 적용
                .excludePathPatterns(
                    "/api/public/**",        // 공개 API 제외
                    "/api/health/**",        // 헬스체크 제외
                    "/api/actuator/**"       // Actuator 제외
                );
    }
}
