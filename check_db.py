import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

async def check_sessions_table():
<<<<<<< HEAD

=======
>>>>>>> ebe07a4 ([feat] env 설정 및 User model 불필요 필드 주석 처리)
    # MySQL 연결 URL을 환경변수에서 읽음
    DATABASE_URL = os.getenv("DB_URL")
    if not DATABASE_URL:
        raise ValueError("DB_URL 환경변수가 설정되어 있지 않습니다.")
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # sessions 테이블 구조 확인
        result = await conn.execute(text("DESCRIBE sessions"))
        rows = result.fetchall()
        
        print("Sessions 테이블 구조:")
        for row in rows:
            print(f"  {row}")
            
        # extension_used 컬럼이 있는지 확인
        has_extension_used = any('extension_used' in str(row) for row in rows)
        print(f"\nextension_used 컬럼 존재 여부: {has_extension_used}")
        
        # 현재 세션 데이터 확인
        result = await conn.execute(text("SELECT * FROM sessions ORDER BY session_id DESC LIMIT 5"))
        sessions = result.fetchall()
        
        print(f"\n최근 세션 데이터 (최대 5개):")
        for session in sessions:
            print(f"  {session}")

if __name__ == "__main__":
    asyncio.run(check_sessions_table()) 