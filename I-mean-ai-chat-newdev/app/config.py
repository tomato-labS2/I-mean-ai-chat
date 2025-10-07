from dotenv import load_dotenv
load_dotenv(dotenv_path=".env.dev")

from pydantic_settings import BaseSettings
from fastapi import WebSocket
import asyncio
from app.utils.logger import get_logger

logger = get_logger("config")

class Settings(BaseSettings):
    # 데이터베이스 설정
    DB_URL: str  # 기본값 제거, 반드시 .env에서 읽음
    REDIS_URL : str = "redis://localhost:6379"

    # JWT 설정
    JWT_SECRET_KEY: str  # .env에서 읽어옴
    ALGORITHM: str = "HS512"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24시간
    
    # 세션 설정
    SESSION_DURATION_MINUTES: int = 1

    # AI 상담사 설정
    OPENAI_API_KEY: str = ""  # 환경변수에서 읽어옴, 기본값은 빈 문자열

    # FastAPI WebSocket에서 ping 응답 유지용
    async def websocket_heartbeat(websocket: WebSocket):
        while True:
            await websocket.ping()  # 또는 await websocket.ping()
            await asyncio.sleep(10)

    # 웹소켓 설정
    WS_PING_INTERVAL: float = 20.0
    WS_PING_TIMEOUT: float = 20.0

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 추가 환경 변수 무시

settings = Settings()

# 설정 검증 및 로깅
def validate_settings():
    """설정값 검증"""
    logger.info("Validating application settings...")
    
    # 필수 설정 검증
    if not settings.DB_URL:
        logger.error("DB_URL is not set")
        raise ValueError("DB_URL is required")
    
    if not settings.JWT_SECRET_KEY:
        logger.error("JWT_SECRET_KEY is not set")
        raise ValueError("JWT_SECRET_KEY is required")
    
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY is not set - AI features will be disabled")
    else:
        logger.info("OpenAI API key is configured")
    
    logger.info(f"Database URL: {settings.DB_URL[:20]}...")  # 보안상 일부만 로깅
    logger.info(f"Session duration: {settings.SESSION_DURATION_MINUTES} minutes")
    logger.info("Settings validation completed")

# 설정 검증 실행
try:
    validate_settings()
except Exception as e:
    logger.error(f"Settings validation failed: {e}")
    raise

print('실제 DB URL:', settings.DB_URL)