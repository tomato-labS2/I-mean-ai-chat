import traceback
from typing import Dict, Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from websockets.exceptions import WebSocketException

from .exceptions import (
    ImeanBaseException, 
    convert_to_http_exception,
    AuthenticationError,
    ValidationError,
    DatabaseError,
    WebSocketError,
    OpenAIServiceError
)
from .logger import get_logger

logger = get_logger("error_handler")

class ErrorHandler:
    """전역 에러 핸들러"""
    
    @staticmethod
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        """요청 검증 오류 처리"""
        logger.warning(
            "Validation error occurred",
            extra={
                "path": request.url.path,
                "method": request.method,
                "errors": exc.errors(),
                "client_ip": request.client.host if request.client else None
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "message": "입력 데이터 검증에 실패했습니다",
                "error_code": "VALIDATION_ERROR",
                "details": {
                    "errors": exc.errors()
                }
            }
        )
    
    @staticmethod
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """HTTP 예외 처리"""
        logger.warning(
            f"HTTP exception occurred: {exc.status_code}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
                "detail": exc.detail,
                "client_ip": request.client.host if request.client else None
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": str(exc.detail),
                "error_code": f"HTTP_{exc.status_code}",
                "details": {}
            }
        )
    
    @staticmethod
    async def handle_imean_exception(request: Request, exc: ImeanBaseException) -> JSONResponse:
        """I-mean 커스텀 예외 처리"""
        logger.error(
            f"I-mean exception occurred: {exc.error_code}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "client_ip": request.client.host if request.client else None
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": exc.message,
                "error_code": exc.error_code,
                "details": exc.details
            }
        )
    
    @staticmethod
    async def handle_database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """데이터베이스 오류 처리"""
        logger.error(
            "Database error occurred",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "client_ip": request.client.host if request.client else None
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": "데이터베이스 오류가 발생했습니다",
                "error_code": "DB_ERROR",
                "details": {
                    "error_type": type(exc).__name__
                }
            }
        )
    
    @staticmethod
    async def handle_websocket_error(request: Request, exc: WebSocketException) -> JSONResponse:
        """WebSocket 오류 처리"""
        logger.error(
            "WebSocket error occurred",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "client_ip": request.client.host if request.client else None
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": "WebSocket 연결 오류가 발생했습니다",
                "error_code": "WEBSOCKET_ERROR",
                "details": {
                    "error_type": type(exc).__name__
                }
            }
        )
    
    @staticmethod
    async def handle_openai_error(request: Request, exc: Exception) -> JSONResponse:
        """OpenAI 서비스 오류 처리"""
        logger.error(
            "OpenAI service error occurred",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "client_ip": request.client.host if request.client else None
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "message": "AI 서비스 오류가 발생했습니다",
                "error_code": "OPENAI_ERROR",
                "details": {
                    "error_type": type(exc).__name__
                }
            }
        )
    
    @staticmethod
    async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
        """일반 예외 처리"""
        logger.error(
            "Unexpected error occurred",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(),
                "client_ip": request.client.host if request.client else None
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": "서버 내부 오류가 발생했습니다",
                "error_code": "INTERNAL_ERROR",
                "details": {
                    "error_type": type(exc).__name__
                }
            }
        )

def setup_error_handlers(app):
    """FastAPI 앱에 에러 핸들러 설정"""
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return await ErrorHandler.handle_validation_error(request, exc)
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return await ErrorHandler.handle_http_exception(request, exc)
    
    @app.exception_handler(ImeanBaseException)
    async def imean_exception_handler(request: Request, exc: ImeanBaseException):
        return await ErrorHandler.handle_imean_exception(request, exc)
    
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        return await ErrorHandler.handle_database_error(request, exc)
    
    @app.exception_handler(WebSocketException)
    async def websocket_exception_handler(request: Request, exc: WebSocketException):
        return await ErrorHandler.handle_websocket_error(request, exc)
    
    # OpenAI 관련 예외 처리
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        # OpenAI 관련 예외인지 확인
        if "openai" in str(type(exc)).lower() or "openai" in str(exc).lower():
            return await ErrorHandler.handle_openai_error(request, exc)
        
        return await ErrorHandler.handle_generic_exception(request, exc)

def log_request_info(request: Request, extra_info: Optional[Dict[str, Any]] = None):
    """요청 정보 로깅"""
    log_data = {
        "path": request.url.path,
        "method": request.method,
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "query_params": dict(request.query_params),
    }
    
    if extra_info:
        log_data.update(extra_info)
    
    logger.info("Request received", extra=log_data)

def log_response_info(request: Request, response_data: Dict[str, Any], status_code: int):
    """응답 정보 로깅"""
    log_data = {
        "path": request.url.path,
        "method": request.method,
        "status_code": status_code,
        "response_size": len(str(response_data)),
    }
    
    logger.info("Response sent", extra=log_data) 