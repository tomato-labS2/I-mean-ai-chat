from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import asyncio
from jose import JWTError, jwt

from ..database import get_db
from ..models.models import Session as DBSession, Room, User, Message, Couple
from .auth import get_current_user

router = APIRouter()

class SessionCreate(BaseModel):
    room_id: int
    topic: str

class SessionResponse(BaseModel):
    session_id: int
    room_id: int
    user_a_id: int
    user_b_id: int
    topic: str
    start_time: datetime
    end_time: Optional[datetime]
    is_active: bool
    extension_used: bool

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: str
    is_ai_message: bool = False

class MessageResponse(BaseModel):
    message_id: int
    session_id: int
    room_id: int
    sender_id: Optional[int]
    is_ai_message: bool
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

# WebSocket 연결 관리를 위한 클래스
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}  # room_id: {user_id: WebSocket}
        self.session_timers: dict = {}  # session_id: asyncio.Task
        self.user_responses: dict = {} # session_id: {user_id: str} - 사용자의 연장/종료 응답 저장
        self.pending_questions: dict = {} # session_id: Set[user_id] - 응답 대기 중인 사용자 저장

    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][user_id] = websocket

    def disconnect(self, room_id: int, user_id: int):
        if room_id in self.active_connections:
            self.active_connections[room_id].pop(user_id, None)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: int, message: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id].values():
                await connection.send_json(message)

    # 특정 사용자에게만 메시지 전송
    async def send_personal_message(self, room_id: int, user_id: int, message: dict):
        if room_id in self.active_connections and user_id in self.active_connections[room_id]:
            websocket = self.active_connections[room_id][user_id]
            await websocket.send_json(message)

    # 타이머 만료 시 질문 발송 로직 (기본 형태, 추후 확장)
    async def ask_to_continue(self, session_id: int, room_id: int, topic: str, db: AsyncSession):
        # 두 사용자 ID를 알아내야 함 (DB 조회 또는 세션 생성 시 정보 저장)
        result = await db.execute(select(DBSession).filter(DBSession.session_id == session_id))
        session_db = result.scalars().first()
        if not session_db:
            return

        users_in_room = list(self.active_connections.get(room_id, {}).keys())
        if len(users_in_room) < 2: # 상대방이 없을 경우 처리 (옵션)
            # 일단 여기서는 두 명 모두에게 보낸다고 가정
            pass 

        self.user_responses[session_id] = {} # 이전 응답 초기화
        self.pending_questions[session_id] = {session_db.user_a_id, session_db.user_b_id}

        question = f"{topic}에 대한 대화 시간이 종료되었습니다. 계속하시겠습니까?"
        options = [
            {"text": "네. 아직 시간이 필요합니다", "value": "extend_yes"},
            {"text": "아니오. 넘어가겠습니다" if topic == "상황" else "아니오. 괜찮습니다", "value": "extend_no"}
        ]
        message = {
            "type": "question",
            "session_id": session_id,
            "question": question,
            "options": options
        }
        await self.broadcast(room_id, message)

    # 사용자의 응답을 기록하고 처리하는 로직
    async def record_user_response(self, session_id: int, user_id: int, response_value: str, db: AsyncSession, room_id: int):
        if session_id not in self.user_responses:
            self.user_responses[session_id] = {}
        self.user_responses[session_id][user_id] = response_value
        
        if session_id in self.pending_questions:
            self.pending_questions[session_id].discard(user_id)

        # 모든 사용자가 응답했는지 확인
        if session_id in self.pending_questions and not self.pending_questions[session_id]:
            # 모든 응답이 모였으므로 처리 로직 호출
            del self.pending_questions[session_id] # 처리 후 삭제
            return "all_responses_received"
        elif session_id not in self.pending_questions: # 이미 처리된 요청일 수 있음
            return "already_processed"
        return "waiting" # 아직 모든 응답이 오지 않음
    
    # 모든 응답이 모였을 때의 처리 (실제 로직은 websocket.py 또는 서비스 레이어에서 호출)
    # async def process_all_responses(self, session_id: int, db: AsyncSession, room_id: int):
    #     pass # 실제 로직은 websocket.py에서 구현

    def start_session_timer(self, session_id: int, db: AsyncSession, duration_minutes: int = 1):
        if session_id in self.session_timers:
            self.session_timers[session_id].cancel()

        async def end_session_or_ask():
            await asyncio.sleep(duration_minutes * 60)
            result = await db.execute(select(DBSession).filter(DBSession.session_id == session_id))
            session_db = result.scalars().first()

            if session_db and session_db.is_active:
                current_topic_str = "상황" if session_db.topic == "topic_1_situation" else "감정"
                
                if session_db.topic == "topic_1_situation":
                    if not session_db.extension_used: # 상황 & 첫 1분 종료
                        # 연장 질문 (시나리오 1)
                        await self.ask_to_continue(session_id, session_db.room_id, current_topic_str, db)
                    else: # 상황 & 이미 연장됨 (연장된 1분 마저 종료) (시나리오 6)
                        # 감정 채팅으로 자동 전환
                        await self.initiate_emotion_chat(session_db, db, "상황에 대한 충분한 대화를 나누셨습니다. 이제 그 상황에서 느꼈던 감정들을 서로 공유해보는 시간을 가져보겠습니다.")
                elif session_db.topic == "topic_2_emotion":
                    if not session_db.extension_used: # 감정 & 첫 1분 종료
                        # 연장 질문 (시나리오 7)
                        await self.ask_to_continue(session_id, session_db.room_id, current_topic_str, db)
                    else: # 감정 & 이미 연장됨 (연장된 1분 마저 종료) (시나리오 12)
                        # 채팅 종료
                        await self.broadcast(session_db.room_id, {
                            "type": "system_message",
                            "content": "채팅을 종료합니다. 상황과 감정에 대한 충분한 대화를 나누셨습니다. 서로의 마음을 이해하고 공감하는 뜻깊은 시간이었습니다. 오늘의 대화가 두 분의 관계에 도움이 되기를 바랍니다."
                        })
                        await self.end_current_session_in_db(session_db, db)
            
            if session_id in self.session_timers:
                self.session_timers.pop(session_id, None)

        self.session_timers[session_id] = asyncio.create_task(end_session_or_ask())
    
    async def end_current_session_in_db(self, session_db: DBSession, db: AsyncSession):
        session_db.is_active = False
        session_db.end_time = datetime.utcnow()
        await db.commit()

    async def initiate_emotion_chat(self, current_session: DBSession, db: AsyncSession, transition_message: str):
        # 기존 세션 비활성화
        await self.end_current_session_in_db(current_session, db)

        # 시스템 메시지 발송
        await self.broadcast(current_session.room_id, {
            "type": "system_message",
            "session_id": current_session.session_id, # 이전 세션 ID를 포함하여 클라이언트가 컨텍스트를 알 수 있도록
            "content": transition_message
        })

        # 새로운 감정 세션 생성 (DB)
        new_emotion_session = DBSession(
            room_id=current_session.room_id,
            user_a_id=current_session.user_a_id,
            user_b_id=current_session.user_b_id,
            topic="topic_2_emotion",
            extension_used=False, # 감정 세션은 새로 시작하므로 연장 미사용
            is_active=True
        )
        db.add(new_emotion_session)
        await db.commit()
        await db.refresh(new_emotion_session)

        # 새 감정 세션 시작 시스템 메시지 (옵션: 위 메시지에 통합 가능)
        await self.broadcast(new_emotion_session.room_id, {
            "type": "session_start",
            "session_id": new_emotion_session.session_id,
            "topic": new_emotion_session.topic,
            "message": "이제 감정에 대한 대화를 시작하겠습니다. 앞서 나눈 상황에 대해 각자 어떤 감정을 느꼈는지 솔직하게 표현해주세요. 상대방의 감정도 공감하며 들어주시기 바랍니다."
        })

        # 새 감정 세션 타이머 시작
        self.start_session_timer(new_emotion_session.session_id, db)

manager = ConnectionManager()

SECRET_KEY = "your-secret-key"  # 실제 사용 중인 값과 동일하게!
ALGORITHM = "HS256"

@router.post("/", response_model=SessionResponse)
async def create_session(
    session: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 채팅방 존재 및 권한 확인
    result = await db.execute(select(Room).filter(Room.room_id == session.room_id))
    room = result.scalars().first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="채팅방을 찾을 수 없습니다"
        )

    # 활성화된 세션이 있는지 확인
    result = await db.execute(select(DBSession).filter(
        DBSession.room_id == session.room_id,
        DBSession.is_active == True
    ))
    active_session = result.scalars().first()
    
    if active_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 활성화된 세션이 있습니다"
        )

    # 커플 정보 조회
    result = await db.execute(select(Couple).filter(
        Couple.couple_id == room.couple_id,
        (Couple.user_a_id == current_user.user_id) | (Couple.user_b_id == current_user.user_id),
        Couple.is_active == True
    ))
    couple = result.scalars().first()

    if not couple:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="커플 관계가 아니거나 권한이 없습니다"
        )

    # 새 세션 생성
    db_session = DBSession(
        room_id=session.room_id,
        user_a_id=couple.user_a_id,
        user_b_id=couple.user_b_id,
        topic=session.topic,
        is_active=True
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)

    # AI 안내 메시지 생성
    ai_message = Message(
        session_id=db_session.session_id,
        room_id=session.room_id,
        is_ai_message=True,
        content="안녕하세요~ 커플 상담을 도와드릴 AI 상담사입니다. 오늘은 어떤 이야기를 나누고 싶으신가요?"
    )
    db.add(ai_message)
    await db.commit()

    # 세션 타이머 시작
    manager.start_session_timer(db_session.session_id, db)

    return db_session

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = await db.execute(select(DBSession).join(
        Room
    ).join(
        Couple,
        Room.couple_id == Couple.couple_id
    ).filter(
        DBSession.session_id == session_id,
        (Couple.user_a_id == current_user.user_id) | (Couple.user_b_id == current_user.user_id),
        Couple.is_active == True
    ))
    session = session.scalars().first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다"
        )

    return session

@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = await db.execute(select(DBSession).join(
        Room
    ).join(
        Couple,
        Room.couple_id == Couple.couple_id
    ).filter(
        DBSession.session_id == session_id,
        (Couple.user_a_id == current_user.user_id) | (Couple.user_b_id == current_user.user_id),
        Couple.is_active == True
    ))
    session = session.scalars().first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다"
        )

    messages = await db.execute(select(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.timestamp))
    messages = messages.scalars().all()

    return messages

@router.websocket("/ws/{room_id}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    # 1. 쿼리스트링에서 토큰 추출
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    # 2. 토큰 검증
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            await websocket.close(code=1008)
            return
        # 필요하다면 여기서 DB에서 사용자 조회 등 추가 검증
    except JWTError:
        await websocket.close(code=1008)
        return

    print(f"WebSocket 연결 시작: room_id={room_id}, user_id={user_id}, username={username}")
    await manager.connect(websocket, room_id, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            
            # 메시지 저장
            message = Message(
                session_id=data["session_id"],
                room_id=room_id,
                sender_id=user_id,
                content=data["content"],
                is_ai_message=False
            )
            db.add(message)
            await db.commit()
            await db.refresh(message)

            # 메시지 브로드캐스트
            await manager.broadcast(room_id, {
                "type": "message",
                "message_id": message.message_id,
                "session_id": message.session_id,
                "sender_id": message.sender_id,
                "content": message.content,
                "timestamp": message.timestamp.isoformat()
            })

    except WebSocketDisconnect:
        manager.disconnect(room_id, user_id)
        await manager.broadcast(room_id, {
            "type": "user_disconnect",
            "user_id": user_id,
            "message": "사용자가 채팅방을 나갔습니다"
        }) 