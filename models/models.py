from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db_connect import Base

class Room(Base):
    __tablename__ = "rooms"
    
    room_id = Column(Integer, primary_key=True, autoincrement=True)
    room_name = Column(String(100), nullable=False)
    couple_id = Column(Integer, ForeignKey("couples.couple_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    sessions = relationship("Session", back_populates="room")
    messages = relationship("Message", back_populates="room")
    logs = relationship("Log", back_populates="room")

class Session(Base):
    __tablename__ = "sessions"
    
    session_id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("rooms.room_id"), nullable=False)
    user_a_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    user_b_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    topic = Column(String(50), nullable=False)  # topic_1_situation, topic_2_emotion
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    extension_used = Column(Boolean, default=False)
    
    room = relationship("Room", back_populates="sessions")
    messages = relationship("Message", back_populates="session")
    logs = relationship("Log", back_populates="session")

class Message(Base):
    __tablename__ = "messages"
    
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.session_id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.room_id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    is_ai_message = Column(Boolean, default=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session", back_populates="messages")
    room = relationship("Room", back_populates="messages")

class Log(Base):
    __tablename__ = "logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.session_id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.room_id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user", "assistant", "system"
    speaker = Column(String(10), nullable=True)  # "A", "B", "AI", system 메시지의 경우 NULL일 수 있음
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    emotion_flagged = Column(Boolean, default=False)
    detected_emotions = Column(Text, nullable=True) # 예: '["분노", "서운함"]' JSON 문자열 형태로 저장

    session = relationship("Session", back_populates="logs")
    room = relationship("Room", back_populates="logs")

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Couple(Base):
    __tablename__ = "couples"
    
    couple_id = Column(Integer, primary_key=True, autoincrement=True)
    user_a_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    user_b_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True) 