from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
import enum
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class SpeakerType(enum.Enum):
    A = "A"
    B = "B"
    AI = "AI"
    UNKNOWN = "UNKNOWN"

class RoleType(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True)
    # username = Column(String(50), unique=True, index=True, nullable=False)
    # password_hash = Column(String(128), nullable=False)
    # email = Column(String(100), unique=True, index=True, nullable=False)
    # created_at = Column(DateTime, default=datetime.utcnow)
    # updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # def set_password(self, password: str):
    #     self.password_hash = generate_password_hash(password)
        
    # def verify_password(self, password: str) -> bool:
    #     return check_password_hash(self.password_hash, password)

class Room(Base, TimestampMixin):
    __tablename__ = "rooms"
    
    room_id = Column(Integer, primary_key=True, index=True)
    room_name = Column(String(100), nullable=False)
    couple_id = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)  # 활성 상태를 나타내는 필드
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sessions = relationship("Session", back_populates="room")
    logs = relationship("ChatLog", back_populates="room")

class Session(Base, TimestampMixin):
    __tablename__ = "sessions"
    
    session_id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("rooms.room_id"), nullable=False)
    user_a_id = Column(Integer, nullable=False)
    user_b_id = Column(Integer, nullable=False)
    topic = Column(String(50), nullable=False)  # topic_1_situation, topic_2_situation 등
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    extension_used = Column(Boolean, default=False)  # 연장 사용 여부
    
    room = relationship("Room", back_populates="sessions")
    logs = relationship("ChatLog", back_populates="session")

class ChatLog(Base, TimestampMixin):
    __tablename__ = "logs"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("rooms.room_id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.session_id"), nullable=True)
    role = Column(Enum(RoleType), nullable=False)
    speaker = Column(Enum(SpeakerType), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    emotion_flagged = Column(Boolean, default=False)
    detected_emotions = Column(Text, nullable=True)
    
    room = relationship("Room", back_populates="logs")
    session = relationship("Session", back_populates="logs") 