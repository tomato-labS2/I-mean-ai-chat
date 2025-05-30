import asyncio
import aiomysql
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_sessions_table():
    # MySQL 연결 URL
    DATABASE_URL = "mysql+aiomysql://gorilla:gorilla@localhost/i_mean"
    
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