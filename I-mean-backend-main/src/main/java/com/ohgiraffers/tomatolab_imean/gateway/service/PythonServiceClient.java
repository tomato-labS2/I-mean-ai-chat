package com.ohgiraffers.tomatolab_imean.gateway.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.Map;

/**
 * Python 서비스와 통신하는 클라이언트 서비스
 * 
 * 이 클래스는 Java Spring Boot 애플리케이션과 Python 기반 AI/채팅 서비스 간의
 * HTTP 통신을 담당하는 클라이언트입니다. WebClient를 사용하여 비동기적으로
 * Python 서비스의 REST API를 호출합니다.
 * 
 * 주요 기능:
 * - AI 채팅 요청 처리
 * - 채팅방 관리 (입장, 목록 조회)
 * - 채팅 메시지 전송
 * - Python 서비스 헬스체크
 * 
 * 통신 특징:
 * - 비동기 처리 (Reactive Programming)
 * - 타임아웃 설정으로 무한 대기 방지
 * - 에러 처리 및 폴백 메커니즘
 * - 구조화된 에러 응답 생성
 * 
 * @author TomatoLab
 * @version 1.0
 */
@Service
public class PythonServiceClient {
    
    /** 로깅을 위한 Logger 인스턴스 */
    private static final Logger logger = LoggerFactory.getLogger(PythonServiceClient.class);
    
    /** Python 서비스와의 HTTP 통신을 위한 WebClient */
    private final WebClient pythonServiceWebClient;
    
    /**
     * 생성자 주입을 통한 의존성 주입
     * 
     * @param pythonServiceWebClient Python 서비스 전용으로 설정된 WebClient
     */
    @Autowired
    public PythonServiceClient(WebClient pythonServiceWebClient) {
        this.pythonServiceWebClient = pythonServiceWebClient;
    }
    
    /**
     * 채팅 메시지 전송을 Python 서버에 요청
     * 
     * 사용자가 특정 채팅방에 보낸 메시지를 Python 채팅 서비스로 전달합니다.
     * Python 서비스에서는 메시지 저장, 전파, 알림 등의 처리를 담당합니다.
     * 
     * API Endpoint: POST /internal/chat/send
     * Timeout: 10초
     * 
     * @param userId 메시지를 보내는 사용자의 고유 식별자
     * @param chatroomId 메시지를 보낼 채팅방의 고유 식별자
     * @param message 전송할 메시지 내용
     * @return Mono<Map> Python 서비스의 응답 데이터
     */
    public Mono<Map> sendChatMessage(String userId, String chatroomId, String message) {
        // 요청 바디 구성
        Map<String, Object> requestBody = Map.of(
            "user_id", userId,
            "chatroom_id", chatroomId,
            "message", message
        );
        
        return pythonServiceWebClient
                .post()
                .uri("/internal/chat/send")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(Map.class)
                .timeout(Duration.ofSeconds(10)) // 10초 타임아웃
                .doOnError(error -> logger.error("Python 서비스 통신 오류 - 채팅 전송: {}", error.getMessage()))
                .onErrorResume(throwable -> {
                    // 에러 발생 시 표준화된 에러 응답 반환
                    logger.error("채팅 전송 실패: {}", throwable.getMessage());
                    return Mono.just(createErrorResponse("채팅 메시지 전송 실패"));
                });
    }
    
    /**
     * 채팅방 입장을 Python 서버에 요청
     * 
     * 사용자를 특정 채팅방에 입장시키기 위해 Python 채팅 서비스로 요청을 보냅니다.
     * Python 서비스에서는 사용자의 채팅방 멤버십 등록, 초기 데이터 로드 등을 처리합니다.
     * 
     * API Endpoint: POST /internal/chat/join
     * Timeout: 5초
     * 
     * @param userId 채팅방에 입장할 사용자의 고유 식별자
     * @param chatroomId 입장할 채팅방의 고유 식별자
     * @return Mono<Map> Python 서비스의 응답 데이터
     */
    public Mono<Map> joinChatroom(String userId, String chatroomId) {
        // 요청 바디 구성
        Map<String, Object> requestBody = Map.of(
            "user_id", userId,
            "chatroom_id", chatroomId
        );
        
        return pythonServiceWebClient
                .post()
                .uri("/internal/chat/join")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(Map.class)
                .timeout(Duration.ofSeconds(5)) // 5초 타임아웃
                .doOnError(error -> logger.error("Python 서비스 통신 오류 - 채팅방 입장: {}", error.getMessage()))
                .onErrorResume(throwable -> {
                    // 에러 발생 시 표준화된 에러 응답 반환
                    logger.error("채팅방 입장 실패: {}", throwable.getMessage());
                    return Mono.just(createErrorResponse("채팅방 입장 실패"));
                });
    }
    
    /**
     * AI 채팅을 Python 서버에 요청
     * 
     * 사용자의 프롬프트를 Python AI 서비스로 전달하여 AI 응답을 생성합니다.
     * 대화의 연속성을 위해 conversation_id를 포함하여 이전 대화 컨텍스트를 유지합니다.
     * 
     * API Endpoint: POST /internal/ai/chat
     * Timeout: 30초 (AI 응답 생성 시간 고려)
     * 
     * @param userId AI 채팅을 요청하는 사용자의 고유 식별자
     * @param prompt 사용자가 AI에게 보내는 질문이나 명령
     * @param conversationId 대화 연속성을 위한 고유 식별자 (null 가능)
     * @return Mono<Map> Python AI 서비스의 응답 데이터
     */
    public Mono<Map> aiChat(String userId, String prompt, String conversationId) {
        // 요청 바디 구성
        Map<String, Object> requestBody = Map.of(
            "user_id", userId,
            "prompt", prompt,
            "conversation_id", conversationId != null ? conversationId : "" // null인 경우 빈 문자열로 처리
        );
        
        return pythonServiceWebClient
                .post()
                .uri("/internal/ai/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(Map.class)
                .timeout(Duration.ofSeconds(30)) // AI 응답 생성은 시간이 더 걸릴 수 있어 30초로 설정
                .doOnError(error -> logger.error("Python 서비스 통신 오류 - AI 채팅: {}", error.getMessage()))
                .onErrorResume(throwable -> {
                    // 에러 발생 시 표준화된 에러 응답 반환
                    logger.error("AI 채팅 실패: {}", throwable.getMessage());
                    return Mono.just(createErrorResponse("AI 채팅 응답 실패"));
                });
    }
    
    /**
     * Python 서비스 헬스체크
     * 
     * Python 서비스의 상태와 연결 가능성을 확인합니다.
     * 시스템 모니터링, 로드밸런서, 서킷브레이커 등에서 사용할 수 있습니다.
     * 
     * API Endpoint: GET /health
     * Timeout: 3초
     * 
     * @return Mono<Map> Python 서비스의 헬스체크 응답
     */
    public Mono<Map> healthCheck() {
        return pythonServiceWebClient
                .get()
                .uri("/health")
                .retrieve()
                .bodyToMono(Map.class)
                .timeout(Duration.ofSeconds(3)) // 헬스체크는 빠른 응답이 중요하므로 3초로 설정
                .doOnError(error -> logger.warn("Python 서비스 헬스체크 실패: {}", error.getMessage()))
                .onErrorResume(throwable -> {
                    // 헬스체크 실패 시 서비스 상태 정보 반환
                    logger.warn("헬스체크 연결 실패: {}", throwable.getMessage());
                    return Mono.just(Map.of("status", "error", "message", "Python 서비스 연결 실패"));
                });
    }
    
    /**
     * 채팅방 목록 조회를 Python 서버에 요청
     * 
     * 특정 사용자가 접근할 수 있는 모든 채팅방의 목록을 Python 채팅 서비스에서 조회합니다.
     * 사용자의 권한에 따라 필터링된 채팅방 목록이 반환됩니다.
     * 
     * API Endpoint: GET /internal/chat/rooms?user_id={userId}
     * Timeout: 5초
     * 
     * @param userId 채팅방 목록을 조회할 사용자의 고유 식별자
     * @return Mono<Map> Python 서비스의 채팅방 목록 응답
     */
    public Mono<Map> getChatrooms(String userId) {
        return pythonServiceWebClient
                .get()
                .uri("/internal/chat/rooms?user_id={userId}", userId) // URL 파라미터로 사용자 ID 전달
                .retrieve()
                .bodyToMono(Map.class)
                .timeout(Duration.ofSeconds(5)) // 5초 타임아웃
                .doOnError(error -> logger.error("Python 서비스 통신 오류 - 채팅방 목록: {}", error.getMessage()))
                .onErrorResume(throwable -> {
                    // 에러 발생 시 표준화된 에러 응답 반환
                    logger.error("채팅방 목록 조회 실패: {}", throwable.getMessage());
                    return Mono.just(createErrorResponse("채팅방 목록 조회 실패"));
                });
    }
    
    /**
     * 에러 응답 생성 헬퍼 메서드
     * 
     * Python 서비스 통신 실패 시 일관된 형태의 에러 응답을 생성합니다.
     * 클라이언트가 에러 상황을 쉽게 식별할 수 있도록 표준화된 형식을 제공합니다.
     * 
     * 에러 응답 구조:
     * - success: false (실패 표시)
     * - error: 에러 메시지
     * - timestamp: 에러 발생 시간 (Unix timestamp)
     * 
     * @param message 에러 상황을 설명하는 메시지
     * @return Map<String, Object> 표준화된 에러 응답 객체
     */
    private Map<String, Object> createErrorResponse(String message) {
        return Map.of(
            "success", false,
            "error", message,
            "timestamp", System.currentTimeMillis()
        );
    }
}
