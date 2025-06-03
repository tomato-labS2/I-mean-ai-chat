from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .config import settings
from .session import SessionManager
from .connection_manager import ConnectionManager

# 라우터 임포트
from .routers import rooms as rooms_router
from .routers import websockets as websockets_router
from .routers import report  # report.py에서 선언한 router 사용

app = FastAPI()

# 전역 매니저 인스턴스 생성
connection_manager = ConnectionManager()
session_manager = SessionManager(
    broadcaster=connection_manager.broadcast_to_room,
    active_connections_provider=connection_manager.get_active_connections_for_room
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(rooms_router.router)
app.include_router(websockets_router.router)
app.include_router(report.router)  # 추가

# 앱 시작 시 DB 초기화 및 매니저 등록
@app.on_event("startup")
async def startup_event():
    await init_db()
    app.state.connection_manager = connection_manager
    app.state.session_manager = session_manager
    print("ConnectionManager 및 SessionManager 초기화 완료")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
