package com.ohgiraffers.tomatolab_imean.gateway.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * 채팅 메시지 전송 요청 DTO (Data Transfer Object)
 * 
 * 프론트엔드에서 채팅 메시지를 전송할 때 사용되는 데이터 전송 객체입니다.
 * 특정 채팅방에 메시지를 보내기 위한 필수 정보들을 포함합니다.
 * 
 * 주요 기능:
 * - 대상 채팅방 식별
 * - 전송할 메시지 내용 전달
 * 
 * 유효성 검사:
 * - 채팅방 ID는 필수 입력값
 * - 메시지는 필수 입력값이며 최대 1000자 제한
 * 
 * @author TomatoLab
 * @version 1.0
 */
public class ChatRequest {
    
    /**
     * 메시지를 전송할 채팅방의 고유 식별자
     * 
     * 유효성 검사:
     * - @NotBlank: null, 빈 문자열, 공백만 포함된 문자열 허용하지 않음
     * 
     * 이 ID를 통해 어느 채팅방에 메시지를 전송할지 결정됩니다.
     */
    @NotBlank(message = "채팅방 ID는 필수입니다.")
    private String chatroomId;
    
    /**
     * 전송할 메시지 내용
     * 
     * 유효성 검사:
     * - @NotBlank: null, 빈 문자열, 공백만 포함된 문자열 허용하지 않음
     * - @Size: 최대 1000자까지 허용 (UI 성능 및 스토리지 고려)
     * 
     * 실제 사용자가 입력한 채팅 메시지 텍스트입니다.
     */
    @NotBlank(message = "메시지는 필수입니다.")
    @Size(max = 1000, message = "메시지는 1000자를 초과할 수 없습니다.")
    private String message;
    
    // ==================== 생성자 ====================
    
    /**
     * 기본 생성자
     * JSON 역직렬화 및 Spring Framework에서 사용됩니다.
     */
    public ChatRequest() {}
    
    /**
     * 모든 필드를 초기화하는 생성자
     * 
     * @param chatroomId 대상 채팅방의 고유 식별자
     * @param message 전송할 메시지 내용
     */
    public ChatRequest(String chatroomId, String message) {
        this.chatroomId = chatroomId;
        this.message = message;
    }
    
    // ==================== Getter/Setter ====================
    
    /**
     * 채팅방 ID 반환
     * 
     * @return 메시지를 전송할 채팅방의 고유 식별자
     */
    public String getChatroomId() {
        return chatroomId;
    }
    
    /**
     * 채팅방 ID 설정
     * 
     * @param chatroomId 메시지를 전송할 채팅방의 고유 식별자
     */
    public void setChatroomId(String chatroomId) {
        this.chatroomId = chatroomId;
    }
    
    /**
     * 메시지 내용 반환
     * 
     * @return 전송할 메시지 텍스트
     */
    public String getMessage() {
        return message;
    }
    
    /**
     * 메시지 내용 설정
     * 
     * @param message 전송할 메시지 텍스트
     */
    public void setMessage(String message) {
        this.message = message;
    }
    
    /**
     * 객체의 문자열 표현 반환
     * 
     * 디버깅 및 로깅 목적으로 사용됩니다.
     * 메시지 내용도 포함되므로 민감한 정보 로깅 시 주의가 필요합니다.
     * 
     * @return 객체의 주요 필드값들을 포함한 문자열
     */
    @Override
    public String toString() {
        return "ChatRequest{" +
                "chatroomId='" + chatroomId + '\'' +
                ", message='" + message + '\'' +
                '}';
    }
}
