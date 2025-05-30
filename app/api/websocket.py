from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..models import models
from .sessions import manager

router = APIRouter()

# Log 저장을 위한 함수 (공통 사용)
async def save_log_message(
    db: AsyncSession,
    room_id: int,
    session_id: int,
    role: str,
    content: str,
    speaker: Optional[str] = None,
    emotion_flagged: bool = False,
    detected_emotions: Optional[str] = None
):
    log_entry = models.Log(
        room_id=room_id,
        session_id=session_id,
        role=role,
        speaker=speaker,
        content=content,
        timestamp=datetime.utcnow(),
        emotion_flagged=emotion_flagged,
        detected_emotions=detected_emotions
    )
    await db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    return log_entry

@router.websocket("/chat/{room_id}/{user_id}")
async def chat_websocket(
    websocket: WebSocket,
    room_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    # 사용자 및 채팅방 존재 확인
    user_result = await db.execute(
        select(models.User).filter(models.User.user_id == user_id)
    )
    user = user_result.scalars().first()
    room_result = await db.execute(
        select(models.Room).filter(models.Room.room_id == room_id)
    )
    room = room_result.scalars().first()
    
    if not user or not room:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, room_id, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            current_session_id = data.get("session_id")

            # --- 1) ping/pong 처리 (content 없음) ---
            if message_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            # --- 세션 조회 (initiate_session 만 예외적으로 세션 없이 허용) ---
            db_session = None
            if current_session_id:
                session_result = await db.execute(
                    select(models.Session).filter(
                        models.Session.session_id == current_session_id,
                        models.Session.room_id == room_id
                    )
                )
                db_session = session_result.scalars().first()

            if not db_session and message_type != "initiate_session":
                await websocket.send_json({
                    "type": "error",
                    "message": "유효하지 않거나 활성화되지 않은 세션입니다."
                })
                continue

            # --- 2) 일반 메시지 처리 ---
            if message_type == "message":
                if not db_session or not db_session.is_active:
                    await websocket.send_json({
                        "type": "error",
                        "message": "현재 메시지를 보낼 수 있는 활성 세션이 없습니다."
                    })
                    continue

                # content 방어적 꺼내기
                content = data.get("content", "")
                if not content.strip():
                    print(f"[WS_ROUTER_WARNING] Empty or missing content from user {user_id}")
                    continue

                # DB 저장
                await save_log_message(
                    db, room_id, current_session_id, "user", content, speaker=str(user_id)
                )
                # 브로드캐스트
                await manager.broadcast(room_id, {
                    "type": "message",
                    "session_id": current_session_id,
                    "user_id": user_id,
                    "username": user.username,
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat()
                })

            # --- 3) 세션 연장/응답 처리 ---
            elif message_type == "session_action":
                action_value = data.get("action_value")
                if not db_session or not action_value:
                    continue

                await manager.record_user_response(
                    current_session_id, user_id, action_value, db, room_id
                )

                users = {db_session.user_a_id, db_session.user_b_id}
                if len(manager.user_responses.get(current_session_id, {})) < len(users):
                    # 한 명만 응답했을 때
                    await manager.send_personal_message(room_id, user_id, {
                        "type": "system_message",
                        "session_id": current_session_id,
                        "content": "다른 사용자가 선택 중입니다..잠시만 기다려주세요"
                    })
                    await save_log_message(
                        db, room_id, current_session_id, "system",
                        "다른 사용자가 선택 중입니다..잠시만 기다려주세요",
                        speaker="AI"
                    )
                    continue

                # 두 명 모두 응답 완료
                resp = manager.user_responses[current_session_id]
                a_resp = resp.get(db_session.user_a_id)
                b_resp = resp.get(db_session.user_b_id)

                perform_ext = (a_resp == "extend_yes" or b_resp == "extend_yes")
                both_yes = (a_resp == "extend_yes" and b_resp == "extend_yes")

                if both_yes:
                    content = f"{'상황' if db_session.topic=='topic_1_situation' else '감정'}에 대한 대화를 1분 연장하겠습니다. 더 깊이 있는 대화를 나누어보세요."
                elif perform_ext:
                    content = f"{'상황' if db_session.topic=='topic_1_situation' else '감정'}에 대한 대화를 1분 연장하겠습니다. 한 분이 더 많은 시간이 필요하다고 하셨습니다."
                else:
                    if db_session.topic == "topic_1_situation":
                        content = "이제 감정에 대한 대화를 시작하겠습니다."
                    else:
                        content = "채팅을 종료합니다. 진솔한 대화에 감사드립니다."

                # 시스템 메시지 브로드캐스트 & 저장
                await manager.broadcast(room_id, {
                    "type": "system_message",
                    "session_id": current_session_id,
                    "content": content
                })
                await save_log_message(db, room_id, current_session_id, "system", content, speaker="AI")

                # 실제 동작
                if both_yes or perform_ext:
                    db_session.extension_used = True
                    await db.commit()
                    await db.refresh(db_session)
                    manager.start_session_timer(current_session_id, db, duration_minutes=1)
                elif db_session.topic == "topic_1_situation":
                    await manager.initiate_emotion_chat(db_session, db, content)
                else:
                    await manager.end_current_session_in_db(db_session, db)

                manager.user_responses.pop(current_session_id, None)

            # --- 4) 세션 신규 시작 ---
            elif message_type == "initiate_session":
                topic_to_start = data.get("topic", "topic_1_situation")
                existing = await db.execute(
                    select(models.Session)
                    .filter(models.Session.room_id == room_id, models.Session.is_active == True)
                )
                if existing.scalars().first():
                    await websocket.send_json({
                        "type": "error",
                        "message": "이미 진행 중인 세션이 있습니다."
                    })
                    continue

                # 간단하게 방에 접속한 두 유저를 A/B로 배정
                users = list(manager.active_connections.get(room_id, {}).keys())
                u_a = users[0] if len(users) > 0 else user_id
                u_b = users[1] if len(users) > 1 else user_id + 1
                if u_a == u_b:
                    u_b += 1

                new_s = models.Session(
                    room_id=room_id,
                    user_a_id=u_a,
                    user_b_id=u_b,
                    topic=topic_to_start,
                    extension_used=False,
                    is_active=True
                )
                db.add(new_s)
                await db.commit()
                await db.refresh(new_s)

                initial_msg = "상황에 대한 대화를 시작하겠습니다. 어떤 상황에 대해 이야기하고 싶으신가요?"
                await manager.broadcast(room_id, {
                    "type": "session_start",
                    "session_id": new_s.session_id,
                    "topic": new_s.topic,
                    "message": initial_msg
                })
                await save_log_message(db, room_id, new_s.session_id, "system", initial_msg, speaker="AI")
                manager.start_session_timer(new_s.session_id, db, duration_minutes=1)

    except WebSocketDisconnect:
        # 연결 끊김 처리
        await manager.disconnect(room_id, user_id)
        # 마지막 사용자 나가면 세션 종료
        if room_id in manager.active_connections and not manager.active_connections[room_id]:
            await manager.end_current_session_in_db(
                await db.execute(
                    select(models.Session)
                    .filter(models.Session.room_id == room_id, models.Session.is_active == True)
                ).scalars().first(),
                db
            )
        else:
            # 나간 사용자 외 나머지에게 알림
            await manager.broadcast(room_id, {
                "type": "user_disconnect",
                "user_id": user_id,
                "username": user.username,
                "message": f"{user.username}님이 채팅방을 나갔습니다"
            })
