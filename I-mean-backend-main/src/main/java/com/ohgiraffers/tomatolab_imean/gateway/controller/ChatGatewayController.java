package com.ohgiraffers.tomatolab_imean.gateway.controller;

import com.ohgiraffers.tomatolab_imean.gateway.model.dto.ChatRequest;
import com.ohgiraffers.tomatolab_imean.gateway.model.dto.GatewayResponse;
import com.ohgiraffers.tomatolab_imean.gateway.model.dto.JoinChatroomRequest;
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
 * 채팅 기능 Gateway Controller
 * 
 * 이 컨트롤러는 커플 간의 채팅 기능을 담당합니다.
 * 프론트엔드에서 오는 채팅 관련 요청을 받아서
 * 사용자 권한을 확인한 후 Python 채팅 서비스로 전달하는 역할을 합니다.
 * 
 * 주요 기능:
 * - 채팅방 목록 조회
 * - 채팅방 입장
 * - 채팅 메시지 전송
 * - 채팅 서비스 상태 확인 (관리자용)
 * 
 * 접근 제한: 커플 관계가 성립된 사용자만 접근 가능 (COUPLE_COUPLED 권한 필요)
 * 
 * @author TomatoLab
 * @version 1.0
 */
@RestController
@RequestMapping("/api/chat")
@PreAuthorize("hasAuthority('COUPLE_COUPLED')") // 클래스 레벨 보안: 커플 관계가 성립된 사용자만 접근 가능
public class ChatGatewayController {
    
    /** 로깅을 위한 Logger 인스턴스 */
    private static final Logger logger = LoggerFactory.getLogger(ChatGatewayController.class);
    
    /** Python 채팅 서비스와의 통신을 담당하는 클라이언트 */
    private final PythonServiceClient pythonServiceClient;
    
    /** 사용자 권한 검증을 담당하는 서비스 */
    private final PermissionService permissionService;
    
    /**
     * 생성자 주입을 통한 의존성 주입
     * 
     * @param pythonServiceClient Python 채팅 서비스 클라이언트
     * @param permissionService 권한 검증 서비스
     */
    @Autowired
    public ChatGatewayController(PythonServiceClient pythonServiceClient, 
                               PermissionService permissionService) {
        this.pythonServiceClient = pythonServiceClient;
        this.permissionService = permissionService;
    }
    
    /**
     * 채팅방 목록 조회
     * 
     * 현재 사용자가 참여할 수 있는 모든 채팅방의 목록을 조회합니다.
     * 일반적으로 커플 간의 개인 채팅방과 그룹 채팅방이 포함됩니다.
     * 
     * HTTP Method: GET
     * Endpoint: /api/chat/rooms
     * 
     * @param authentication 현재 인증된 사용자 정보
     * @return Mono<ResponseEntity<GatewayResponse<Object>>> 채팅방 목록 조회 결과
     */
    @GetMapping("/rooms")
    @SuppressWarnings("rawtypes")
    public Mono<ResponseEntity<GatewayResponse<Object>>> getChatrooms(Authentication authentication) {
        logger.info("채팅방 목록 조회 요청: {}", authentication.getName());
        
        // 추가 권한 확인: 채팅 기능 접근 권한 검증
        if (!permissionService.canAccessChat(authentication)) {
            logger.warn("채팅방 목록 조회 권한 없음: {}", authentication.getName());
            return Mono.just(ResponseEntity.status(403)
                .body(GatewayResponse.<Object>error("채팅 기능 접근 권한이 없습니다.")));
        }
        
        // 사용자 ID 추출
        String userId = permissionService.extractUserId(authentication);
        
        // Python 채팅 서비스에서 채팅방 목록 조회
        return pythonServiceClient.getChatrooms(userId)
                .map(result -> {
                    // Python 서비스에서 오류가 발생한 경우
                    if (result.containsKey("error")) {
                        logger.error("Python 서비스 오류 - 채팅방 목록: {}", result.get("error"));
                        return ResponseEntity.status(500)
                            .body(GatewayResponse.<Object>error("채팅방 목록 조회 중 오류가 발생했습니다."));
                    }
                    
                    // 성공적인 응답 처리
                    logger.info("채팅방 목록 조회 성공: {}", userId);
                    return ResponseEntity.ok(GatewayResponse.<Object>success("채팅방 목록 조회 성공", result));
                })
                .onErrorResume(throwable -> {
                    // 네트워크 오류 등 예외 상황 처리
                    logger.error("채팅방 목록 서비스 연결 오류: {}", throwable.getMessage());
                    return Mono.just(ResponseEntity.status(500)
                        .body(GatewayResponse.<Object>error("서비스 연결 오류가 발생했습니다.")));
                });
    }
    
    /**
     * 채팅방 입장
     * 
     * 특정 채팅방에 사용자를 입장시킵니다.
     * 채팅방별 접근 권한을 확인하여 권한이 있는 사용자만 입장할 수 있습니다.
     * 
     * HTTP Method: POST
     * Endpoint: /api/chat/join
     * 
     * @param request 채팅방 입장 요청 데이터 (채팅방 ID 포함)
     * @param authentication 현재 인증된 사용자 정보
     * @return Mono<ResponseEntity<GatewayResponse<Object>>> 채팅방 입장 결과
     */
    @PostMapping("/join")
    @SuppressWarnings("rawtypes")
    public Mono<ResponseEntity<GatewayResponse<Object>>> joinChatroom(
            @Valid @RequestBody JoinChatroomRequest request,
            Authentication authentication) {
        
        logger.info("채팅방 입장 요청: {} -> {}", authentication.getName(), request.getChatroomId());
        
        // 채팅방별 세부 권한 확인
        if (!permissionService.canAccessChatroom(authentication, request.getChatroomId())) {
            logger.warn("채팅방 접근 권한 없음: {} -> {}", authentication.getName(), request.getChatroomId());
            return Mono.just(ResponseEntity.status(403)
                .body(GatewayResponse.<Object>error("해당 채팅방에 접근할 권한이 없습니다.")));
        }
        
        // 사용자 ID 추출
        String userId = permissionService.extractUserId(authentication);
        
        // Python 채팅 서비스에 채팅방 입장 요청
        return pythonServiceClient.joinChatroom(userId, request.getChatroomId())
                .map(result -> {
                    // Python 서비스에서 오류가 발생한 경우
                    if (result.containsKey("error")) {
                        logger.error("Python 서비스 오류 - 채팅방 입장: {}", result.get("error"));
                        return ResponseEntity.status(500)
                            .body(GatewayResponse.<Object>error("채팅방 입장 중 오류가 발생했습니다."));
                    }
                    
                    // 성공적인 응답 처리
                    logger.info("채팅방 입장 성공: {} -> {}", userId, request.getChatroomId());
                    return ResponseEntity.ok(GatewayResponse.<Object>success("채팅방 입장 성공", result));
                })
                .onErrorResume(throwable -> {
                    // 네트워크 오류 등 예외 상황 처리
                    logger.error("채팅방 입장 서비스 연결 오류: {}", throwable.getMessage());
                    return Mono.just(ResponseEntity.status(500)
                        .body(GatewayResponse.<Object>error("서비스 연결 오류가 발생했습니다.")));
                });
    }
    
    /**
     * 채팅 메시지 전송
     * 
     * 특정 채팅방에 메시지를 전송합니다.
     * 해당 채팅방에 대한 메시지 전송 권한을 확인한 후 처리합니다.
     * 
     * HTTP Method: POST
     * Endpoint: /api/chat/send
     * 
     * @param request 채팅 메시지 전송 요청 데이터 (채팅방 ID, 메시지 내용 포함)
     * @param authentication 현재 인증된 사용자 정보
     * @return Mono<ResponseEntity<GatewayResponse<Object>>> 메시지 전송 결과
     */
    @PostMapping("/send")
    @SuppressWarnings("rawtypes")
    public Mono<ResponseEntity<GatewayResponse<Object>>> sendMessage(
            @Valid @RequestBody ChatRequest request,
            Authentication authentication) {
        
        // 요청 로깅: 사용자명, 채팅방 ID, 메시지 길이 기록
        logger.info("채팅 메시지 전송 요청: {} -> {} ({}자)", 
            authentication.getName(), request.getChatroomId(), request.getMessage().length());
        
        // 채팅방별 메시지 전송 권한 확인
        if (!permissionService.canAccessChatroom(authentication, request.getChatroomId())) {
            logger.warn("채팅방 메시지 전송 권한 없음: {} -> {}", 
                authentication.getName(), request.getChatroomId());
            return Mono.just(ResponseEntity.status(403)
                .body(GatewayResponse.<Object>error("해당 채팅방에 메시지를 전송할 권한이 없습니다.")));
        }
        
        // 사용자 ID 추출
        String userId = permissionService.extractUserId(authentication);
        
        // Python 채팅 서비스에 메시지 전송 요청
        return pythonServiceClient.sendChatMessage(userId, request.getChatroomId(), request.getMessage())
                .map(result -> {
                    // Python 서비스에서 오류가 발생한 경우
                    if (result.containsKey("error")) {
                        logger.error("Python 서비스 오류 - 메시지 전송: {}", result.get("error"));
                        return ResponseEntity.status(500)
                            .body(GatewayResponse.<Object>error("메시지 전송 중 오류가 발생했습니다."));
                    }
                    
                    // 성공적인 응답 처리
                    logger.info("채팅 메시지 전송 성공: {} -> {}", userId, request.getChatroomId());
                    return ResponseEntity.ok(GatewayResponse.<Object>success("메시지 전송 성공", result));
                })
                .onErrorResume(throwable -> {
                    // 네트워크 오류 등 예외 상황 처리
                    logger.error("채팅 메시지 전송 서비스 연결 오류: {}", throwable.getMessage());
                    return Mono.just(ResponseEntity.status(500)
                        .body(GatewayResponse.<Object>error("서비스 연결 오류가 발생했습니다.")));
                });
    }
    
    /**
     * Python 채팅 서비스 상태 확인 (관리자 전용)
     * 
     * Python 채팅 서비스의 현재 상태와 연결 상태를 확인합니다.
     * 시스템 모니터링 및 장애 진단에 사용됩니다.
     * 일반 관리자 또는 최고 관리자 권한이 필요합니다.
     * 
     * HTTP Method: GET
     * Endpoint: /api/chat/health
     * 
     * @param authentication 현재 인증된 사용자 정보 (관리자여야 함)
     * @return Mono<ResponseEntity<GatewayResponse<Object>>> 채팅 서비스 상태 정보
     */
    @GetMapping("/health")
    @PreAuthorize("hasAnyAuthority('ROLE_GENERAL_ADMIN', 'ROLE_SUPER_ADMIN')")
    @SuppressWarnings("rawtypes")
    public Mono<ResponseEntity<GatewayResponse<Object>>> healthCheck(Authentication authentication) {
        logger.info("채팅 서비스 헬스체크 요청: {}", authentication.getName());
        
        // Python 채팅 서비스의 헬스체크 엔드포인트 호출
        return pythonServiceClient.healthCheck()
                .map(result -> {
                    logger.info("채팅 서비스 헬스체크 완료: {}", result);
                    return ResponseEntity.ok(GatewayResponse.<Object>success("헬스체크 완료", result));
                })
                .onErrorResume(throwable -> {
                    // 헬스체크 실패 시 서비스 장애 상태로 판단
                    logger.error("채팅 서비스 헬스체크 연결 오류: {}", throwable.getMessage());
                    return Mono.just(ResponseEntity.status(500)
                        .body(GatewayResponse.<Object>error("헬스체크 실패")));
                });
    }
}
