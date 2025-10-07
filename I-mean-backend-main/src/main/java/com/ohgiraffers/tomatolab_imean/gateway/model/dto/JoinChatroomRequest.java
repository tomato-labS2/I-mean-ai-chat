package com.ohgiraffers.tomatolab_imean.gateway.model.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * 채팅방 입장 요청 DTO (Data Transfer Object)
 * 
 * 프론트엔드에서 특정 채팅방에 입장을 요청할 때 사용되는 데이터 전송 객체입니다.
 * 사용자가 참여하고자 하는 채팅방의 식별 정보를 포함합니다.
 * 
 * 주요 기능:
 * - 입장할 채팅방 식별
 * - 채팅방 입장 권한 검증용 데이터 제공
 * 
 * 유효성 검사:
 * - 채팅방 ID는 필수 입력값
 * 
 * 사용 시나리오:
 * 1. 사용자가 채팅방 목록에서 특정 채팅방 선택
 * 2. 프론트엔드에서 해당 채팅방 ID로 입장 요청
 * 3. 서버에서 권한 확인 후 채팅방 입장 처리
 * 
 * @author TomatoLab
 * @version 1.0
 */
public class JoinChatroomRequest {
    
    /**
     * 입장하고자 하는 채팅방의 고유 식별자
     * 
     * 유효성 검사:
     * - @NotBlank: null, 빈 문자열, 공백만 포함된 문자열 허용하지 않음
     * 
     * 이 ID를 통해 사용자가 어느 채팅방에 입장하려는지 식별하고,
     * 해당 채팅방에 대한 접근 권한을 검증합니다.
     */
    @NotBlank(message = "채팅방 ID는 필수입니다.")
    private String chatroomId;
    
    // ==================== 생성자 ====================
    
    /**
     * 기본 생성자
     * JSON 역직렬화 및 Spring Framework에서 사용됩니다.
     */
    public JoinChatroomRequest() {}
    
    /**
     * 채팅방 ID로 초기화하는 생성자
     * 
     * @param chatroomId 입장할 채팅방의 고유 식별자
     */
    public JoinChatroomRequest(String chatroomId) {
        this.chatroomId = chatroomId;
    }
    
    // ==================== Getter/Setter ====================
    
    /**
     * 채팅방 ID 반환
     * 
     * @return 입장할 채팅방의 고유 식별자
     */
    public String getChatroomId() {
        return chatroomId;
    }
    
    /**
     * 채팅방 ID 설정
     * 
     * @param chatroomId 입장할 채팅방의 고유 식별자
     */
    public void setChatroomId(String chatroomId) {
        this.chatroomId = chatroomId;
    }
    
    /**
     * 객체의 문자열 표현 반환
     * 
     * 디버깅 및 로깅 목적으로 사용됩니다.
     * 채팅방 ID 정보를 포함합니다.
     * 
     * @return 객체의 주요 필드값들을 포함한 문자열
     */
    @Override
    public String toString() {
        return "JoinChatroomRequest{" +
                "chatroomId='" + chatroomId + '\'' +
                '}';
    }
}
