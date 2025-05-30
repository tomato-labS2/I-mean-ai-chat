from fastapi import WebSocket, WebSocketDisconnect, Query
from typing import Optional
from ..database import get_db
from ..models import Log
from sqlalchemy.orm import Session
from sqlalchemy import desc

@router.websocket("/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    user_id: str,
    session_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        print(f"[WS_ROUTER_ENDPOINT] Connecting User {user_id} to room {room_id}")
        
        # 기존 세션 ID가 있는 경우 해당 세션의 유효성 검증
        current_session = None
        if session_id:
            # 세션 유효성 검증 로직
            current_session = validate_session(db, room_id, session_id)
        
        # 유효한 세션이 없으면 새 세션 생성
        if not current_session:
            current_session = create_new_session(db, room_id, user_id)
            session_id = current_session.id
        
        await manager.connect(websocket, room_id, user_id)
        
        # 이전 메시지 히스토리 조회
        previous_messages = get_chat_history(db, room_id, session_id)
        
        # 세션 정보와 이전 메시지 전송
        await manager.broadcast_to_room(
            room_id,
            {
                "type": "session",
                "session_id": session_id,
                "messages": previous_messages
            },
            target_user_id=user_id  # 현재 연결된 사용자에게만 전송
        )
        
        # ... existing message handling code ...
        
    except WebSocketDisconnect:
        await manager.disconnect(room_id, user_id)
        
def get_chat_history(db: Session, room_id: int, session_id: str):
    """해당 세션의 이전 채팅 메시지 조회"""
    messages = db.query(Log).filter(
        Log.room_id == room_id,
        Log.session_id == session_id
    ).order_by(desc(Log.created_at)).all()
    
    return [
        {
            "type": "message",
            "content": msg.content,
            "speaker": msg.speaker,
            "timestamp": msg.timestamp.isoformat()
        }
        for msg in messages
    ]

def validate_session(db: Session, room_id: int, session_id: str):
    """세션 유효성 검증"""
    return db.query(Session).filter(
        Session.id == session_id,
        Session.room_id == room_id,
        Session.is_active == True
    ).first()

# ... rest of the code ... 