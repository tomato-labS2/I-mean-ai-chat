package com.ohgiraffers.tomatolab_imean.gateway.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * AI 채팅 요청 DTO (Data Transfer Object)
 * 
 * 프론트엔드에서 AI 채팅 기능을 요청할 때 사용되는 데이터 전송 객체입니다.
 * 사용자의 질문(프롬프트)과 대화 컨텍스트 정보를 포함합니다.
 * 
 * 주요 기능:
 * - 사용자 입력 프롬프트 전달
 * - 대화 연속성을 위한 conversation ID 관리
 * - AI 모델 선택 기능 (선택사항)
 * 
 * 유효성 검사:
 * - 프롬프트는 필수 입력값
 * - 프롬프트 최대 길이 2000자 제한
 * 
 * @author TomatoLab
 * @version 1.0
 */
public class AiRequest {
    
    /**
     * 사용자가 AI에게 보내는 질문이나 명령
     * 
     * 유효성 검사:
     * - @NotBlank: null, 빈 문자열, 공백만 포함된 문자열 허용하지 않음
     * - @Size: 최대 2000자까지 허용 (토큰 제한 및 성능 고려)
     */
    @NotBlank(message = "프롬프트는 필수입니다.")
    @Size(max = 2000, message = "프롬프트는 2000자를 초과할 수 없습니다.")
    private String prompt;
    
    /**
     * 대화 연속성을 위한 고유 식별자 (선택사항)
     * 
     * 이전 대화와 연결하여 컨텍스트를 유지하고 싶을 때 사용합니다.
     * null인 경우 새로운 대화로 처리됩니다.
     */
    private String conversationId;
    
    /**
     * 사용할 AI 모델 지정 (선택사항)
     * 
     * 예: "gpt-3.5-turbo", "gpt-4", "claude-3" 등
     * null인 경우 시스템 기본 모델을 사용합니다.
     */
    private String aiModel;
    
    // ==================== 생성자 ====================
    
    /**
     * 기본 생성자
     * JSON 역직렬화 및 Spring Framework에서 사용됩니다.
     */
    public AiRequest() {}
    
    /**
     * 프롬프트만으로 생성하는 생성자
     * 
     * @param prompt 사용자 질문/명령
     */
    public AiRequest(String prompt) {
        this.prompt = prompt;
    }
    
    /**
     * 프롬프트와 대화 ID로 생성하는 생성자
     * 
     * @param prompt 사용자 질문/명령
     * @param conversationId 대화 연속성을 위한 ID
     */
    public AiRequest(String prompt, String conversationId) {
        this.prompt = prompt;
        this.conversationId = conversationId;
    }
    
    // ==================== Getter/Setter ====================
    
    /**
     * 프롬프트 반환
     * 
     * @return 사용자가 입력한 질문이나 명령
     */
    public String getPrompt() {
        return prompt;
    }
    
    /**
     * 프롬프트 설정
     * 
     * @param prompt 사용자가 입력한 질문이나 명령
     */
    public void setPrompt(String prompt) {
        this.prompt = prompt;
    }
    
    /**
     * 대화 ID 반환
     * 
     * @return 대화 연속성을 위한 고유 식별자
     */
    public String getConversationId() {
        return conversationId;
    }
    
    /**
     * 대화 ID 설정
     * 
     * @param conversationId 대화 연속성을 위한 고유 식별자
     */
    public void setConversationId(String conversationId) {
        this.conversationId = conversationId;
    }
    
    /**
     * AI 모델명 반환
     * 
     * @return 사용할 AI 모델의 식별자
     */
    public String getAiModel() {
        return aiModel;
    }
    
    /**
     * AI 모델명 설정
     * 
     * @param aiModel 사용할 AI 모델의 식별자
     */
    public void setAiModel(String aiModel) {
        this.aiModel = aiModel;
    }
    
    /**
     * 객체의 문자열 표현 반환
     * 
     * 디버깅 및 로깅 목적으로 사용됩니다.
     * 보안상 민감한 정보는 포함되지 않습니다.
     * 
     * @return 객체의 주요 필드값들을 포함한 문자열
     */
    @Override
    public String toString() {
        return "AiRequest{" +
                "prompt='" + prompt + '\'' +
                ", conversationId='" + conversationId + '\'' +
                ", aiModel='" + aiModel + '\'' +
                '}';
    }
}
