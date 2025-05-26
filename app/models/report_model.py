from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime
from app.database import engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(Integer, nullable=False)
    room_id = Column(Integer, nullable=False)
    
    situation_summary = Column(Text, nullable=False)
    emotion_type = Column(String(100), nullable=False)
    communication_pattern = Column(Text, nullable=False)
    improvement_suggestions = Column(Text, nullable=False)
    counseling_recommended = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
