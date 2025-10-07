from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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

# 로깅 및 에러 핸들링 시스템 import
from .utils.logger import setup_logger, get_logger
from .utils.error_handler import setup_error_handlers, log_request_info, log_response_info
from .utils.exceptions import ConfigurationError, OpenAIServiceError

# 로거 설정
logger = get_logger("main")

app = FastAPI(
    title="I-mean AI Chat API",
    description="AI 기반 커플 상담형 챗 서비스",
    version="1.0.0"
)

# 에러 핸들러 설정
setup_error_handlers(app)

# ConnectionManager는 GPTService에 대한 의존성이 없음
connection_manager = ConnectionManager()

# SessionManager는 GPTService에 의존하므로, app.state 초기화 후 생성하거나
# startup_event 내에서 gpt_service를 가져와서 생성.
# 여기서는 전역 변수로 우선 None으로 선언하고 startup_event에서 초기화.
session_manager: Optional[SessionManager] = None

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
    global session_manager # 전역 session_manager 사용 선언
    
    logger.info("Starting I-mean AI Chat application...")
    
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise ConfigurationError(f"데이터베이스 초기화 실패: {e}")
    
    app.state.connection_manager = connection_manager
    logger.info("ConnectionManager initialized")

    # OpenAI 클라이언트 및 GPTService 초기화
    gpt_service_instance: Optional[GPTService] = None # 타입 힌팅
    try:
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is not set in settings. GPTService will not be available.")
            app.state.gpt_service = None # gpt_service는 None으로 명시적 설정
        else:
            openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            gpt_service_instance = GPTService(openai_client=openai_client)
            app.state.gpt_service = gpt_service_instance # app.state에도 저장 (다른 곳에서 필요할 수 있음)
            logger.info("OpenAI client and GPTService initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client or GPTService: {e}", exc_info=True)
        app.state.gpt_service = None # 초기화 실패 시 None으로 설정
        raise OpenAIServiceError(f"OpenAI 서비스 초기화 실패: {e}")

    # SessionManager 초기화 시 GPTService 주입
    try:
        session_manager = SessionManager(
            broadcaster=connection_manager.broadcast_to_room,
            active_connections_provider=connection_manager.get_active_connections_for_room,
            gpt_service=app.state.gpt_service # app.state에 저장된 gpt_service 사용 (None일 수 있음)
        )
        app.state.session_manager = session_manager # SessionManager도 app.state에 저장
        logger.info("SessionManager initialized successfully with GPTService injection")
    except Exception as e:
        logger.error(f"Failed to initialize SessionManager: {e}", exc_info=True)
        raise ConfigurationError(f"SessionManager 초기화 실패: {e}")

    # # Redis 클라이언트 초기화 및 할당 (주석 처리)
    # try:
    #     redis_client = await Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    #     await redis_client.ping() # 연결 테스트
    #     app.state.redis = redis_client
    #     logger.info(f"Redis client connected to {settings.REDIS_URL}")
    # except Exception as e:
    #     logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
    #     app.state.redis = None # 연결 실패 시 None으로 설정 (선택적)

    logger.info("Application startup completed successfully")

# @app.on_event("shutdown") # shutdown 이벤트 핸들러 주석 처리
# async def shutdown_event():
#     if hasattr(app.state, 'redis') and app.state.redis:
#         await app.state.redis.close()
#         logger.info("Redis client closed")

# 미들웨어: 요청/응답 로깅
@app.middleware("http")
async def log_requests(request, call_next):
    """요청과 응답을 로깅하는 미들웨어"""
    log_request_info(request)
    
    response = await call_next(request)
    
    # 응답 내용을 로깅 (민감한 정보는 제외)
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk
    
    # 응답을 다시 생성 (body_iterator는 한 번만 읽을 수 있음)
    response_data = response_body.decode() if response_body else ""
    
    log_response_info(request, {"response_length": len(response_data)}, response.status_code)
    
    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type
    )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)