from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # select 추가
import json
from datetime import datetime
import traceback
import logging
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

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
    current_connection_manager = websocket.app.state.connection_manager
    current_session_manager = websocket.app.state.session_manager

    try:
        print(f"[WS_ROUTER_DEBUG] Token verification attempt - Room: {room_id}, Token: {token[:20]}...")
        payload = await verify_token(token)
        print(f"[WS_ROUTER_DEBUG] Token payload received: {payload}")
        
        user_id = str(payload.get("memberId"))
        if not user_id:
            print(f"[WS_ROUTER_ERROR] WebSocket connection failed: memberId not found in token payload for room {room_id}. Full payload: {payload}")
            await websocket.close(code=1008)
            return

        print(f"[WS_ROUTER_DEBUG] Token verification successful - Room: {room_id}, User ID: {user_id}")
        
        await current_connection_manager.connect(websocket, room_id, user_id)
        print(f"[WS_ROUTER_DEBUG] Room {room_id} User {user_id} - CM.connect() returned. Users known by CM: {list(current_connection_manager.get_active_connections_for_room(room_id).keys())}")
        
        room = await db.get(Room, room_id)
        if not room:
            await websocket.send_json({"type": "error", "content": "Room not found"})
            print(f"[WS_ROUTER_ERROR] Room {room_id} not found for user {user_id}. Closing WebSocket.")
            await current_connection_manager.disconnect(room_id, user_id) # 연결 후 실패 시 disconnect 추가
            return

        # 현재 활성 세션 정보 (새 메시지 저장 등에 사용)
        current_active_session = await current_session_manager.get_current_session(room_id) 
        
        # --- 이전 대화 내용 불러오기 로직 수정 ---
        print(f"[WS_ROUTER_DEBUG] Room {room_id} User {user_id} - Loading ALL previous chat logs for this room.")

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
                print(f"[WS_ROUTER_DEBUG] Room {room_id} User {user_id} - Sent {len(history_messages)} previous messages from all sessions.")
        else:
            print(f"[WS_ROUTER_DEBUG] Room {room_id} User {user_id} - No previous sessions or logs found for this room.")
        # --- 이전 대화 내용 불러오기 로직 끝 ---

        active_connections_in_room = current_connection_manager.get_active_connections_for_room(room_id)
        connected_users_count = len(active_connections_in_room)
        print(f"[WS_ROUTER_DEBUG] Active connections check - Room: {room_id}, Connected users: {connected_users_count}, Users: {list(active_connections_in_room.keys())}")
        
        # get_current_session을 다시 호출하여 최신 상태를 반영
        current_active_session = await current_session_manager.get_current_session(room_id)
        print(f"[WS_ROUTER_DEBUG] Current session check - Room: {room_id}, Active session: {current_active_session.session_id if current_active_session else 'None'}")

        if connected_users_count == 2 and not current_active_session:
            print(f"[WS_ROUTER_DEBUG] Attempting to create new session - Room: {room_id}, Connected users: {list(active_connections_in_room.keys())}")
            connected_user_ids_str = list(active_connections_in_room.keys())
            if len(connected_user_ids_str) == 2:
                try:
                    user_a_id_for_session = int(connected_user_ids_str[0]) 
                    user_b_id_for_session = int(connected_user_ids_str[1])
                    print(f"[WS_ROUTER_DEBUG] Creating initial session - Room: {room_id}, User A: {user_a_id_for_session}, User B: {user_b_id_for_session}")
                    
                    new_started_session = await current_session_manager.start_new_initial_session(room_id, user_a_id_for_session, user_b_id_for_session, db)
                    if new_started_session:
                        print(f"[WS_ROUTER_DEBUG] Session created successfully - Room: {room_id}, Session ID: {new_started_session.session_id}")
                        current_active_session = new_started_session
                        
                        # 세션 생성 후 상태 확인
                        print(f"[WS_ROUTER_DEBUG] Verifying session state after creation - Room: {room_id}")
                        verify_session = await current_session_manager.get_current_session(room_id)
                        print(f"[WS_ROUTER_DEBUG] Session verification result - Room: {room_id}, Session: {verify_session.session_id if verify_session else 'None'}")
                    else:
                        print(f"[WS_ROUTER_ERROR] Failed to create session - Room: {room_id}")
                except Exception as e:
                    print(f"[WS_ROUTER_ERROR] Error creating session - Room: {room_id}, Error: {str(e)}")
                    traceback.print_exc()
            else:
                print(f"[WS_ROUTER_WARNING] User count mismatch - Room: {room_id}, Expected: 2, Found: {len(connected_user_ids_str)}")


        try:
            while True:
                try:
                    data = await websocket.receive_json()
                    print(f"[WS_ROUTER_ENDPOINT] User {user_id} in room {room_id} RECEIVED: {data}")

                    # 1) ping/pong 메시지 처리 (content 없이도 OK)
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                        continue

                    # 항상 최신 세션 조회
                    session_for_new_message = await current_session_manager.get_current_session(room_id)

                    # 응답 타입 처리
                    if data.get("type") == "response":
                        if not session_for_new_message:
                            await websocket.send_json({"type": "error", "content": "No active session to respond to."})
                            continue
                        resp = data.get("content", "")
                        is_yes = (resp == "네")
                        await current_session_manager.add_session_response(room_id, user_id, is_yes, db)
                        continue

                    # 일반 메시지 처리
                    if session_for_new_message:
                        # speaker 결정
                        if user_id == str(session_for_new_message.user_a_id):
                            speaker = SpeakerType.A
                        elif user_id == str(session_for_new_message.user_b_id):
                            speaker = SpeakerType.B
                        else:
                            speaker = SpeakerType.UNKNOWN

                        # content 안전 추출
                        content = data.get("content", "")
                        if not content.strip():
                            print(f"[WS_ROUTER_WARNING] Empty or missing content from user {user_id}, skip logging")
                            continue

                        # DB에 저장
                        chat_log = ChatLog(
                            room_id=room_id,
                            session_id=session_for_new_message.session_id,
                            role=RoleType.USER,
                            speaker=speaker,
                            content=content,
                            timestamp=datetime.utcnow()
                        )
                        db.add(chat_log)
                        await db.commit()

                        # 브로드캐스트
                        await current_connection_manager.broadcast_to_room(room_id, {
                            "type": "message",
                            "user_id": user_id,
                            "content": content,
                            "timestamp": chat_log.timestamp.isoformat(),
                            "session_id": session_for_new_message.session_id,
                            "role": RoleType.USER.value
                        })

                    else:
                        # 세션 없음(보통 발생하지 않음)
                        content = data.get("content", "")
                        if not content.strip():
                            continue
                        await current_connection_manager.broadcast_to_room(room_id, {
                            "type": "message",
                            "user_id": user_id,
                            "content": content,
                            "timestamp": datetime.utcnow().isoformat()
                        })

                except ConnectionClosedError as cce:
                    print(f"[WS_ROUTER_ERROR] Connection closed unexpectedly - Room: {room_id}, User: {user_id}, Code: {cce.code}, Reason: {cce.reason}")
                    logging.error(f"WebSocket connection closed error: Room {room_id}, User {user_id}, Code: {cce.code}, Reason: {cce.reason}")
                    break

                except ConnectionClosedOK as cco:
                    print(f"[WS_ROUTER_INFO] Connection closed normally - Room: {room_id}, User: {user_id}, Code: {cco.code}, Reason: {cco.reason}")
                    logging.info(f"WebSocket connection closed normally: Room {room_id}, User {user_id}, Code: {cco.code}, Reason: {cco.reason}")
                    break

                except json.JSONDecodeError as jde:
                    print(f"[WS_ROUTER_ERROR] Invalid JSON received - Room: {room_id}, User: {user_id}, Error: {str(jde)}")
                    logging.error(f"JSON decode error in WebSocket: Room {room_id}, User {user_id}, Error: {str(jde)}")
                    try:
                        await websocket.send_json({"type": "error", "content": "Invalid message format"})
                    except Exception:
                        break

                except Exception as msg_error:
                    print(f"[WS_ROUTER_ERROR] Error processing message - Room: {room_id}, User: {user_id}, Error: {str(msg_error)}")
                    logging.error(f"Message processing error: Room {room_id}, User {user_id}, Error: {str(msg_error)}")
                    traceback.print_exc()
                    try:
                        await websocket.send_json({"type": "error", "content": "Message processing failed"})
                    except Exception:
                        break

        except WebSocketDisconnect as wd:
            print(f"[WS_ROUTER_INFO] Client disconnected normally - Room: {room_id}, User: {user_id}, Code: {wd.code}, Reason: {getattr(wd, 'reason', 'No reason provided')}")
            logging.info(f"WebSocket client disconnected: Room {room_id}, User {user_id}, Code: {wd.code}")

    except HTTPException as he:
        print(f"[WS_ROUTER_ERROR] HTTP Exception during WebSocket connection - Room: {room_id}, User: {user_id}, Status: {he.status_code}, Detail: {he.detail}")
        logging.error(f"HTTP Exception in WebSocket: Room {room_id}, User {user_id}, Status: {he.status_code}, Detail: {he.detail}")
        if websocket.client_state == websocket.client_state.CONNECTED:
            try:
                await websocket.close(code=1011, reason="Authentication failed")
            except Exception as close_error:
                print(f"[WS_ROUTER_ERROR] Failed to close WebSocket after HTTP error - Room: {room_id}, User: {user_id}, Error: {str(close_error)}")

    except ConnectionClosedError as cce:
        print(f"[WS_ROUTER_ERROR] Top-level connection error - Room: {room_id}, User: {user_id}, Code: {cce.code}, Reason: {cce.reason}")
        logging.error(f"Top-level WebSocket connection error: Room {room_id}, User {user_id}, Code: {cce.code}, Reason: {cce.reason}")

    except ConnectionClosedOK as cco:
        print(f"[WS_ROUTER_INFO] Top-level connection closed normally - Room: {room_id}, User: {user_id}, Code: {cco.code}, Reason: {cco.reason}")
        logging.info(f"Top-level WebSocket connection closed normally: Room {room_id}, User {user_id}, Code: {cco.code}, Reason: {cco.reason}")

    except Exception as outer:
        print(f"[WS_ROUTER_ERROR] Unexpected top-level error - Room: {room_id}, User: {user_id}, Error: {str(outer)}")
        logging.error(f"Unexpected top-level WebSocket error: Room {room_id}, User {user_id}, Error: {str(outer)}")
        traceback.print_exc()
        # 에러 발생 시 안전하게 종료
        if websocket.client_state == websocket.client_state.CONNECTED:
            try:
                await websocket.close(code=1011, reason="Internal server error")
            except Exception as close_error:
                print(f"[WS_ROUTER_ERROR] Failed to close WebSocket after error - Room: {room_id}, User: {user_id}, Error: {str(close_error)}")
                logging.error(f"Failed to close WebSocket after error: Room {room_id}, User {user_id}, Error: {str(close_error)}")

    finally:
        try:
            # disconnect & 세션 종료 로직
            print(f"[WS_ROUTER_CLEANUP] Starting cleanup for Room: {room_id}, User: {user_id}")
            await current_connection_manager.disconnect(room_id, user_id)
            remaining = len(current_connection_manager.get_active_connections_for_room(room_id))
            print(f"[WS_ROUTER_CLEANUP] Remaining connections in room {room_id}: {remaining}")
            
            if remaining == 0:
                sess = await current_session_manager.get_current_session(room_id)
                if sess:
                    print(f"[WS_ROUTER_CLEANUP] Ending session {sess.session_id} for empty room {room_id}")
                    await current_session_manager.end_session_for_room(room_id, db)
            
            print(f"[WS_ROUTER_CLEANUP] Cleanup completed for Room: {room_id}, User: {user_id}")
            
        except Exception as cleanup_error:
            print(f"[WS_ROUTER_ERROR] Error during cleanup - Room: {room_id}, User: {user_id}, Error: {str(cleanup_error)}")
            logging.error(f"WebSocket cleanup error: Room {room_id}, User {user_id}, Error: {str(cleanup_error)}")
            traceback.print_exc()