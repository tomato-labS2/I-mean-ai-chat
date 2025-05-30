from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # 데이터베이스 설정
    DATABASE_URL: str = "mysql+aiomysql://root:1234@localhost:3306/imean"
    
    # JWT 설정
    SECRET_KEY: str = "myVerySecureJwtSecretKeyThatShouldBeAtLeast256BitsLongForHS256Algorithm1234567890"  # 실제 운영환경에서는 환경변수로 관리해야 합니다
    ALGORITHM: str = "HS512"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24시간
    
    # 세션 설정
    SESSION_DURATION_MINUTES: int = 15
    
    # 웹소켓 설정
    WS_PING_INTERVAL: float = 20.0
    WS_PING_TIMEOUT: float = 20.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 추가 환경 변수 무시

settings = Settings() 