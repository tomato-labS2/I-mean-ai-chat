from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import settings
from .models.base import Base
from sqlalchemy import text
import os

# MySQL 연결 URL 직접 구성
DATABASE_URL = os.getenv("DB_URL")

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

# ✅ 컬럼 존재 여부 확인 함수
async def column_exists(conn, table_name: str, column_name: str) -> bool:
    # 현재 데이터베이스명을 동적으로 가져오기
    db_result = await conn.execute(text("SELECT DATABASE()"))
    current_db = db_result.scalar_one()
    
    result = await conn.execute(text("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :schema_name
          AND TABLE_NAME = :table_name
          AND COLUMN_NAME = :column_name
    """), {"schema_name": current_db, "table_name": table_name, "column_name": column_name})
    return result.scalar_one() > 0

# ✅ 데이터베이스 초기화 함수
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # rooms 테이블 컬럼들 추가
        if not await column_exists(conn, "rooms", "is_active"):
            await conn.execute(text("""
                ALTER TABLE rooms ADD COLUMN is_active BOOLEAN DEFAULT TRUE
            """))

        if not await column_exists(conn, "rooms", "created_at"):
            await conn.execute(text("""
                ALTER TABLE rooms ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            """))

        if not await column_exists(conn, "rooms", "updated_at"):
            await conn.execute(text("""
                ALTER TABLE rooms ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            """))

        # sessions 테이블 컬럼 추가
        if not await column_exists(conn, "sessions", "extension_used"):
            await conn.execute(text("""
                ALTER TABLE sessions ADD COLUMN extension_used BOOLEAN DEFAULT FALSE
            """))
