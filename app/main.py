from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from redis.asyncio import Redis # Redis import 주석 처리

from .database import init_db
from .config import settings
from .session import SessionManager
from .connection_manager import ConnectionManager

from .routers import rooms as rooms_router
from .routers import websocket as websocket_router  # ✅ 병합된 웹소켓 라우터 사용

from openai import AsyncOpenAI # OpenAI 클라이언트 import
from .services.gpt_service import GPTService # GPTService import
from typing import Optional # Optional 추가

app = FastAPI()

# ConnectionManager는 GPTService에 대한 의존성이 없음
connection_manager = ConnectionManager()

# SessionManager는 GPTService에 의존하므로, app.state 초기화 후 생성하거나
# startup_event 내에서 gpt_service를 가져와서 생성.
# 여기서는 전역 변수로 우선 None으로 선언하고 startup_event에서 초기화.
session_manager: Optional[SessionManager] = None

# CORS 허용 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://imean.shop", 
        "https://d3v60vbjziepuv.cloudfront.net"
    ],
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
    global session_manager # 전역 session_manager 사용 선언

    await init_db()
    app.state.connection_manager = connection_manager

    # OpenAI 클라이언트 및 GPTService 초기화
    gpt_service_instance: Optional[GPTService] = None # 타입 힌팅
    try:
        if not settings.OPENAI_API_KEY:
            print("[MAIN_ERROR] OPENAI_API_KEY is not set in settings. GPTService will not be available.")
            # app.state.openai_client = None # openai_client를 app.state에 직접 저장할 필요는 없을 수 있음
            app.state.gpt_service = None # gpt_service는 None으로 명시적 설정
        else:
            openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            gpt_service_instance = GPTService(openai_client=openai_client)
            app.state.gpt_service = gpt_service_instance # app.state에도 저장 (다른 곳에서 필요할 수 있음)
            print("OpenAI client and GPTService initialized.")
    except Exception as e:
        print(f"[MAIN_ERROR] Failed to initialize OpenAI client or GPTService: {e}")
        app.state.gpt_service = None # 초기화 실패 시 None으로 설정
        # gpt_service_instance는 여전히 None이거나 예외 발생 전 값일 수 있으므로 app.state.gpt_service를 사용

    # SessionManager 초기화 시 GPTService 주입
    session_manager = SessionManager(
        broadcaster=connection_manager.broadcast_to_room,
        active_connections_provider=connection_manager.get_active_connections_for_room,
        gpt_service=app.state.gpt_service # app.state에 저장된 gpt_service 사용 (None일 수 있음)
    )
    app.state.session_manager = session_manager # SessionManager도 app.state에 저장
    print("ConnectionManager 및 SessionManager 초기화 완료 (GPTService 주입됨)")

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