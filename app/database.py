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
