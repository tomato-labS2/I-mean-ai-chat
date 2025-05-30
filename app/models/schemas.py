from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Couple Schemas
class CoupleBase(BaseModel):
    user_a_id: int
    user_b_id: int

class CoupleCreate(CoupleBase):
    pass

class Couple(CoupleBase):
    couple_id: int
    created_at: datetime
    is_active: bool

    class Config:
        orm_mode = True

# Room Schemas
class RoomBase(BaseModel):
    room_name: str
    couple_id: int

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    room_id: int
    created_at: datetime
    # sessions: List["Session"] = [] # 순환 참조 문제 해결을 위해 주석 처리 또는 ForwardRef 사용
    # messages: List["Message"] = []
    # logs: List["Log"] = []

    class Config:
        orm_mode = True

# Session Schemas
class SessionBase(BaseModel):
    room_id: int
    user_a_id: int
    user_b_id: int
    topic: str
    extension_used: bool = False

class SessionCreate(SessionBase):
    pass

class Session(SessionBase):
    session_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    is_active: bool
    # messages: List["Message"] = [] # 순환 참조
    # logs: List["Log"] = [] # 순환 참조

    class Config:
        orm_mode = True

# Message Schemas (사용자 메시지용)
class MessageBase(BaseModel):
    session_id: int
    room_id: int
    sender_id: int
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    message_id: int
    is_ai_message: bool # Log 모델로 대체될 수 있음
    timestamp: datetime

    class Config:
        orm_mode = True

# Log Schemas (모든 채팅 기록 및 시스템 메시지용)
class LogBase(BaseModel):
    session_id: int
    room_id: int
    role: str  # "user", "assistant", "system"
    content: str
    speaker: Optional[str] = None # "A", "B", "AI", system 메시지의 경우 None
    emotion_flagged: bool = False
    detected_emotions: Optional[str] = None # JSON string

class LogCreate(LogBase):
    pass

class Log(LogBase):
    log_id: int
    timestamp: datetime

    class Config:
        orm_mode = True

# ForwardRef를 사용하여 순환 참조 해결 (필요한 경우)
# from pydantic import ForwardRef
# Room.update_forward_refs()
# Session.update_forward_refs()
