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
from app.utils.logger import get_logger
from app.utils.exceptions import AuthenticationError, NotFoundError, WebSocketError, DatabaseError
# from openai import AsyncOpenAI # EmotionService가 직접 AsyncOpenAI를 임포트하므로 여기서 필요X

logger = get_logger("websocket_router")
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
    # redis_client = websocket.app.state.redis # <--- 주석 처리
    # if not redis_client: # <--- 이 조건 블록 전체 주석 처리
    #     logger.error("Redis client not available in app.state. Cannot initialize EmotionService.")
    #     await websocket.close(code=1011, reason="Internal server error: Redis not configured")
    #     return

    # GPTService에서 OpenAI 클라이언트 가져오기
    gpt_service = websocket.app.state.gpt_service
    openai_client = gpt_service.client if gpt_service else None

    # EmotionService 초기화 시 OpenAI 클라이언트 주입
    emotion_service = EmotionService(openai_client=openai_client)

    try:
        logger.info(f"WebSocket connection attempt for room {room_id}")
        
        # 토큰 검증
        try:
            payload = await verify_token(token)
            user_id = str(payload.get("memberId"))
            if not user_id:
                logger.warning("Invalid token: missing memberId")
                await websocket.close(code=1008)
                return
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            await websocket.close(code=1008)
            return

        # WebSocket 연결
        await current_connection_manager.connect(websocket, room_id, user_id)
        logger.info(f"User {user_id} connected to room {room_id}")
        
        # 방 존재 확인
        room = await db.get(Room, room_id)
        if not room:
            logger.warning(f"Room {room_id} not found")
            await websocket.send_json({"type": "error", "content": "Room not found"})
            await current_connection_manager.disconnect(room_id, user_id)
            return

        # 세션 히스토리 로드
        try:
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
                    elif log_entry.role == RoleType.ASSISTANT:
                        message["user_id"] = "AI"
                    else:
                        message["user_id"] = str(log_entry.speaker.value) if log_entry.speaker else log_entry.role.value

                    history_messages.append(message)

            if history_messages:
                await websocket.send_json({"type": "chat_history", "messages": history_messages})
                logger.info(f"Sent {len(history_messages)} history messages to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to load chat history: {e}", exc_info=True)

        # 세션 시작 확인
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
                    logger.info(f"Started new session {session.session_id} for room {room_id}")
                except Exception as e:
                    logger.error(f"Failed to start new session: {e}", exc_info=True)

        # 메시지 처리 루프
        while True:
            try:
                data = await websocket.receive_json()
                msg_type = data.get("type")

                logger.debug(f"Received message type '{msg_type}' from user {user_id} in room {room_id}")

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
                    logger.info(f"User {user_id} responded with: {is_yes}")
                    continue

                if msg_type == "message" and current_active_session:
                    speaker = SpeakerType.A if user_id == str(current_active_session.user_a_id) else SpeakerType.B
                    content = data.get("content", "")
                    if not content.strip():
                        logger.debug("Empty message received, skipping")
                        continue

                    logger.info(f"Processing message from user {user_id}: '{content[:50]}...'")

                    # 사용자 메시지 DB 저장 및 브로드캐스트 (기존 로직)
                    try:
                        chat_log = ChatLog(
                            room_id=room_id,
                            session_id=current_active_session.session_id,
                            role=RoleType.USER,
                            speaker=speaker,
                            content=content,
                            timestamp=datetime.utcnow()
                        )
                        db.add(chat_log)
                        await db.commit() # 사용자 메시지 먼저 저장
                        logger.debug(f"Saved user message to database: log_id={chat_log.log_id}")
                    except Exception as e:
                        logger.error(f"Failed to save user message to database: {e}", exc_info=True)
                        await db.rollback()

                    await current_connection_manager.broadcast_to_room(room_id, {
                        "type": "message",
                        "user_id": user_id, # 실제 사용자 ID
                        "content": content,
                        "timestamp": chat_log.timestamp.isoformat(),
                        "session_id": current_active_session.session_id,
                        "role": RoleType.USER.value
                    })

                    # 감정 키워드 감지 및 GPT 응답 처리 (상황 대화 시)
                    gpt_response_content = None
                    if current_active_session: # 현재 활성 세션이 있을 때만 GPT 호출 로직 고려
                        try:
                            gpt_response_content = await emotion_service.handle_emotion_message(
                                room_id=room_id,
                                user_id=user_id, 
                                message=content,
                                session_topic=current_active_session.topic  # 현재 세션의 토픽 전달
                            )
                        except Exception as e:
                            logger.error(f"Failed to handle emotion message: {e}", exc_info=True)

                    # 비속어 감지 및 중재 메시지 처리 (감정 대화 시)
                    mediation_response_content = None
                    if current_active_session and current_active_session.topic == "topic_2_emotion":
                        try:
                            mediation_response_content = await emotion_service.handle_mediation_message(
                                room_id=room_id,
                                user_id=user_id,
                                message=content,
                                session_topic=current_active_session.topic
                            )
                        except Exception as e:
                            logger.error(f"Failed to handle mediation message: {e}", exc_info=True)

                    # GPT 응답 처리 (감정 키워드 감지 시)
                    if gpt_response_content:
                        # GPT 응답을 AI 메시지로 DB에 저장 (선택적이지만 권장)
                        try:
                            ai_chat_log = ChatLog(
                                room_id=room_id,
                                session_id=current_active_session.session_id,
                                role=RoleType.ASSISTANT.value,  # RoleType.AI 대신 RoleType.ASSISTANT 사용
                                speaker=SpeakerType.AI,       # SpeakerType.AI 로 스피커 명시
                                content=gpt_response_content,
                                timestamp=datetime.utcnow()
                            )
                            db.add(ai_chat_log)
                            await db.commit() # AI 메시지 저장
                            logger.debug(f"Saved AI response to database: log_id={ai_chat_log.log_id}")
                        except Exception as e:
                            logger.error(f"Failed to save AI response to database: {e}", exc_info=True)
                            await db.rollback()

                        # GPT 응답을 방 전체에 브로드캐스트
                        await current_connection_manager.broadcast_to_room(room_id, {
                            "type": "message", # 사용자 메시지와 동일한 타입 사용
                            "user_id": "AI",  # AI가 보낸 메시지임을 명시 (또는 SpeakerType.AI.value)
                            "content": gpt_response_content,
                            "timestamp": ai_chat_log.timestamp.isoformat(), # 저장된 시간 사용
                            "session_id": current_active_session.session_id,
                            "role": RoleType.ASSISTANT.value  # RoleType.AI 대신 RoleType.ASSISTANT 사용
                        })
                        logger.info(f"AI message broadcasted to room {room_id}: '{gpt_response_content[:50]}...'")

                    # 중재 메시지 처리 (비속어 감지 시)
                    if mediation_response_content:
                        # 중재 메시지를 AI 메시지로 DB에 저장
                        try:
                            mediation_chat_log = ChatLog(
                                room_id=room_id,
                                session_id=current_active_session.session_id,
                                role=RoleType.ASSISTANT.value,
                                speaker=SpeakerType.AI,
                                content=mediation_response_content,
                                timestamp=datetime.utcnow()
                            )
                            db.add(mediation_chat_log)
                            await db.commit() # 중재 메시지 저장
                            logger.debug(f"Saved mediation message to database: log_id={mediation_chat_log.log_id}")
                        except Exception as e:
                            logger.error(f"Failed to save mediation message to database: {e}", exc_info=True)
                            await db.rollback()

                        # 중재 메시지를 방 전체에 브로드캐스트
                        await current_connection_manager.broadcast_to_room(room_id, {
                            "type": "message",
                            "user_id": "AI_Mediation",  # 중재 메시지임을 명시
                            "content": mediation_response_content,
                            "timestamp": mediation_chat_log.timestamp.isoformat(),
                            "session_id": current_active_session.session_id,
                            "role": RoleType.ASSISTANT.value
                        })
                        logger.info(f"Mediation message broadcasted to room {room_id}: '{mediation_response_content[:50]}...'")

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user_id} in room {room_id}")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                try:
                    await websocket.send_json({"type": "error", "content": "Message processing failed"})
                except:
                    logger.error("Failed to send error message to client")
                    break
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}", exc_info=True)
    finally:
        # 연결 정리
        try:
            await current_connection_manager.disconnect(room_id, user_id)
            logger.info(f"User {user_id} disconnected from room {room_id}")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}", exc_info=True)
