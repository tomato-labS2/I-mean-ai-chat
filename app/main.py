from fastapi import FastAPI
from app.api import report
from app.models.report_model import Base
from app.database import engine

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="GPT Report Parser API",
    description="GPT 응답을 파싱하여 구조화된 리포트를 생성하고 저장하는 API",
    version="1.0.0"
)

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(
    report.router,
    prefix="/reports",
    tags=["reports"]
) 