package com.ohgiraffers.tomatolab_imean.gateway.controller;

import com.ohgiraffers.tomatolab_imean.gateway.model.dto.AiRequest;
import com.ohgiraffers.tomatolab_imean.gateway.model.dto.GatewayResponse;
import com.ohgiraffers.tomatolab_imean.gateway.service.PermissionService;
import com.ohgiraffers.tomatolab_imean.gateway.service.PythonServiceClient;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.Map;

/**
 * AI 기능 Gateway Controller
 * 
 * 이 컨트롤러는 프론트엔드에서 오는 AI 관련 요청을 받아서
 * 사용자 권한을 확인한 후 Python AI 서비스로 전달하는 역할을 합니다.
 * 
 * 주요 기능:
 * - AI 채팅 (대화형 AI 상호작용)
 * - AI 대화 기록 관리
 * - AI 모델 정보 조회 (관리자용)
 * - AI 서비스 상태 확인 (관리자용)
 * 
 * 모든 요청은 인증된 사용자만 접근 가능하며,
 * 추가적으로 AI 접근 권한 검증을 수행합니다.
 * 
 * @author TomatoLab
 * @version 1.0
 */
@RestController
@RequestMapping("/api/ai")
@PreAuthorize("isAuthenticated()") // 클래스 레벨 보안: 인증된 사용자만 모든 엔드포인트에 접근 가능
public class AiGatewayController {
    
    /** 로깅을 위한 Logger 인스턴스 */
    private static final Logger logger = LoggerFactory.getLogger(AiGatewayController.class);
    
    /** Python AI 서비스와의 통신을 담당하는 클라이언트 */
    private final PythonServiceClient pythonServiceClient;
    
    /** 사용자 권한 검증을 담당하는 서비스 */
    private final PermissionService permissionService;
    
    /**
     * 생성자 주입을 통한 의존성 주입
     * 
     * @param pythonServiceClient Python AI 서비스 클라이언트
     * @param permissionService 권한 검증 서비스
     */
    @Autowired
    public AiGatewayController(PythonServiceClient pythonServiceClient, 
                             PermissionService permissionService) {
        this.pythonServiceClient = pythonServiceClient;
        this.permissionService = permissionService;
    }
    
    /**
     * AI 채팅 기능
     * 
     * 사용자의 질문(프롬프트)을 받아서 AI가 응답을 생성합니다.
     * 대화의 연속성을 위해 conversationId를 통해 이전 대화 컨텍스트를 유지합니다.
     * 
     * HTTP Method: POST
     * Endpoint: /api/ai/chat
     * 
     * @param request AI 요청 데이터 (프롬프트, 대화 ID 포함)
     * @param authentication 현재 인증된 사용자 정보
     * @return Mono<ResponseEntity<GatewayResponse<Object>>> AI 응답 결과
     */
    @PostMapping("/chat")
    @SuppressWarnings("rawtypes")
    public Mono<ResponseEntity<GatewayResponse<Object>>> aiChat(
            @Valid @RequestBody AiRequest request,
            Authentication authentication) {
        
        // 요청 로깅: 사용자명과 프롬프트 길이 기록
        logger.info("AI 채팅 요청: {} ({}자)", authentication.getName(), request.getPrompt().length());
        
        // 1단계: AI 기능 접근 권한 확인
        if (!permissionService.canAccessAi(authentication)) {
            logger.warn("AI 접근 권한 없음: {}", authentication.getName());
            return Mono.just(ResponseEntity.status(403)
                .body(GatewayResponse.<Object>error("AI 기능 접근 권한이 없습니다.")));
        }
        
        // 2단계: 사용자 ID 추출
        String userId = permissionService.extractUserId(authentication);
        
        // 3단계: Python AI 서비스 호출 및 응답 처리
        return pythonServiceClient.aiChat(userId, request.getPrompt(), request.getConversationId())
                .map(result -> {
                    // Python 서비스에서 오류가 발생한 경우
                    if (result.containsKey("error")) {
                        logger.error("Python 서비스 오류 - AI 채팅: {}", result.get("error"));
                        return ResponseEntity.status(500)
                            .body(GatewayResponse.<Object>error("AI 응답 생성 중 오류가 발생했습니다."));
                    }
                    
                    // 성공적인 응답 처리
                    logger.info("AI 채팅 응답 성공: {}", userId);
                    return ResponseEntity.ok(GatewayResponse.<Object>success("AI 응답 생성 완료", result));
                })
                .onErrorResume(throwable -> {
                    // 네트워크 오류 등 예외 상황 처리
                    logger.error("AI 채팅 서비스 연결 오류: {}", throwable.getMessage());
                    return Mono.just(ResponseEntity.status(500)
                        .body(GatewayResponse.<Object>error("AI 서비스 연결 오류가 발생했습니다.")));
                });
    }
    
    /**
     * AI 대화 기록 조회
     * 
     * 특정 대화 ID의 전체 대화 내역을 조회합니다.
     * 
     * HTTP Method: GET
     * Endpoint: /api/ai/conversations/{conversationId}
     * 
     * @param conversationId 조회할 대화의 고유 ID
     * @param authentication 현재 인증된 사용자 정보
     * @return Mono<ResponseEntity> 대화 기록 조회 결과
     */
    @GetMapping("/conversations/{conversationId}")
    @SuppressWarnings("rawtypes")
    public Mono<ResponseEntity> getConversation(
            @PathVariable String conversationId,
            Authentication authentication) {
        
        logger.info("AI 대화 기록 조회 요청: {} -> {}", authentication.getName(), conversationId);
        
        // AI 접근 권한 확인
        if (!permissionService.canAccessAi(authentication)) {
            logger.warn("AI 접근 권한 없음: {}", authentication.getName());
            return Mono.just(ResponseEntity.status(403)
                .body(GatewayResponse.<Object>error("AI 기능 접근 권한이 없습니다.")));
        }
        
        // TODO: Python 서비스에 대화 기록 조회 API 구현 후 연동
        // 현재는 임시 응답 - 향후 pythonServiceClient.getConversation(conversationId) 구현 예정
        return Mono.just(ResponseEntity.ok(
            GatewayResponse.<Object>success("대화 기록 조회 기능은 준비 중입니다.", 
                Map.of("conversationId", conversationId, "status", "준비중"))
        ));
    }
    
    /**
     * AI 대화 목록 조회
     * 
     * 현재 사용자의 모든 AI 대화 목록을 조회합니다.
     * 
     * HTTP Method: GET
     * Endpoint: /api/ai/conversations
     * 
     * @param authentication 현재 인증된 사용자 정보
     * @return Mono<ResponseEntity> 대화 목록 조회 결과
     */
    @GetMapping("/conversations")
    @SuppressWarnings("rawtypes")
    public Mono<ResponseEntity> getConversations(Authentication authentication) {
        
        logger.info("AI 대화 목록 조회 요청: {}", authentication.getName());
        
        // AI 접근 권한 확인
        if (!permissionService.canAccessAi(authentication)) {
            logger.warn("AI 접근 권한 없음: {}", authentication.getName());
            return Mono.just(ResponseEntity.status(403)
                .body(GatewayResponse.<Object>error("AI 기능 접근 권한이 없습니다.")));
        }
        
        // TODO: Python 서비스에 대화 목록 조회 API 구현 후 연동
        // 현재는 임시 응답 - 향후 pythonServiceClient.getConversations(userId) 구현 예정
        String userId = permissionService.extractUserId(authentication);
        return Mono.just(ResponseEntity.ok(
            GatewayResponse.<Object>success("대화 목록 조회 기능은 준비 중입니다.", 
                Map.of("userId", userId, "conversations", "준비중"))
        ));
    }
    
    /**
     * AI 모델 목록 조회 (관리자 전용)
     * 
     * 현재 시스템에서 사용 가능한 AI 모델들의 목록과 상태를 조회합니다.
     * 일반 관리자 또는 최고 관리자 권한이 필요합니다.
     * 
     * HTTP Method: GET
     * Endpoint: /api/ai/models
     * 
     * @param authentication 현재 인증된 사용자 정보 (관리자여야 함)
     * @return Mono<ResponseEntity> 사용 가능한 AI 모델 목록
     */
    @GetMapping("/models")
    @PreAuthorize("hasAnyAuthority('ROLE_GENERAL_ADMIN', 'ROLE_SUPER_ADMIN')")
    @SuppressWarnings("rawtypes")
    public Mono<ResponseEntity> getAvailableModels(Authentication authentication) {
        
        logger.info("AI 모델 목록 조회 요청: {}", authentication.getName());
        
        // TODO: Python 서비스에 모델 목록 조회 API 구현 후 연동
        // 현재는 임시 응답 - 향후 pythonServiceClient.getAvailableModels() 구현 예정
        return Mono.just(ResponseEntity.ok(
            GatewayResponse.<Object>success("사용 가능한 AI 모델 목록", 
                Map.of(
                    "models", java.util.List.of(
                        Map.of("id", "gpt-3.5-turbo", "name", "GPT-3.5 Turbo", "status", "available"),
                        Map.of("id", "gpt-4", "name", "GPT-4", "status", "available")
                    )
                ))
        ));
    }
    
    /**
     * AI 서비스 상태 확인 (관리자 전용)
     * 
     * Python AI 서비스의 현재 상태와 연결 상태를 확인합니다.
     * 시스템 모니터링 및 장애 진단에 사용됩니다.
     * 
     * HTTP Method: GET
     * Endpoint: /api/ai/health
     * 
     * @param authentication 현재 인증된 사용자 정보 (관리자여야 함)
     * @return Mono<ResponseEntity<GatewayResponse<Object>>> AI 서비스 상태 정보
     */
    @GetMapping("/health")
    @PreAuthorize("hasAnyAuthority('ROLE_GENERAL_ADMIN', 'ROLE_SUPER_ADMIN')")
    @SuppressWarnings("rawtypes")
    public Mono<ResponseEntity<GatewayResponse<Object>>> healthCheck(Authentication authentication) {
        
        logger.info("AI 서비스 헬스체크 요청: {}", authentication.getName());
        
        // Python AI 서비스의 헬스체크 엔드포인트 호출
        return pythonServiceClient.healthCheck()
                .map(result -> {
                    logger.info("AI 서비스 헬스체크 완료: {}", result);
                    return ResponseEntity.ok(GatewayResponse.<Object>success("AI 서비스 헬스체크 완료", result));
                })
                .onErrorResume(throwable -> {
                    // 헬스체크 실패 시 서비스 장애 상태로 판단
                    logger.error("AI 서비스 헬스체크 연결 오류: {}", throwable.getMessage());
                    return Mono.just(ResponseEntity.status(500)
                        .body(GatewayResponse.<Object>error("AI 서비스 헬스체크 실패")));
                });
    }
}
