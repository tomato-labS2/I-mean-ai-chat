
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
from datetime import datetime
import traceback
import logging
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from ..database import get_db
from ..models.chat import Room, Session, ChatLog, SpeakerType, RoleType
from ..security import verify_token
from app.services.emotion_service import EmotionService

router = APIRouter()

@router.websocket("/api/sessions/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    room_id: int, 
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    current_connection_manager = websocket.app.state.connection_manager
    current_session_manager = websocket.app.state.session_manager
    redis_client = websocket.app.state.redis
    emotion_service = EmotionService(redis_client)

    try:
        payload = await verify_token(token)
        user_id = str(payload.get("memberId"))
        if not user_id:
            await websocket.close(code=1008)
            return

        await current_connection_manager.connect(websocket, room_id, user_id)
        room = await db.get(Room, room_id)
        if not room:
            await websocket.send_json({"type": "error", "content": "Room not found"})
            await current_connection_manager.disconnect(room_id, user_id)
            return

        sessions_in_room_stmt = select(Session).where(Session.room_id == room_id)
        sessions_result = await db.execute(sessions_in_room_stmt)
        sessions_in_room_list = sessions_result.scalars().all()

        history_messages = []
        if sessions_in_room_list:
            session_id_to_user_map = {
                s.session_id: {"user_a_id": str(s.user_a_id), "user_b_id": str(s.user_b_id)}
                for s in sessions_in_room_list
            }
            all_session_ids_in_room = [s.session_id for s in sessions_in_room_list]

            chat_logs_stmt = (
                select(ChatLog)
                .where(ChatLog.session_id.in_(all_session_ids_in_room))
                .order_by(ChatLog.timestamp.asc())
            )
            logs_result = await db.execute(chat_logs_stmt)
            previous_logs = logs_result.scalars().all()

            for log_entry in previous_logs:
                message = {
                    "type": "message", 
                    "content": log_entry.content,
                    "timestamp": log_entry.timestamp.isoformat(),
                    "session_id": log_entry.session_id,
                    "role": log_entry.role.value,
                }
                session_users = session_id_to_user_map.get(log_entry.session_id)
                if log_entry.role == RoleType.USER and session_users:
                    message["user_id"] = session_users["user_a_id"] if log_entry.speaker == SpeakerType.A else session_users["user_b_id"]
                elif log_entry.role == RoleType.AI:
                    message["user_id"] = "AI"
                else:
                    message["user_id"] = str(log_entry.speaker.value) if log_entry.speaker else log_entry.role.value

                history_messages.append(message)

        if history_messages:
            await websocket.send_json({"type": "chat_history", "messages": history_messages})

        active_connections = current_connection_manager.get_active_connections_for_room(room_id)
        if len(active_connections) == 2:
            current_active_session = await current_session_manager.get_current_session(room_id)
            if not current_active_session:
                users = list(active_connections.keys())
                try:
                    session = await current_session_manager.start_new_initial_session(
                        room_id, int(users[0]), int(users[1]), db
                    )
                    current_active_session = session
                except Exception as e:
                    traceback.print_exc()

        while True:
            try:
                data = await websocket.receive_json()
                msg_type = data.get("type")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                if msg_type == "typing":
                    await current_connection_manager.broadcast_to_room(room_id, {
                        "type": "typing",
                        "user_id": user_id,
                        "is_typing": data.get("is_typing", True)
                    })
                    continue

                current_active_session = await current_session_manager.get_current_session(room_id)

                if msg_type == "response" and current_active_session:
                    is_yes = (data.get("content") == "네")
                    await current_session_manager.add_session_response(room_id, user_id, is_yes, db)
                    continue

                if msg_type == "message" and current_active_session:
                    speaker = SpeakerType.A if user_id == str(current_active_session.user_a_id) else SpeakerType.B
                    content = data.get("content", "")
                    if not content.strip():
                        continue

                    # 감정 키워드 감지
                    detected = await emotion_service.handle_emotion_message(
                        room_id=room_id,
                        user_id=user_id,
                        message=content
                    )
                    if detected:
                        await websocket.send_json({
                            "type": "notice",
                            "content": f"⚠ 감정 키워드('{detected}')가 감지되었습니다. 감정보다는 상황에 집중해주세요."
                        })

                    chat_log = ChatLog(
                        room_id=room_id,
                        session_id=current_active_session.session_id,
                        role=RoleType.USER,
                        speaker=speaker,
                        content=content,
                        timestamp=datetime.utcnow()
                    )
                    db.add(chat_log)
                    await db.commit()

                    await current_connection_manager.broadcast_to_room(room_id, {
                        "type": "message",
                        "user_id": user_id,
                        "content": content,
                        "timestamp": chat_log.timestamp.isoformat(),
                        "session_id": current_active_session.session_id,
                        "role": RoleType.USER.value
                    })

            except WebSocketDisconnect:
                break
            except Exception as e:
                traceback.print_exc()
                try:
                    await websocket.send_json({"type": "error", "content": "Message processing failed"})
                except:
                    break

    except Exception as e:
        traceback.print_exc()
        if websocket.client_state == websocket.client_state.CONNECTED:
            try:
                await websocket.close(code=1011, reason="Internal server error")
            except:
                pass

    finally:
        try:
            await current_connection_manager.disconnect(room_id, user_id)
            remaining = len(current_connection_manager.get_active_connections_for_room(room_id))
            if remaining == 0:
                session = await current_session_manager.get_current_session(room_id)
                if session:
                    await current_session_manager.end_session_for_room(room_id, db)
        except:
            traceback.print_exc()
