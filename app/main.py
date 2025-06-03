from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from redis.asyncio import Redis # Redis import 주석 처리

from .database import init_db
from .config import settings
from .session import SessionManager
from .connection_manager import ConnectionManager

from .routers import rooms as rooms_router
from .routers import websocket as websocket_router  # ✅ 병합된 웹소켓 라우터 사용

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

    # # Redis 클라이언트 초기화 및 할당 (주석 처리)
    # try:
    #     redis_client = await Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    #     await redis_client.ping() # 연결 테스트
    #     app.state.redis = redis_client
    #     print(f"Redis client connected to {settings.REDIS_URL} and added to app.state")
    # except Exception as e:
    #     print(f"Failed to connect to Redis: {e}")
    #     app.state.redis = None # 연결 실패 시 None으로 설정 (선택적)

# @app.on_event("shutdown") # shutdown 이벤트 핸들러 주석 처리
# async def shutdown_event():
#     if hasattr(app.state, 'redis') and app.state.redis:
#         await app.state.redis.close()
#         print("Redis client closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)