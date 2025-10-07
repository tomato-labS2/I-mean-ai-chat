import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class CustomFormatter(logging.Formatter):
    """커스텀 로그 포맷터"""
    
    # 색상 코드
    grey = "\x1b[38;21m"
    blue = "\x1b[34;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    # 로그 레벨별 포맷
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: blue + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

class FileFormatter(logging.Formatter):
    """파일 로깅용 포맷터 (색상 코드 제외)"""
    
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    
    def format(self, record):
        formatter = logging.Formatter(self.format_str, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

def setup_logger(
    name: str = "imean_chat",
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    로거 설정
    
    Args:
        name: 로거 이름
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 로그 파일 저장 디렉토리
        max_bytes: 로그 파일 최대 크기
        backup_count: 백업 파일 개수
    
    Returns:
        설정된 로거 인스턴스
    """
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 이미 핸들러가 설정되어 있다면 중복 설정 방지
    if logger.handlers:
        return logger
    
    # 로그 디렉토리 생성
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # 콘솔 핸들러 (개발 환경용)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)
    
    # 파일 핸들러들
    handlers = [
        # 일반 로그
        ("app.log", logging.INFO),
        # 에러 로그
        ("error.log", logging.ERROR),
        # 디버그 로그
        ("debug.log", logging.DEBUG)
    ]
    
    for filename, level in handlers:
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(FileFormatter())
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    로거 인스턴스 반환
    
    Args:
        name: 로거 이름 (None이면 기본 로거 반환)
    
    Returns:
        로거 인스턴스
    """
    if name:
        return logging.getLogger(f"imean_chat.{name}")
    return logging.getLogger("imean_chat")

# 기본 로거 설정
default_logger = setup_logger() 