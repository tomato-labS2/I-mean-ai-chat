from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, Text, Boolean, DateTime
from app.models.base import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("rooms.room_id"), unique=True, nullable=False)  # room_id당 1개 리포트
    session_id = Column(Integer, ForeignKey("sessions.session_id"), nullable=False)
    situation_summary = Column(Text)
    emotion_summary = Column(Text)
    communication_pattern = Column(Text)
    recommendations = Column(Text)
    suggest_counseling = Column(Boolean, default=False)
    report_generated = Column(Boolean, default=True)
    report_generated_at = Column(DateTime, default=datetime.utcnow)
