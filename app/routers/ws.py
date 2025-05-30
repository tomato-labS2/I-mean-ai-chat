from fastapi import WebSocket, WebSocketDisconnect, Query, WebSocketState
from typing import Optional
from ..database import get_db
from ..models import Log
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from ..models import Session as SessionModel  # 충돌 방지용 별칭
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Session as SessionModel
from ..models import Couple
from sqlalchemy import or_

async def process_message(websocket: WebSocket, data: dict, room_id: int, user_id: str, db: AsyncSession):
    try:
        message_type = data.get("type")
        
        # 핑/퐁 처리를 가장 먼저
        if message_type == "ping":
            await websocket.send_json({"type": "pong"})
            return
            
        # 일반 메시지 처리
        if message_type == "message":
            content = data.get("content")
            if not content:
                print(f"[WS_ROUTER_WARNING] Empty content received from user {user_id}")
                return
                
            # 발신자 타입 결정 (A or B)
            session = await db.execute(
                text("""
                    SELECT id, user_a_id, user_b_id 
                    FROM sessions 
                    WHERE room_id = :room_id 
                    AND is_active = TRUE 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """),
                {"room_id": room_id}
            )
            session_data = session.fetchone()
            
            if not session_data:
                print(f"[WS_ROUTER_ERROR] No active session found for room {room_id}")
                return
                
            speaker_type = "A" if user_id == session_data.user_a_id else "B"
            print(f"[WS_ROUTER_DEBUG] User {user_id} identified as Speaker {speaker_type}")
            
            # 메시지 DB 저장
            current_time = datetime.utcnow()
            await db.execute(
                text("""
                    INSERT INTO logs (
                        room_id, session_id, role, speaker, content, 
                        timestamp, emotion_flagged, created_at, updated_at
                    ) VALUES (
                        :room_id, :session_id, 'USER', :speaker, :content,
                        :timestamp, FALSE, :created_at, :updated_at
                    )
                """),
                {
                    "room_id": room_id,
                    "session_id": session_data.id,
                    "speaker": speaker_type,
                    "content": content,
                    "timestamp": current_time,
                    "created_at": current_time,
                    "updated_at": current_time
                }
            )
            await db.commit()
            
            # 브로드캐스트 메시지 구성
            broadcast_message = {
                "type": "message",
                "content": content,
                "speaker": speaker_type,
                "timestamp": current_time.isoformat()
            }
            
            # 방의 모든 사용자에게 메시지 브로드캐스트
            await manager.broadcast_to_room(room_id, broadcast_message)
            print(f"[WS_ROUTER_DEBUG] Message broadcasted to room {room_id}")
            
        elif message_type == "typing":
            # 타이핑 상태 브로드캐스트 (옵션)
            typing_message = {
                "type": "typing",
                "user_id": user_id,
                "is_typing": data.get("is_typing", True)
            }
            await manager.broadcast_to_room(
                room_id, 
                typing_message,
                target_user_id=None  # 발신자를 제외한 모든 사용자에게 전송
            )
            
    except Exception as e:
        print(f"[WS_ROUTER_ERROR] Error processing message from user {user_id} in room {room_id}: {e}")
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json({
                "type": "error",
                "message": "메시지 처리 중 오류가 발생했습니다."
            })

@router.websocket("/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    user_id: str,
    session_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    try:
        print(f"[WS_ROUTER_ENDPOINT] Connecting User {user_id} to room {room_id}")
        await websocket.accept()
        
        # 기존 세션 ID가 있는 경우 해당 세션의 유효성 검증
        current_session = None
        if session_id:
            current_session = await validate_session(db, room_id, session_id)
        
        # 유효한 세션이 없으면 새 세션 생성
        if not current_session:
            current_session = await create_new_session(db, room_id, user_id)
            session_id = current_session.id
        
        await manager.connect(websocket, room_id, user_id)
        
        # 이전 메시지 히스토리 조회
        previous_messages = await get_chat_history(db, room_id, session_id)
        
        # 세션 정보와 이전 메시지 전송
        await manager.broadcast_to_room(
            room_id,
            {
                "type": "session",
                "session_id": session_id,
                "messages": previous_messages
            },
            target_user_id=user_id
        )
        
        # 메시지 수신 루프
        while True:
            try:
                data = await websocket.receive_json()
                await process_message(websocket, data, room_id, user_id, db)
            except WebSocketDisconnect:
                raise  # 상위 예외 처리로 전달
            except Exception as e:
                print(f"[WS_ROUTER_ERROR] Error in message loop: {e}")
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json({
                        "type": "error",
                        "message": "메시지 처리 중 오류가 발생했습니다."
                    })
                
    except WebSocketDisconnect:
        print(f"[WS_ROUTER_DEBUG] User {user_id} disconnected from room {room_id}")
    except Exception as e:
        print(f"[WS_ROUTER_ERROR] Unexpected error: {e}")
    finally:
        print(f"[WS_ROUTER_DEBUG] Cleaning up for user {user_id} in room {room_id} (finally block).")
        await manager.disconnect(room_id, user_id)
        # 방의 마지막 사용자가 나갔을 때 세션 종료
        remaining_users = len(manager.get_active_connections_for_room(room_id))
        print(f"[WS_ROUTER_DEBUG] User {user_id} disconnected. Remaining users in room {room_id}: {remaining_users}")
        if remaining_users == 0:
            print(f"[WS_ROUTER_DEBUG] Last user disconnected from room {room_id}. Attempting to end session via SessionManager.")
            await websocket.app.state.session_manager.end_session_for_room(room_id, db)


async def get_chat_history(db: AsyncSession, room_id: int, session_id: str):
    stmt = select(Log).where(
        Log.room_id == room_id,
        Log.session_id == session_id
    ).order_by(Log.created_at.desc())

    result = await db.execute(stmt)
    messages = result.scalars().all()

    return [
        {
            "type": "message",
            "content": msg.content,
            "speaker": msg.speaker,
            "timestamp": msg.timestamp.isoformat()
        }
        for msg in messages
    ]

async def validate_session(db: AsyncSession, room_id: int, session_id: str):
    stmt = select(SessionModel).where(
        SessionModel.id == session_id,
        SessionModel.room_id == room_id,
        SessionModel.is_active == True
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_new_session(
    db: AsyncSession,
    room_id: int,
    user_id: int,
    topic: str = "topic_1_situation"
) -> SessionModel:
    # ① 커플 조회: user_id가 포함된 커플 1건 가져오기
    result = await db.execute(
        select(Couple).where(
            or_(
                Couple.user_a_id == user_id,
                Couple.user_b_id == user_id
            )
        )
    )
    couple = result.scalar_one_or_none()
    if not couple:
        raise ValueError(f"No couple found for user_id {user_id}")

    # ② 커플의 양쪽 ID 설정
    user_a_id = couple.user_a_id
    user_b_id = couple.user_b_id

    # ③ 세션 생성
    new_session = SessionModel(
        room_id=room_id,
        user_a_id=user_a_id,
        user_b_id=user_b_id,
        topic=topic,
        is_active=True,
        extension_used=False
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session



# ... rest of the code ... 