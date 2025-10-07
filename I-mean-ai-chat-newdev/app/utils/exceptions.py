from typing import Optional, Dict, Any
from fastapi import HTTPException, status

class ImeanBaseException(Exception):
    """I-mean 프로젝트 기본 예외 클래스"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code

class AuthenticationError(ImeanBaseException):
    """인증 관련 예외"""
    
    def __init__(self, message: str = "인증에 실패했습니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class AuthorizationError(ImeanBaseException):
    """권한 관련 예외"""
    
    def __init__(self, message: str = "권한이 없습니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHZ_ERROR",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN
        )

class ValidationError(ImeanBaseException):
    """데이터 검증 예외"""
    
    def __init__(self, message: str = "입력 데이터가 올바르지 않습니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class NotFoundError(ImeanBaseException):
    """리소스 찾을 수 없음 예외"""
    
    def __init__(self, message: str = "요청한 리소스를 찾을 수 없습니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            details=details,
            status_code=status.HTTP_404_NOT_FOUND
        )

class DatabaseError(ImeanBaseException):
    """데이터베이스 관련 예외"""
    
    def __init__(self, message: str = "데이터베이스 오류가 발생했습니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DB_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class OpenAIServiceError(ImeanBaseException):
    """OpenAI 서비스 관련 예외"""
    
    def __init__(self, message: str = "AI 서비스 오류가 발생했습니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="OPENAI_ERROR",
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

class WebSocketError(ImeanBaseException):
    """WebSocket 관련 예외"""
    
    def __init__(self, message: str = "WebSocket 연결 오류가 발생했습니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="WEBSOCKET_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class SessionError(ImeanBaseException):
    """세션 관련 예외"""
    
    def __init__(self, message: str = "세션 오류가 발생했습니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SESSION_ERROR",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class RateLimitError(ImeanBaseException):
    """속도 제한 예외"""
    
    def __init__(self, message: str = "요청이 너무 많습니다. 잠시 후 다시 시도해주세요", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details=details,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

class ConfigurationError(ImeanBaseException):
    """설정 관련 예외"""
    
    def __init__(self, message: str = "설정 오류가 발생했습니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def convert_to_http_exception(exception: ImeanBaseException) -> HTTPException:
    """ImeanBaseException을 FastAPI HTTPException으로 변환"""
    return HTTPException(
        status_code=exception.status_code,
        detail={
            "message": exception.message,
            "error_code": exception.error_code,
            "details": exception.details
        }
    ) 