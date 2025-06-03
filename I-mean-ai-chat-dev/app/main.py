from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .config import settings
from .session import SessionManager
from .connection_manager import ConnectionManager

from .routers import rooms as rooms_router
from .routers import final_websocket_handler as websocket_router  # ✅ 병합된 웹소켓 라우터 사용

app = FastAPI()

# 전역 매니저 인스턴스
connection_manager = ConnectionManager()
session_manager = SessionManager(
    broadcaster=connection_manager.broadcast_to_room,
    active_connections_provider=connection_manager.get_active_connections_for_room
)

# CORS 허용 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(rooms_router.router)
app.include_router(websocket_router.router)  # ✅ 병합된 웹소켓 라우터 등록

# 애플리케이션 시작 시 초기화
@app.on_event("startup")
async def startup_event():
    await init_db()
    app.state.connection_manager = connection_manager
    app.state.session_manager = session_manager
    print("ConnectionManager 및 SessionManager 초기화 완료")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)