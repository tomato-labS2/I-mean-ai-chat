from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Set, Optional
import json
from datetime import datetime

from ..database import get_db
from ..models import models
from ..models.schemas import LogCreate
from .sessions import manager

router = APIRouter()

# Log 저장을 위한 함수 (공통 사용)
async def save_log_message(db: AsyncSession, room_id: int, session_id: int, role: str, content: str, speaker: Optional[str] = None, emotion_flagged: bool = False, detected_emotions: Optional[str] = None):
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
    user_result = await db.execute(select(models.User).filter(models.User.user_id == user_id))
    user = user_result.scalars().first()
    room_result = await db.execute(select(models.Room).filter(models.Room.room_id == room_id))
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

            # 현재 세션 정보 조회 (공통적으로 필요할 수 있음)
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

            if message_type == "message":
                if not db_session or not db_session.is_active:
                    await websocket.send_json({
                        "type": "error",
                        "message": "현재 메시지를 보낼 수 있는 활성 세션이 없습니다."
                    })
                    continue
                
                content = data["content"]
                # 사용자 메시지 Log 저장
                await save_log_message(db, room_id, current_session_id, "user", content, speaker=str(user_id))
                
                # 메시지 브로드캐스트
                await manager.broadcast(room_id, {
                    "type": "message",
                    "session_id": current_session_id,
                    "user_id": user_id,
                    "username": user.username,
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "session_action":
                action_value = data.get("action_value")
                if not db_session or not action_value:
                    continue

                # 1. 사용자 응답 기록
                await manager.record_user_response(current_session_id, user_id, action_value, db, room_id)

                num_total_users = 2
                session_users = {db_session.user_a_id, db_session.user_b_id}

                if len(manager.user_responses.get(current_session_id, {})) < len(session_users):
                    await manager.send_personal_message(room_id, user_id, {
                        "type": "system_message",
                        "session_id": current_session_id,
                        "content": "다른 사용자가 선택 중입니다..잠시만 기다려주세요"
                    })
                    await save_log_message(db, room_id, current_session_id, "system", "다른 사용자가 선택 중입니다..잠시만 기다려주세요", speaker="AI")
                    continue
                
                responses = manager.user_responses.get(current_session_id, {})
                user_a_response = responses.get(db_session.user_a_id)
                user_b_response = responses.get(db_session.user_b_id)

                system_message_content = ""
                perform_extension = False
                move_to_emotion_chat = False
                end_chat_entirely = False

                current_topic_str = "상황" if db_session.topic == "topic_1_situation" else "감정"

                if user_a_response == "extend_yes" and user_b_response == "extend_yes":
                    perform_extension = True
                    if db_session.topic == "topic_1_situation":
                        system_message_content = "상황에 대한 대화를 1분 연장하겠습니다. 연장된 시간 동안 더 깊이 있는 대화를 나누어보세요. 서로의 입장을 이해하는 것에 집중해주시기 바랍니다."
                    else:
                        system_message_content = "감정에 대한 대화를 1분 연장하겠습니다. 서로의 감정을 더 깊이 이해할 수 있는 소중한 시간입니다. 마음을 열고 진솔한 대화를 계속해주세요."
                
                elif (user_a_response == "extend_yes" and user_b_response == "extend_no") or \
                     (user_a_response == "extend_no" and user_b_response == "extend_yes"):
                    perform_extension = True
                    if db_session.topic == "topic_1_situation":
                        system_message_content = "상황에 대한 대화를 1분 연장하겠습니다. 한 분이 더 많은 시간이 필요하다고 하셨습니다. 연장된 시간 동안 서로의 마음을 충분히 나누어주세요."
                    else:
                        system_message_content = "감정에 대한 대화를 1분 연장하겠습니다. 한 분이 감정을 더 나누고 싶어하십니다. 서로의 마음을 충분히 표현하고 이해하는 시간을 가져보세요."

                elif user_a_response == "extend_no" and user_b_response == "extend_no":
                    if db_session.topic == "topic_1_situation":
                        move_to_emotion_chat = True
                        system_message_content = "이제 감정에 대한 대화를 시작하겠습니다. 앞서 나눈 상황에 대해 각자 어떤 감정을 느꼈는지 솔직하게 표현해주세요. 상대방의 감정도 공감하며 들어주시기 바랍니다."
                    else:
                        end_chat_entirely = True
                        system_message_content = "채팅을 종료합니다. 오늘 상황과 감정에 대해 진솔한 대화를 나누어주셔서 감사합니다. 서로를 더 잘 이해하게 되셨기를 바랍니다. 앞으로도 이런 소통을 계속해나가시길 응원합니다."
                
                if system_message_content:
                    await manager.broadcast(room_id, {
                        "type": "system_message",
                        "session_id": current_session_id,
                        "content": system_message_content
                    })
                    await save_log_message(db, room_id, current_session_id, "system", system_message_content, speaker="AI")

                if perform_extension:
                    db_session.extension_used = True
                    await db.commit()
                    await db.refresh(db_session)
                    manager.start_session_timer(current_session_id, db, duration_minutes=1)
                
                elif move_to_emotion_chat:
                    await manager.initiate_emotion_chat(db_session, db, system_message_content)
                
                elif end_chat_entirely:
                    await manager.end_current_session_in_db(db_session, db)

                manager.user_responses.pop(current_session_id, None)
            
            elif message_type == "initiate_session":
                topic_to_start = data.get("topic", "topic_1_situation")
                active_session_result = await db.execute(
                    select(models.Session).filter(models.Session.room_id == room_id, models.Session.is_active == True)
                )
                existing_active_session = active_session_result.scalars().first()

                if existing_active_session:
                    await websocket.send_json({
                        "type": "error",
                        "message": "이미 진행 중인 세션이 있습니다."
                    })
                else:
                    users_in_room_for_session = list(manager.active_connections.get(room_id, {}).keys())
                    if len(users_in_room_for_session) < 2 and (not hasattr(room, 'temp_user_a_id') or not hasattr(room, 'temp_user_b_id')):
                        await websocket.send_json({
                            "type": "error",
                            "message": "세션 시작을 위한 사용자 정보를 찾을 수 없습니다."
                        })
                        continue
                    
                    couple_users = list(manager.active_connections[room_id].keys())
                    u_a_id = couple_users[0] if len(couple_users) > 0 else user_id
                    u_b_id = couple_users[1] if len(couple_users) > 1 else user_id + 1
                    if u_a_id == u_b_id: u_b_id = u_a_id - 1
                    if u_a_id <= 0: u_a_id = user_id
                    if u_b_id <= 0: u_b_id = user_id + 1 if user_id != 1 else user_id + 2
                    if u_a_id == u_b_id:
                        await websocket.send_json({
                            "type": "error",
                            "message": "세션 사용자 ID 설정 오류"
                        })
                        continue

                    new_db_session = models.Session(
                        room_id=room_id,
                        user_a_id=u_a_id,
                        user_b_id=u_b_id,
                        topic=topic_to_start,
                        extension_used=False,
                        is_active=True
                    )
                    db.add(new_db_session)
                    await db.commit()
                    await db.refresh(new_db_session)

                    initial_message_content = ""
                    if topic_to_start == "topic_1_situation":
                        initial_message_content = "상황에 대한 대화를 시작하겠습니다. 어떤 상황에 대해 이야기하고 싶으신가요? 편하게 말씀해주세요."

                    await manager.broadcast(room_id, {
                        "type": "session_start",
                        "session_id": new_db_session.session_id,
                        "topic": new_db_session.topic,
                        "message": initial_message_content
                    })
                    await save_log_message(db, room_id, new_db_session.session_id, "system", initial_message_content, speaker="AI")
                    manager.start_session_timer(new_db_session.session_id, db, duration_minutes=1)
    
    except WebSocketDisconnect:
        manager.disconnect(room_id, user_id)
        if room_id in manager.active_connections and not manager.active_connections[room_id]:
            active_session_result = await db.execute(
                select(models.Session).filter(models.Session.room_id == room_id, models.Session.is_active == True)
            )
            active_session_to_close = active_session_result.scalars().first()
            if active_session_to_close:
                await manager.end_current_session_in_db(active_session_to_close, db)
                if active_session_to_close.session_id in manager.session_timers:
                    manager.session_timers[active_session_to_close.session_id].cancel()
                    manager.session_timers.pop(active_session_to_close.session_id, None)
        else:
            await manager.broadcast(room_id, {
                "type": "user_disconnect",
                "user_id": user_id,
                "username": user.username,
                "message": f"{user.username}님이 채팅방을 나갔습니다"
            })
    finally:
        pass