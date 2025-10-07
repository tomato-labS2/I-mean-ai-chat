package com.ohgiraffers.tomatolab_imean.gateway.model.dto;

import java.time.LocalDateTime;

/**
 * Gateway 공통 응답 DTO (Data Transfer Object)
 * 
 * 모든 Gateway API 응답에서 사용되는 표준화된 응답 형식입니다.
 * 성공/실패 여부, 메시지, 데이터, 타임스탬프 등을 일관된 형태로 제공합니다.
 * 
 * Generic 타입 T를 사용하여 다양한 종류의 데이터를 담을 수 있습니다.
 * 
 * 응답 구조:
 * - success: 요청 성공/실패 여부
 * - message: 사용자에게 표시할 메시지
 * - data: 실제 응답 데이터 (성공 시)
 * - error: 오류 상세 정보 (실패 시)
 * - timestamp: 응답 생성 시간
 * 
 * @param <T> 응답 데이터의 타입
 * @author TomatoLab
 * @version 1.0
 */
public class GatewayResponse<T> {
    
    /**
     * 요청 처리 성공 여부
     * - true: 성공
     * - false: 실패
     */
    private boolean success;
    
    /**
     * 사용자에게 표시할 메시지
     * 성공/실패에 관계없이 항상 제공되는 설명 메시지입니다.
     */
    private String message;
    
    /**
     * 실제 응답 데이터
     * 성공적인 요청에 대한 결과 데이터를 담습니다.
     * 실패 시에는 null이 될 수 있습니다.
     */
    private T data;
    
    /**
     * 응답 생성 시간
     * 서버에서 응답을 생성한 정확한 시간을 기록합니다.
     * 디버깅 및 로깅 목적으로 사용됩니다.
     */
    private LocalDateTime timestamp;
    
    /**
     * 오류 상세 정보
     * 요청 실패 시 구체적인 오류 내용을 제공합니다.
     * 성공 시에는 null입니다.
     */
    private String error;
    
    // ==================== 생성자 ====================
    
    /**
     * 기본 생성자
     * 
     * 생성 시점의 현재 시간을 자동으로 timestamp에 설정합니다.
     * JSON 역직렬화 및 Spring Framework에서 사용됩니다.
     */
    public GatewayResponse() {
        this.timestamp = LocalDateTime.now();
    }
    
    // ==================== 정적 팩토리 메서드 ====================
    
    /**
     * 성공 응답 생성 (기본 메시지 사용)
     * 
     * 성공적인 요청에 대한 응답을 생성합니다.
     * 기본 성공 메시지를 사용합니다.
     * 
     * @param <T> 응답 데이터의 타입
     * @param data 응답 데이터
     * @return 성공 응답 객체
     */
    public static <T> GatewayResponse<T> success(T data) {
        GatewayResponse<T> response = new GatewayResponse<>();
        response.success = true;
        response.message = "요청이 성공적으로 처리되었습니다.";
        response.data = data;
        return response;
    }
    
    /**
     * 성공 응답 생성 (커스텀 메시지 사용)
     * 
     * 성공적인 요청에 대한 응답을 생성합니다.
     * 사용자 정의 성공 메시지를 사용합니다.
     * 
     * @param <T> 응답 데이터의 타입
     * @param message 커스텀 성공 메시지
     * @param data 응답 데이터
     * @return 성공 응답 객체
     */
    public static <T> GatewayResponse<T> success(String message, T data) {
        GatewayResponse<T> response = new GatewayResponse<>();
        response.success = true;
        response.message = message;
        response.data = data;
        return response;
    }
    
    /**
     * 실패 응답 생성 (기본 메시지 사용)
     * 
     * 실패한 요청에 대한 응답을 생성합니다.
     * 기본 실패 메시지를 사용합니다.
     * 
     * @param <T> 응답 데이터의 타입
     * @param error 오류 상세 정보
     * @return 실패 응답 객체
     */
    public static <T> GatewayResponse<T> error(String error) {
        GatewayResponse<T> response = new GatewayResponse<>();
        response.success = false;
        response.message = "요청 처리 중 오류가 발생했습니다.";
        response.error = error;
        return response;
    }
    
    /**
     * 실패 응답 생성 (커스텀 메시지 사용)
     * 
     * 실패한 요청에 대한 응답을 생성합니다.
     * 사용자 정의 실패 메시지를 사용합니다.
     * 
     * @param <T> 응답 데이터의 타입
     * @param message 커스텀 실패 메시지
     * @param error 오류 상세 정보
     * @return 실패 응답 객체
     */
    public static <T> GatewayResponse<T> error(String message, String error) {
        GatewayResponse<T> response = new GatewayResponse<>();
        response.success = false;
        response.message = message;
        response.error = error;
        return response;
    }
    
    // ==================== Getter/Setter ====================
    
    /**
     * 성공 여부 반환
     * 
     * @return 요청 처리 성공 시 true, 실패 시 false
     */
    public boolean isSuccess() {
        return success;
    }
    
    /**
     * 성공 여부 설정
     * 
     * @param success 요청 처리 성공 여부
     */
    public void setSuccess(boolean success) {
        this.success = success;
    }
    
    /**
     * 메시지 반환
     * 
     * @return 사용자에게 표시할 메시지
     */
    public String getMessage() {
        return message;
    }
    
    /**
     * 메시지 설정
     * 
     * @param message 사용자에게 표시할 메시지
     */
    public void setMessage(String message) {
        this.message = message;
    }
    
    /**
     * 응답 데이터 반환
     * 
     * @return 실제 응답 데이터
     */
    public T getData() {
        return data;
    }
    
    /**
     * 응답 데이터 설정
     * 
     * @param data 실제 응답 데이터
     */
    public void setData(T data) {
        this.data = data;
    }
    
    /**
     * 응답 생성 시간 반환
     * 
     * @return 응답이 생성된 시간
     */
    public LocalDateTime getTimestamp() {
        return timestamp;
    }
    
    /**
     * 응답 생성 시간 설정
     * 
     * @param timestamp 응답이 생성된 시간
     */
    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }
    
    /**
     * 오류 정보 반환
     * 
     * @return 오류 상세 정보 (성공 시 null)
     */
    public String getError() {
        return error;
    }
    
    /**
     * 오류 정보 설정
     * 
     * @param error 오류 상세 정보
     */
    public void setError(String error) {
        this.error = error;
    }
}
