<<<<<<< HEAD
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings  # 환경변수에서 DB_URL 가져오기

DATABASE_URL = settings.DB_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
=======
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import settings
from .models.base import Base
from sqlalchemy import text

# MySQL 연결 URL 직접 구성
DATABASE_URL = f"mysql+aiomysql://root:1234@localhost/imean"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# 데이터베이스 초기화 함수
async def init_db():
    async with engine.begin() as conn:
        # 기존 테이블이 있다면 삭제 (이 부분을 주석 처리하거나 삭제하여 데이터 유실 방지)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # 테이블 생성 (없는 테이블만 생성)
        await conn.run_sync(Base.metadata.create_all)
        
        # is_active 컬럼이 없다면 추가
        try:
            await conn.execute(text("""
                ALTER TABLE rooms 
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
                ADD COLUMN IF NOT EXISTS created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ADD COLUMN IF NOT EXISTS updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            """))
        except Exception as e:
            print(f"Error adding columns to rooms: {e}")
            
        # extension_used 컬럼이 없다면 추가
        try:
            await conn.execute(text("""
                ALTER TABLE sessions 
                ADD COLUMN IF NOT EXISTS extension_used BOOLEAN DEFAULT FALSE
            """))
        except Exception as e:
            print(f"Error adding extension_used column to sessions: {e}") 
>>>>>>> 7ce7d69 (채팅로직구현)
