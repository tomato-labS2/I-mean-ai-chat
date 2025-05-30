from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # select 추가
import json
import asyncio
from datetime import datetime
import traceback

from ..database import get_db
from ..models.chat import Room, Session, ChatLog, SpeakerType, RoleType # User 모델은 여기서 직접 사용 안함
from ..security import verify_token
# SessionManager와 ConnectionManager 클래스 자체는 이 파일에서 직접 인스턴스화하지 않으므로 import 불필요
# from ..session import SessionManager 
# from ..connection_manager import ConnectionManager

router = APIRouter()

# 전역 인스턴스들을 이 라우터 파일 내에서 직접 참조하거나,
# main.py에서 생성된 인스턴스를 Depends 등으로 주입받는 방식을 고려할 수 있습니다.
# 여기서는 main.py에서 생성된 인스턴스를 사용한다고 가정하고, main.py에서 라우터를 초기화할 때 전달하거나,
# 또는 main.py의 인스턴스를 직접 import하여 사용합니다.
# 이 예제에서는 후자를 선택하여 main.py에서 생성된 connection_manager와 session_manager를 가져옵니다.
# 하지만 이는 순환 참조의 위험이 있어, 더 큰 애플리케이션에서는 의존성 주입 패턴이 권장됩니다.
# 지금은 main.py에서 이 라우터를 import하므로, main.py에서 생성된 manager들을 여기서 import하는 것은 순환참조입니다.
# 따라서 manager 인스턴스들을 websocket_endpoint 함수의 파라미터로 전달받도록 수정하거나,
# FastAPI의 의존성 주입을 통해 제공받도록 하는 것이 좋습니다.

# 임시 해결책: main.py에서 라우터 생성 시 manager들을 전달하는 형태로 변경하거나,
# manager들을 상태 관리용 싱글톤 등으로 관리하는 방법도 있습니다.
# 여기서는 FastAPI의 Depends를 활용하기 위해, main.py에서 생성된 전역 인스턴스를 사용하도록 하고, 필요시 리팩토링합니다.
# 또는, main.py에서 router를 초기화할 때 manager를 넘겨주는 방식도 고려할 수 있습니다.

# 더 간단한 접근 방식: main.py에서 connection_manager와 session_manager를 생성하므로,
# 이 라우터 파일에서는 해당 인스턴스를 직접 import하여 사용합니다.
# main.py에서 이 라우터를 포함시키므로, main.py가 먼저 로드되고 manager 인스턴스들이 생성됩니다.
# from ..main import connection_manager, session_manager # <- 이 방식은 순환참조 위험이 큼.

# 해결책: 의존성 주입을 사용하기 위해 Manager들을 Depends로 가져옵니다.
# 이는 main.py에서 해당 manager들이 app.state에 설정되거나, FastAPI의 고급 의존성 주입 메커니즘을 사용해야 합니다.
# 우선은 main.py에서 생성된 전역 인스턴스를 사용하도록 하고, 필요시 리팩토링합니다.
# from ..main import connection_manager, session_manager # 실제로 이렇게하면 순환참조

# 이 라우터가 main.py의 connection_manager 및 session_manager 인스턴스를 사용할 수 있도록,
# main.py에서 해당 인스턴스를 이 라우터의 함수에 전달하거나, FastAPI의 app.state 등을 활용해야합니다.
# 지금은 main.py에서 생성하고 이 라우터의 함수가 직접 접근한다고 가정하고 진행합니다 (실제로는 수정 필요).

# 가장 현실적인 접근: main.py에서 라우터를 포함할 때, 라우터 객체에 manager를 속성으로 설정하거나,
# 라우터 함수들이 직접 main.py의 manager 변수를 참조하도록 하는 것입니다.
# 여기서는 main.py 에서 생성된 connection_manager 와 session_manager 를 직접 사용한다고 가정하고 코드를 작성합니다.
# (이 부분은 실제 실행 시점에서 main.py의 manager 인스턴스가 이 파일에 어떻게 제공될지에 따라 달라집니다.)

@router.websocket("/api/sessions/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    room_id: int, 
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    # 연결 시작 로깅
    client_ip = websocket.client.host if websocket.client else "unknown"
    client_port = websocket.client.port if websocket.client else "unknown"
    print(f"[WS_CONNECTION_START] Room: {room_id}, Client: {client_ip}:{client_port}, Token: {token[:20]}... (WebSocket handshake initiated)")
    
    current_connection_manager = websocket.app.state.connection_manager
    current_session_manager = websocket.app.state.session_manager
    user_id = "unknown"  # 초기값 설정

    try:
        print(f"[WS_TOKEN_VERIFY] Room: {room_id}, Client: {client_ip}:{client_port} - Starting token verification")
        payload = await verify_token(token)
        print(f"[WS_TOKEN_SUCCESS] Room: {room_id}, Client: {client_ip}:{client_port} - Token verified successfully. Payload: {payload}")
        
        user_id = str(payload.get("memberId"))
        if not user_id:
            print(f"[WS_TOKEN_ERROR] Room: {room_id}, Client: {client_ip}:{client_port} - memberId not found in token payload. Full payload: {payload}")
            await websocket.close(code=1008)
            return

        print(f"[WS_USER_IDENTIFIED] Room: {room_id}, User: {user_id}, Client: {client_ip}:{client_port} - User identified from token")
        
        # ConnectionManager 연결 시도
        print(f"[WS_CONNECT_ATTEMPT] Room: {room_id}, User: {user_id}, Client: {client_ip}:{client_port} - Attempting to connect to ConnectionManager")
        await current_connection_manager.connect(websocket, room_id, user_id)
        print(f"[WS_CONNECT_SUCCESS] Room: {room_id}, User: {user_id}, Client: {client_ip}:{client_port} - Successfully connected to ConnectionManager")
        
        # 연결 후 상태 확인
        active_connections = current_connection_manager.get_active_connections_for_room(room_id)
        print(f"[WS_CONNECTION_STATE] Room: {room_id}, User: {user_id} - Active connections after connect: {list(active_connections.keys())}")
        
        room = await db.get(Room, room_id)
        if not room:
            print(f"[WS_ROOM_ERROR] Room: {room_id}, User: {user_id} - Room not found in database")
            await websocket.send_json({"type": "error", "content": "Room not found"})
            await current_connection_manager.disconnect(room_id, user_id)
            return

        print(f"[WS_ROOM_VERIFIED] Room: {room_id}, User: {user_id} - Room exists in database")

        # 현재 활성 세션 정보
        current_active_session = await current_session_manager.get_current_session(room_id) 
        print(f"[WS_SESSION_CHECK] Room: {room_id}, User: {user_id} - Current active session: {current_active_session.session_id if current_active_session else 'None'}")
        
        # 이전 대화 내용 불러오기
        print(f"[WS_HISTORY_LOAD] Room: {room_id}, User: {user_id} - Loading chat history")

        sessions_in_room_stmt = select(Session).where(Session.room_id == room_id)
        sessions_result = await db.execute(sessions_in_room_stmt)
        sessions_in_room_list = sessions_result.scalars().all()

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
            
            history_messages = []
            for log_entry in previous_logs:
                history_message = {
                    "type": "message", 
                    "content": log_entry.content,
                    "timestamp": log_entry.timestamp.isoformat(),
                    "session_id": log_entry.session_id,
                    "role": log_entry.role.value,
                }
                session_users = session_id_to_user_map.get(log_entry.session_id)
                if log_entry.role == RoleType.USER and session_users:
                    history_message["user_id"] = session_users["user_a_id"] if log_entry.speaker == SpeakerType.A else session_users["user_b_id"]
                elif log_entry.role == RoleType.AI:
                     history_message["user_id"] = "AI"
                else: 
                     history_message["user_id"] = str(log_entry.speaker.value) if log_entry.speaker else log_entry.role.value

                history_messages.append(history_message)
            
            if history_messages:
                await websocket.send_json({
                    "type": "chat_history",
                    "messages": history_messages
                })
                print(f"[WS_HISTORY_SENT] Room: {room_id}, User: {user_id} - Sent {len(history_messages)} previous messages from all sessions")
        else:
            print(f"[WS_HISTORY_EMPTY] Room: {room_id}, User: {user_id} - No previous sessions or logs found")

        # 활성 연결 확인 및 세션 생성 로직
        active_connections_in_room = current_connection_manager.get_active_connections_for_room(room_id)
        connected_users_count = len(active_connections_in_room)
        print(f"[WS_CONNECTION_COUNT] Room: {room_id}, User: {user_id} - Connected users: {connected_users_count}, Users: {list(active_connections_in_room.keys())}")
        
        current_active_session = await current_session_manager.get_current_session(room_id)
        print(f"[WS_SESSION_STATUS] Room: {room_id}, User: {user_id} - Active session after connection: {current_active_session.session_id if current_active_session else 'None'}")

        if connected_users_count == 2 and not current_active_session:
            print(f"[WS_SESSION_CREATE] Room: {room_id}, User: {user_id} - Attempting to create new session with users: {list(active_connections_in_room.keys())}")
            connected_user_ids_str = list(active_connections_in_room.keys())
            if len(connected_user_ids_str) == 2:
                try:
                    user_a_id_for_session = int(connected_user_ids_str[0]) 
                    user_b_id_for_session = int(connected_user_ids_str[1])
                    print(f"[WS_SESSION_INIT] Room: {room_id}, User: {user_id} - Creating session with User A: {user_a_id_for_session}, User B: {user_b_id_for_session}")
                    
                    new_started_session = await current_session_manager.start_new_initial_session(room_id, user_a_id_for_session, user_b_id_for_session, db)
                    if new_started_session:
                        print(f"[WS_SESSION_CREATED] Room: {room_id}, User: {user_id} - Session created successfully with ID: {new_started_session.session_id}")
                        current_active_session = new_started_session
                        
                        verify_session = await current_session_manager.get_current_session(room_id)
                        print(f"[WS_SESSION_VERIFY] Room: {room_id}, User: {user_id} - Session verification: {verify_session.session_id if verify_session else 'None'}")
                    else:
                        print(f"[WS_SESSION_FAILED] Room: {room_id}, User: {user_id} - Failed to create session")
                except Exception as e:
                    print(f"[WS_SESSION_ERROR] Room: {room_id}, User: {user_id} - Error creating session: {str(e)}")
                    traceback.print_exc()

        print(f"[WS_READY] Room: {room_id}, User: {user_id}, Client: {client_ip}:{client_port} - WebSocket connection ready, entering message loop")

        try:
            while True:
                # 메시지 수신 대기
                print(f"[WS_WAITING] Room: {room_id}, User: {user_id} - Waiting for message...")
                data = await websocket.receive_text()
                message_data = json.loads(data)
                print(f"[WS_MESSAGE_RECEIVED] Room: {room_id}, User: {user_id} - Message: {message_data}")
                
                # 메시지 처리
                session_for_new_message = await current_session_manager.get_current_session(room_id)
                print(f"[WS_MESSAGE_SESSION] Room: {room_id}, User: {user_id} - Processing with session: {session_for_new_message.session_id if session_for_new_message else 'None'}")

                # ping/pong 처리를 가장 먼저
                if message_data.get("type") == "ping":
                    print(f"[WS_PING_RECEIVED] Room: {room_id}, User: {user_id} - Received ping, sending pong")
                    await websocket.send_json({"type": "pong"})
                    print(f"[WS_PONG_SENT] Room: {room_id}, User: {user_id} - Pong sent successfully")
                    continue

                if message_data.get("type") == "response":
                    if not session_for_new_message:
                        print(f"[WS_RESPONSE_ERROR] Room: {room_id}, User: {user_id} - No active session for response: {message_data}")
                        await websocket.send_json({"type": "error", "content": "No active session to respond to."})
                        continue
                    
                    response_content_str = message_data.get("content")
                    is_yes = response_content_str == "네" if isinstance(response_content_str, str) else False
                    print(f"[WS_RESPONSE_PROCESS] Room: {room_id}, User: {user_id} - Processing response: {response_content_str} (is_yes: {is_yes})")
                    await current_session_manager.add_session_response(room_id, user_id, is_yes, db)
                    continue
                
                if session_for_new_message:
                    speaker_type_for_log = SpeakerType.UNKNOWN
                    print(f"[WS_SPEAKER_DETERMINE] Room: {room_id}, User: {user_id} - Determining speaker (Session User A: {session_for_new_message.user_a_id}, User B: {session_for_new_message.user_b_id})")
                    
                    if user_id == str(session_for_new_message.user_a_id):
                        speaker_type_for_log = SpeakerType.A
                        print(f"[WS_SPEAKER_A] Room: {room_id}, User: {user_id} - Identified as Speaker A")
                    elif user_id == str(session_for_new_message.user_b_id):
                        speaker_type_for_log = SpeakerType.B
                        print(f"[WS_SPEAKER_B] Room: {room_id}, User: {user_id} - Identified as Speaker B")
                    else:
                        print(f"[WS_SPEAKER_UNKNOWN] Room: {room_id}, User: {user_id} - Could not identify speaker")
                    
                    if speaker_type_for_log == SpeakerType.UNKNOWN:
                         print(f"[WS_SPEAKER_WARNING] Room: {room_id}, User: {user_id} - Speaker type unknown for session {session_for_new_message.session_id}")

                    print(f"[WS_LOG_SAVE] Room: {room_id}, User: {user_id} - Saving chat log (Session: {session_for_new_message.session_id}, Speaker: {speaker_type_for_log.value})")
                    chat_log = ChatLog(
                        room_id=room_id,
                        session_id=session_for_new_message.session_id,
                        role=RoleType.USER,
                        speaker=speaker_type_for_log,
                        content=message_data["content"],
                        timestamp=datetime.utcnow()
                    )
                    db.add(chat_log)
                    await db.commit()
                    print(f"[WS_LOG_SAVED] Room: {room_id}, User: {user_id} - Chat log saved successfully")

                    broadcast_message = {
                        "type": "message",
                        "user_id": user_id,
                        "content": message_data["content"],
                        "timestamp": chat_log.timestamp.isoformat(),
                        "session_id": session_for_new_message.session_id,
                        "role": RoleType.USER.value 
                    }
                    print(f"[WS_BROADCAST] Room: {room_id}, User: {user_id} - Broadcasting message to room")
                    await current_connection_manager.broadcast_to_room(room_id, broadcast_message)
                    print(f"[WS_BROADCAST_SENT] Room: {room_id}, User: {user_id} - Message broadcasted successfully")
                else:
                    print(f"[WS_NO_SESSION] Room: {room_id}, User: {user_id} - No active session, broadcasting without logging")
                    broadcast_message = {
                        "type": "message",
                        "user_id": user_id,
                        "content": message_data.get("content"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await current_connection_manager.broadcast_to_room(room_id, broadcast_message)
                
        except WebSocketDisconnect:
            print(f"[WS_DISCONNECT_CLIENT] Room: {room_id}, User: {user_id}, Client: {client_ip}:{client_port} - Client disconnected normally")
        except json.JSONDecodeError as je:
            print(f"[WS_JSON_ERROR] Room: {room_id}, User: {user_id} - Invalid JSON received: {str(je)}")
            await websocket.send_json({"type": "error", "content": "Invalid JSON format."})
        except Exception as e:
            print(f"[WS_MESSAGE_ERROR] Room: {room_id}, User: {user_id} - Error processing message: {str(e)}")
            traceback.print_exc()
        finally:
            print(f"[WS_CLEANUP_START] Room: {room_id}, User: {user_id}, Client: {client_ip}:{client_port} - Starting cleanup process")

            await current_connection_manager.disconnect(room_id, user_id)
            print(f"[WS_DISCONNECTED] Room: {room_id}, User: {user_id} - Disconnected from ConnectionManager")
            
            active_connections_after = current_connection_manager.get_active_connections_for_room(room_id)
            remaining_users_count = len(active_connections_after)
            print(f"[WS_REMAINING_USERS] Room: {room_id}, User: {user_id} - Remaining users: {remaining_users_count}, Users: {list(active_connections_after.keys())}")
            
            if remaining_users_count == 0:
                print(f"[WS_LAST_USER] Room: {room_id}, User: {user_id} - Last user disconnected, ending session")
                session_to_end = await current_session_manager.get_current_session(room_id)
                if session_to_end:
                     print(f"[WS_SESSION_END] Room: {room_id}, User: {user_id} - Ending session {session_to_end.session_id}")
                     await current_session_manager.end_session_for_room(room_id, db)
                     print(f"[WS_SESSION_ENDED] Room: {room_id}, User: {user_id} - Session ended successfully")
                else:
                    print(f"[WS_NO_SESSION_END] Room: {room_id}, User: {user_id} - No active session to end")
            
            print(f"[WS_CLEANUP_COMPLETE] Room: {room_id}, User: {user_id}, Client: {client_ip}:{client_port} - Cleanup completed")
            
    except HTTPException as he:
        print(f"[WS_HTTP_ERROR] Room: {room_id}, User: {user_id}, Client: {client_ip}:{client_port} - HTTPException: {he.detail}")
        if websocket.client_state == websocket.client_state.CONNECTED:
             await websocket.close(code=1011)
             print(f"[WS_CLOSED_HTTP] Room: {room_id}, User: {user_id} - WebSocket closed due to HTTP error")
    except Exception as e_outer:
        print(f"[WS_CRITICAL_ERROR] Room: {room_id}, User: {user_id}, Client: {client_ip}:{client_port} - Critical error: {str(e_outer)}")
        traceback.print_exc()
        if 'websocket' in locals() and websocket.client_state == websocket.client_state.CONNECTED:
            try:
                await websocket.close(code=1011)
                print(f"[WS_CLOSED_CRITICAL] Room: {room_id}, User: {user_id} - WebSocket closed due to critical error")
            except Exception as e_close_on_error:
                print(f"[WS_CLOSE_ERROR] Room: {room_id}, User: {user_id} - Failed to close websocket: {e_close_on_error}")
        
        if 'current_connection_manager' in locals() and room_id and user_id:
            await current_connection_manager.disconnect(room_id, user_id)
            print(f"[WS_FORCE_DISCONNECT] Room: {room_id}, User: {user_id} - Force disconnected after critical error")
    
    print(f"[WS_CONNECTION_END] Room: {room_id}, User: {user_id}, Client: {client_ip}:{client_port} - WebSocket connection completely terminated")