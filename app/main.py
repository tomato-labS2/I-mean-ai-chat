<<<<<<< HEAD
<<<<<<< HEAD
from fastapi import FastAPI
from app.api import report
from app.models.report_model import Base
from app.database import engine
=======
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query, Body, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .database import get_db, init_db
from .models.chat import Room, Session, ChatLog, SpeakerType, RoleType, User
from datetime import datetime, timedelta
import json
from typing import Dict, Set, Optional
import jwt
from .config import settings
from pydantic import BaseModel
import asyncio
from sqlalchemy import update
>>>>>>> 7ce7d69 (채팅로직구현)
=======
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .config import settings # settings는 다른 모듈에서도 필요할 수 있으므로 유지
from .session import SessionManager
from .connection_manager import ConnectionManager # 새로 분리된 ConnectionManager
from .routers import rooms as rooms_router
from .routers import websockets as websockets_router # 새로 분리된 웹소켓 라우터
>>>>>>> d1a8801 (채팅중간저장)

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="GPT Report Parser API",
    description="GPT 응답을 파싱하여 구조화된 리포트를 생성하고 저장하는 API",
    version="1.0.0"
)

<<<<<<< HEAD
<<<<<<< HEAD
# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(
    report.router,
    prefix="/reports",
    tags=["reports"]
) 
=======
# CORS 설정 - FastAPI 사용 시, 클라이언트가 다른 도메인에서 API 요청을 보낼 수 있도록 허용하거나 제한
=======
# 전역 Manager 인스턴스 생성
connection_manager = ConnectionManager()
session_manager = SessionManager(
    broadcaster=connection_manager.broadcast_to_room,
    active_connections_provider=connection_manager.get_active_connections_for_room
)

# CORS 설정
>>>>>>> d1a8801 (채팅중간저장)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 실제 프로덕션에서는 특정 도메인만 허용하는 것이 좋습니다.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(rooms_router.router)
app.include_router(websockets_router.router) # 웹소켓 라우터 등록

# 애플리케이션 시작 시 데이터베이스 초기화
@app.on_event("startup")
async def startup_event():
    await init_db()
    # 애플리케이션 상태(app.state)에 매니저 인스턴스 저장
    app.state.connection_manager = connection_manager
    app.state.session_manager = session_manager
    print("ConnectionManager 및 SessionManager 초기화 완료")

if __name__ == "__main__":
    import uvicorn
<<<<<<< HEAD
    uvicorn.run(app, host="0.0.0.0", port=8000) 
>>>>>>> 7ce7d69 (채팅로직구현)
=======
    # reload=True는 개발 중에만 사용하고, 프로덕션에서는 False로 설정하거나 uvicorn 옵션에서 제거합니다.
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 
>>>>>>> d1a8801 (채팅중간저장)
