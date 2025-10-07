package com.ohgiraffers.tomatolab_imean.gateway.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * Python 서비스와 통신하기 위한 WebClient 설정 클래스
 * 
 * 이 클래스는 Spring의 Configuration 어노테이션을 사용하여
 * Python AI 서비스와의 HTTP 통신을 위한 WebClient Bean을 구성합니다.
 * 
 * @author TomatoLab
 * @version 1.0
 */
@Configuration
public class PythonServiceConfig {
    
    /**
     * Python 서비스의 URL 주소
     * application.properties에서 python.service.url 설정값을 읽어오며,
     * 설정되지 않은 경우 기본값으로 http://localhost:5000을 사용합니다.
     */
    @Value("${python.service.url:http://localhost:5000}")
    private String pythonServiceUrl;
    
    /**
     * Python 서비스와의 HTTP 통신을 위한 WebClient Bean을 생성합니다.
     * 
     * WebClient는 Spring WebFlux에서 제공하는 비동기 HTTP 클라이언트로,
     * 기존의 RestTemplate보다 성능이 우수하고 비동기 처리를 지원합니다.
     * 
     * @return WebClient Python 서비스 전용 WebClient 인스턴스
     */
    @Bean
    public WebClient pythonServiceWebClient() {
        return WebClient.builder()
                .baseUrl(pythonServiceUrl)  // Python AI 서버의 기본 URL 설정
                .defaultHeader("Content-Type", "application/json")  // 기본 요청 헤더 - JSON 형식으로 데이터 전송
                .defaultHeader("Accept", "application/json")        // 기본 응답 헤더 - JSON 형식으로 응답 수신
                .codecs(configurer -> configurer
                    .defaultCodecs()
                    .maxInMemorySize(1024 * 1024 * 10)) // 메모리 내 최대 버퍼 크기를 10MB로 설정 (대용량 AI 응답 처리)
                .build();
    }
}
