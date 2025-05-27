from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query, Body, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .database import get_db, init_db
from .models.chat import Room, Session, ChatLog, SpeakerType, RoleType, User
from datetime import datetime, timedelta
import json
from typing import Dict, Set, Optional
import jwt
from .config import settings
from pydantic import BaseModel
import asyncio
from sqlalchemy import update

app = FastAPI()

# CORS 설정 - FastAPI 사용 시, 클라이언트가 다른 도메인에서 API 요청을 보낼 수 있도록 허용하거나 제한
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 애플리케이션 시작 시 데이터베이스 초기화
@app.on_event("startup")
async def startup_event():
    await init_db()

# 연결된 클라이언트 관리
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}  # 활성 웹소켓 연결 저장 = room_id: {user_id: websocket}
        self.room_sessions: Dict[int, Session] = {}  # 방별 세션 정보 저장 = room_id: session
        self.session_tasks: Dict[int, asyncio.Task] = {}  # 방별 세션 타임아웃 체크 태스크 = room_id: task
        self.session_responses: Dict[int, Dict[str, bool]] = {}  # 방별 사용자 응답 저장 = room_id: {user_id: response}
        self.pending_messages: Dict[int, asyncio.Queue] = {}  # 방별 메시지 큐 = room_id: message queue
        self.message_processing: Dict[int, bool] = {}  # 방별 메시지 처리 상태 = room_id: is_processing

    async def connect(self, websocket: WebSocket, room_id: int, user_id: str):
        await websocket.accept()
        # 해당 방이 없으면 초기화(연결, 메시지 큐, 처리 상태)
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
            self.pending_messages[room_id] = asyncio.Queue()
            self.message_processing[room_id] = False
        self.active_connections[room_id][user_id] = websocket
        print(f"User {user_id} connected to room {room_id}")
        print(f"Current room connections: {self.active_connections[room_id]}")

    def disconnect(self, room_id: int, user_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].pop(user_id, None)
            print(f"User {user_id} disconnected from room {room_id}")  # 디버깅용 로그
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
                if room_id in self.pending_messages:
                    del self.pending_messages[room_id]
                if room_id in self.message_processing:
                    del self.message_processing[room_id]
                # 세션 체크 태스크 종료
                if room_id in self.session_tasks:
                    self.session_tasks[room_id].cancel()
                    del self.session_tasks[room_id]
                print(f"Room {room_id} closed")

    async def broadcast_to_room(self, room_id: int, message: dict, target_user_id: Optional[str] = None):
        if room_id not in self.active_connections:
            print(f"[BROADCAST] Room {room_id} not in active_connections. Cannot send: {message.get('type')}")
            return

        print(f"[BROADCAST] To room {room_id} (target: {target_user_id if target_user_id else 'all'}) - Queuing message type: {message.get('type')}, content: '{message.get('content')}'")
        
        if room_id in self.pending_messages:
            await self.pending_messages[room_id].put({"message_data": message, "target_user_id": target_user_id})
        else:
            print(f"[BROADCAST] Room {room_id} not in pending_messages. Cannot queue: {message.get('type')}")

    async def process_messages(self, room_id: int):
        """메시지 큐를 처리하는 태스크"""
        while True:
            try:
                if room_id not in self.pending_messages or room_id not in self.active_connections:
                    if room_id not in self.pending_messages:
                        print(f"[PROCESS_MSG] Task for room {room_id} stopping - pending_messages queue is gone.")
                    if room_id not in self.active_connections:
                        print(f"[PROCESS_MSG] Task for room {room_id} stopping - active_connections for room is gone.")
                    break
                
                if self.message_processing.get(room_id, False):
                    await asyncio.sleep(0.1)
                    continue
                
                self.message_processing[room_id] = True
                try:
                    queued_item = await self.pending_messages[room_id].get()
                    message_data = queued_item["message_data"]
                    target_user_id = queued_item.get("target_user_id")
                    print(f"[PROCESS_MSG] Room {room_id} - Dequeued message type: {message_data.get('type')} for target: {target_user_id if target_user_id else 'all'}")

                    if room_id in self.active_connections:
                        connections_to_send_to = {}
                        if target_user_id:
                            if target_user_id in self.active_connections[room_id]:
                                connections_to_send_to[target_user_id] = self.active_connections[room_id][target_user_id]
                            else:
                                print(f"[PROCESS_MSG] Room {room_id} - WARNING: Target user {target_user_id} not found for message: {message_data.get('type')}")
                        else:
                            connections_to_send_to = self.active_connections[room_id]
                        
                        active_connection_ids = list(connections_to_send_to.keys())
                        for user_id_to_send in active_connection_ids:
                            connection = connections_to_send_to.get(user_id_to_send)
                            if not connection:
                                print(f"[PROCESS_MSG] Room {room_id} - WARNING: Connection for user {user_id_to_send} disappeared before sending.")
                                continue
                            try:
                                print(f"[PROCESS_MSG] Room {room_id} - Sending to user {user_id_to_send if target_user_id else ('all (' + user_id_to_send + ')')}: {message_data.get('type')}")
                                await connection.send_json(message_data)
                                print(f"[PROCESS_MSG] Room {room_id} - Sent to user {user_id_to_send if target_user_id else ('all (' + user_id_to_send + ')')}: {message_data.get('type')} - SUCCESS")
                            except Exception as e:
                                print(f"[PROCESS_MSG] Room {room_id} - ERROR sending to user {user_id_to_send}: {str(e)}. Message type: {message_data.get('type')}")

                    self.pending_messages[room_id].task_done()
                finally:
                    if room_id in self.message_processing: # 방이 아직 존재하면
                        self.message_processing[room_id] = False
                    
            except asyncio.QueueEmpty: # 큐가 비었을 때의 예외 처리 (get_nowait 사용 시)
                self.message_processing[room_id] = False
                await asyncio.sleep(0.1) # 잠시 대기
            except Exception as e:
                print(f"Error processing messages for room {room_id}: {str(e)}")
                await asyncio.sleep(1)
                if room_id in self.message_processing:
                    self.message_processing[room_id] = False

    async def check_session_timeout(self, room_id: int, db: AsyncSession, target_session_id: int):
        """세션 타임아웃을 체크하고 필요한 경우 메시지를 전송합니다."""
        try:
            print(f"[DEBUG] Starting check_session_timeout for room {room_id}, target session_id {target_session_id}.")
            while True:
                await asyncio.sleep(10)  # 10초마다 체크

                current_session_in_manager = self.room_sessions.get(room_id) # 현재 세션 가져오기

                if not current_session_in_manager: # 세션이 없으면 종료
                    print(f"[DEBUG] No active session in manager for room {room_id} during timeout check for session {target_session_id}. Ending task.")
                    break
                
                if current_session_in_manager.session_id != target_session_id: # 타겟 세션이 아니면 종료
                    print(f"[DEBUG] Active session in manager for room {room_id} is {current_session_in_manager.session_id}, not target {target_session_id}. Ending this task for old session.")
                    break

                # Now, current_session_in_manager is the session we are tracking
                session = current_session_in_manager 

                # 세션 시작 시간이 없으면 종료
                if not session.start_time:
                    print(f"[ERROR] Session {session.session_id} for room {room_id} is missing start_time. Ending timeout check.")
                    break
                
                # start_time부터 경과 시간 계산 (연장 시 start_time이 업데이트됨)
                elapsed_time = datetime.utcnow() - session.start_time
                print(f"[DEBUG] Session {session.session_id} - calculating from start_time: {session.start_time}, elapsed: {elapsed_time}")
                
                # 세션 타임아웃 시간 설정(예 : 1분)
                # 실제 설정에서는 settings.SESSION_DURATION_MINUTES 등을 사용해야 합니다.
                SESSION_TIMEOUT_DURATION = timedelta(minutes=1) 

                if elapsed_time >= SESSION_TIMEOUT_DURATION:
                    print(f"[DEBUG] Session {session.session_id} in room {room_id} has timed out.")
                    
                    # DB에서 최신 세션 정보 가져오기 (extension_used 상태 확인)
                    session_from_db = await db.get(Session, session.session_id)
                    if not session_from_db:
                        print(f"[ERROR] Session {session.session_id} not found in DB. Ending timeout check.")
                        break
                    
                    # extension_used가 true인 경우 자동 전환 처리
                    if session_from_db.extension_used:
                        print(f"[DEBUG] Session {session.session_id} already used extension. Auto-transitioning.")
                        
                        if session_from_db.topic == "topic_1_situation":
                            # 시나리오 6: 상황 채팅 연장 시간 만료 시 (자동 전환)
                            system_message_content = "이제 감정에 대한 대화를 시작하겠습니다. 상황에 대한 충분한 대화를 나누셨습니다. 이제 그 상황에서 느꼈던 감정들을 서로 공유해보는 시간을 가져보겠습니다."
                            
                            # 기존 세션 종료
                            session_from_db.end_time = datetime.utcnow()
                            await db.commit()
                            await db.refresh(session_from_db)
                            self.room_sessions[room_id] = session_from_db
                            print(f"[DEBUG] Session {session_from_db.session_id} ended and saved for room {room_id}.")
                            
                            # 새 감정 세션 생성
                            connected_user_ids = list(self.active_connections[room_id].keys())
                            if len(connected_user_ids) < 2:
                                print(f"[ERROR] Less than 2 users in room {room_id} when trying to start emotion session. Aborting.")
                                break
                            
                            user_a_id_str, user_b_id_str = connected_user_ids[0], connected_user_ids[1]
                            new_session = Session(
                                room_id=room_id,
                                user_a_id=int(user_a_id_str),
                                user_b_id=int(user_b_id_str),
                                topic="topic_2_emotion",
                                start_time=datetime.utcnow()
                            )
                            db.add(new_session)
                            await db.commit()
                            await db.refresh(new_session)
                            self.room_sessions[room_id] = new_session
                            print(f"[INFO] New emotion session {new_session.session_id} started for room {room_id}.")
                            
                            # 새 세션 타임아웃 태스크 시작 -> 기존 타임아웃 태스크 종료
                            if room_id in self.session_tasks:
                                try:
                                    self.session_tasks[room_id].cancel()
                                    await self.session_tasks[room_id]
                                except asyncio.CancelledError:
                                    print(f"[DEBUG] Old session task for room {room_id} cancelled successfully.")
                                except Exception as e_cancel:
                                    print(f"[ERROR] Error cancelling old session task for room {room_id}: {e_cancel}")
                            
                            # 새 세션 타임아웃 태스크 시작
                            self.session_tasks[room_id] = asyncio.create_task(
                                self.check_session_timeout(room_id, db, new_session.session_id)
                            )
                            print(f"[DEBUG] New session timeout task started for session {new_session.session_id} in room {room_id}.")
                            
                            # 사용자에게 알림 메시지 전송
                            session_update_message = {
                                "type": "session",
                                "content": system_message_content,
                                "session_id": new_session.session_id,
                                "topic": new_session.topic,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            await self.broadcast_to_room(room_id, session_update_message)
                            
                        elif session_from_db.topic == "topic_2_emotion":
                            # 시나리오 12: 감정 채팅 연장 시간 만료 시 (채팅 종료)
                            system_message_content = "채팅을 종료합니다. 상황과 감정에 대한 충분한 대화를 나누셨습니다. 서로의 마음을 이해하고 공감하는 뜻깊은 시간이었습니다. 오늘의 대화가 두 분의 관계에 도움이 되기를 바랍니다."
                            
                            # 세션 종료
                            session_from_db.end_time = datetime.utcnow()
                            await db.commit()
                            await db.refresh(session_from_db)
                            print(f"[DEBUG] Final session {session_from_db.session_id} ended for room {room_id}.")
                            
                            # 종료 메시지 전송
                            final_message = {
                                "type": "system",
                                "content": system_message_content,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            await self.broadcast_to_room(room_id, final_message)
                            
                            # 세션 및 타임아웃 태스크 정리
                            if room_id in self.room_sessions:
                                del self.room_sessions[room_id]
                            if room_id in self.session_tasks:
                                try:
                                    self.session_tasks[room_id].cancel()
                                    await self.session_tasks[room_id]
                                except asyncio.CancelledError:
                                    print(f"[DEBUG] Session task for room {room_id} cancelled successfully in auto-termination.")
                                except Exception as e_cancel:
                                    print(f"[ERROR] Error cancelling session task for room {room_id} in auto-termination: {e_cancel}")
                                del self.session_tasks[room_id]
                            print(f"[DEBUG] All session data cleared for room {room_id} in auto-termination.")
                        
                        break  # 자동 전환 처리 완료, 타임아웃 체크 종료
                    
                    else:
                        # extension_used가 false인 경우 연장 질문 표시
                        topic_display = "현재" # 기본값
                        if session_from_db.topic == "topic_1_situation":
                            topic_display = "상황"
                        elif session_from_db.topic == "topic_2_emotion":
                            topic_display = "감정"

                        timeout_message = {
                            "type": "system",
                            "content": f"{topic_display}에 대한 대화 시간이 종료되었습니다. 계속하시겠습니까?",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        await self.broadcast_to_room(room_id, timeout_message)
                        
                        # 이 프롬프트에 대한 새로운 응답을 받기 위해 초기화
                        self.session_responses[room_id] = {} 
                        
                        print(f"[DEBUG] Extension prompt sent for session {session.session_id}. Timeout check task for this session instance is now complete.")
                        break # 현재 세션 인스턴스에 대한 타임아웃 체크 루프 종료
        
        except asyncio.CancelledError:
            print(f"[DEBUG] Session check task for room {room_id}, target session {target_session_id} was cancelled.")
        except Exception as e:
            print(f"[ERROR] Error in session check task for room {room_id}, target session {target_session_id}: {str(e)}")

    async def add_session_response(self, room_id: int, user_id: str, response: bool, db: AsyncSession):
        """사용자의 세션 응답을 저장하고 필요한 경우 새 세션을 시작합니다."""
        if room_id not in self.session_responses:
            self.session_responses[room_id] = {}
        
        self.session_responses[room_id][user_id] = response
        
        current_session_in_manager = self.room_sessions.get(room_id)
        current_topic = "unknown"
        current_manager_session_id = None
        if current_session_in_manager:
            current_topic = current_session_in_manager.topic
            current_manager_session_id = current_session_in_manager.session_id
        
        print(f"[DEBUG] User {user_id} responded {response} for room {room_id}. Manager session ID: {current_manager_session_id}, topic: {current_topic}. Responses: {self.session_responses.get(room_id, {})}")
        
        if room_id not in self.active_connections or len(self.active_connections[room_id]) < 2:
            print(f"[WARNING] Not enough users in room {room_id} to process session response. Users: {len(self.active_connections.get(room_id, {})) if self.active_connections.get(room_id) else 'None'}")
            return

        if len(self.session_responses.get(room_id, {})) == 1:
            wait_message_content = "다른 사용자가 선택 중입니다..잠시만 기다려주세요"
            print(f"[DEBUG] User {user_id} is waiting for the other user in room {room_id}.")
            wait_message = {
                "type": "system",
                "content": wait_message_content,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.broadcast_to_room(room_id, wait_message, target_user_id=user_id)

        elif len(self.session_responses.get(room_id, {})) == 2:
            print(f"[DEBUG] Both users responded in room {room_id}. Processing responses: {self.session_responses[room_id]}")
            responses_map = self.session_responses[room_id]
            response_values = list(responses_map.values())
            all_yes = all(response_values)
            any_yes = any(response_values)
            
            if current_session_in_manager:
                try:
                    session_to_modify = await db.get(Session, current_session_in_manager.session_id)

                    if not session_to_modify:
                        print(f"[ERROR] Fetched session_to_modify is None for session_id {current_session_in_manager.session_id} in room {room_id}. Manager's session topic: {current_session_in_manager.topic}")
                        if room_id in self.session_responses:
                            del self.session_responses[room_id]
                        return
                    else:
                        print(f"[DEBUG] Fetched session_to_modify. ID: {session_to_modify.session_id}, Topic: {session_to_modify.topic}, extension_used: {session_to_modify.extension_used}, start_time: {session_to_modify.start_time}")

                    if all_yes or any_yes: # 사용자들이 연장을 선택한 경우
                        system_message_content = "" 

                        if session_to_modify.topic == "topic_1_situation":
                            print(f"[DEBUG] Processing situation chat extension for room {room_id}. all_yes: {all_yes}, any_yes: {any_yes}")
                            if all_yes:
                                system_message_content = "상황에 대한 대화를 1분 연장하겠습니다. 연장된 시간 동안 더 깊이 있는 대화를 나누어보세요. 서로의 입장을 이해하는 것에 집중해주시기 바랍니다."
                            else: 
                                system_message_content = "상황에 대한 대화를 1분 연장하겠습니다. 한 분이 더 많은 시간이 필요하다고 하셨습니다. 연장된 시간 동안 서로의 마음을 충분히 나누어주세요."
                        
                        elif session_to_modify.topic == "topic_2_emotion":
                            print(f"[DEBUG] Processing emotion chat extension for room {room_id}. all_yes: {all_yes}, any_yes: {any_yes}")
                            if all_yes:
                                system_message_content = "감정에 대한 대화를 1분 연장하겠습니다. 연장된 시간 동안 더 깊은 감정을 공유해보세요."
                            else: 
                                system_message_content = "감정에 대한 대화를 1분 연장하겠습니다. 한 분이 더 많은 시간이 필요하다고 하셨습니다. 서로의 감정을 깊이 나누어주세요."
                        
                        else:
                            print(f"[ERROR] Unknown topic '{session_to_modify.topic}' during extension for session {session_to_modify.session_id}. Aborting extension.")
                            if room_id in self.session_responses: del self.session_responses[room_id]
                            return

                        session_to_modify.extension_used = True
                        session_to_modify.start_time = datetime.utcnow()
                        
                        print(f"[DEBUG] Session {session_to_modify.session_id} (Topic: {session_to_modify.topic}) attempting to commit extension. DB object topic: {session_to_modify.topic}, new start_time: {session_to_modify.start_time}, extension_used: {session_to_modify.extension_used}")
                        await db.commit()
                        print(f"[DEBUG] Session {session_to_modify.session_id} commit successful for extension.")
                        await db.refresh(session_to_modify)
                        print(f"[DEBUG] Session {session_to_modify.session_id} refresh successful. Actual start_time from DB: {session_to_modify.start_time}, extension_used: {session_to_modify.extension_used}")
                        
                        self.room_sessions[room_id] = session_to_modify
                        print(f"[DEBUG] Session {session_to_modify.session_id} extended and updated in manager. Manager session topic: {self.room_sessions[room_id].topic}.")
                        
                        session_update_message = {
                            "type": "session",
                            "content": system_message_content,
                            "session_id": session_to_modify.session_id,
                            "topic": session_to_modify.topic,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        await self.broadcast_to_room(room_id, session_update_message)
                        print(f"[DEBUG] Session (Topic: {session_to_modify.topic}) extension message sent for room {room_id}.")

                        if room_id in self.session_tasks:
                            try:
                                self.session_tasks[room_id].cancel()
                                await self.session_tasks[room_id] 
                                print(f"[DEBUG] Old session task (Topic: {session_to_modify.topic}) cancelled successfully for room {room_id}.")
                            except asyncio.CancelledError:
                                print(f"[DEBUG] Old session task (Topic: {session_to_modify.topic}) for room {room_id} was already cancelled or finished.")
                            except Exception as e_cancel:
                                print(f"[ERROR] Error cancelling old session task (Topic: {session_to_modify.topic}) for room {room_id}: {e_cancel}")
                        
                        self.session_tasks[room_id] = asyncio.create_task(
                            self.check_session_timeout(room_id, db, session_to_modify.session_id)
                        )
                        print(f"[DEBUG] New session timeout task (Topic: {session_to_modify.topic}) started for session {session_to_modify.session_id} in room {room_id}.")
                        
                        if room_id in self.session_responses:
                            del self.session_responses[room_id]
                        print(f"[DEBUG] Session responses for room {room_id} cleared after {session_to_modify.topic} extension.")

                    else: 
                        print(f"[DEBUG] Both users selected 'no' for session {session_to_modify.session_id} (Topic: {session_to_modify.topic}).")
                        if session_to_modify.topic == "topic_1_situation":
                            session_to_modify.end_time = datetime.utcnow()
                            await db.commit()
                            await db.refresh(session_to_modify)
                            print(f"[DEBUG] Session {session_to_modify.session_id} ended and saved for room {room_id}.")
                            
                            connected_user_ids = list(self.active_connections[room_id].keys())
                            if len(connected_user_ids) < 2:
                                print(f"[ERROR] Less than 2 users in room {room_id} when trying to start emotion session. Aborting.")
                                if room_id in self.session_responses: del self.session_responses[room_id]
                                return
                            user_a_id_str, user_b_id_str = connected_user_ids[0], connected_user_ids[1]
                            new_topic = "topic_2_emotion"
                            system_message_content = "이제 감정에 대한 대화를 시작하겠습니다. 앞서 나눈 상황에 대해 각자 어떤 감정을 느꼈는지 솔직하게 표현해주세요. 상대방의 감정도 공감하며 들어주시기 바랍니다."
                            new_session = Session(
                                room_id=room_id,
                                user_a_id=int(user_a_id_str),
                                user_b_id=int(user_b_id_str),
                                topic=new_topic,
                                start_time=datetime.utcnow()
                            )
                            db.add(new_session)
                            await db.commit()
                            await db.refresh(new_session)
                            
                            if room_id in self.room_sessions:
                                del self.room_sessions[room_id]
                            if room_id in self.session_tasks:
                                try:
                                    self.session_tasks[room_id].cancel()
                                    await self.session_tasks[room_id]
                                except asyncio.CancelledError:
                                    print(f"[DEBUG] Old session task for room {room_id} cancelled successfully.")
                                except Exception as e_cancel:
                                    print(f"[ERROR] Error cancelling old session task for room {room_id}: {e_cancel}")
                                del self.session_tasks[room_id]
                            
                            self.room_sessions[room_id] = new_session
                            print(f"[INFO] New emotion session {new_session.session_id} started and set in manager for room {room_id}. Topic: {new_session.topic}")
                            
                            self.session_tasks[room_id] = asyncio.create_task(
                                self.check_session_timeout(room_id, db, new_session.session_id)
                            )
                            print(f"[DEBUG] New session timeout task started for session {new_session.session_id} in room {room_id}.")
                            
                            session_update_message = {
                                "type": "session",
                                "content": system_message_content,
                                "session_id": new_session.session_id,
                                "topic": new_session.topic,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            await self.broadcast_to_room(room_id, session_update_message)
                            
                            if room_id in self.session_responses:
                                del self.session_responses[room_id]
                            print(f"[DEBUG] Session responses cleared for room {room_id} after emotion session start.")

                        elif session_to_modify.topic == "topic_2_emotion":
                            print(f"[DEBUG] Processing emotion chat termination for room {room_id}. Both users selected 'no'.")
                            session_to_modify.end_time = datetime.utcnow()
                            await db.commit()
                            await db.refresh(session_to_modify)
                            print(f"[DEBUG] Final session {session_to_modify.session_id} ended for room {room_id}.")
                            
                            system_message_content = "채팅을 종료합니다. 오늘 상황과 감정에 대해 진솔한 대화를 나누어주셔서 감사합니다. 서로를 더 잘 이해하게 되셨기를 바랍니다. 앞으로도 이런 소통을 계속해나가시길 응원합니다."
                            final_message = {
                                "type": "system",
                                "content": system_message_content,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            await self.broadcast_to_room(room_id, final_message)
                            
                            if room_id in self.room_sessions:
                                del self.room_sessions[room_id]
                            if room_id in self.session_tasks:
                                try:
                                    self.session_tasks[room_id].cancel()
                                    await self.session_tasks[room_id]
                                except asyncio.CancelledError:
                                    print(f"[DEBUG] Session task for room {room_id} cancelled successfully in auto-termination.")
                                except Exception as e_cancel:
                                    print(f"[ERROR] Error cancelling session task for room {room_id} in auto-termination: {e_cancel}")
                                del self.session_tasks[room_id]
                            if room_id in self.session_responses:
                                del self.session_responses[room_id]
                            print(f"[DEBUG] All session data cleared for room {room_id} in auto-termination.")
                            return
                
                except Exception as e_commit_end:
                    print(f"[ERROR] Failed to process session response for room {room_id}: {e_commit_end}")
                    await db.rollback()
            else:
                print(f"[WARNING] No active session found in manager for room {room_id} to end or extend.")
        else:
            print(f"[WARNING] Unexpected number of responses for room {room_id}: {len(self.session_responses.get(room_id, {}))}")

manager = ConnectionManager()

async def verify_token(token: str) -> dict:
    try:
        # 토큰에서 'Bearer ' 접두사 제거
        if token.startswith('Bearer '):
            token = token[7:]
            
        # 토큰 디코딩 시도
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            print(f"Token validation error: {str(e)}")  # 디버깅용 로그
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
            
    except Exception as e:
        print(f"Token processing error: {str(e)}")  # 디버깅용 로그
        raise HTTPException(status_code=401, detail=str(e))

@app.websocket("/api/sessions/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    room_id: int, 
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        # JWT 토큰 검증
        payload = await verify_token(token)
        user_id = str(payload.get("sub"))
        print(f"[DEBUG] WebSocket connection attempt - Room: {room_id}, User: {user_id}")
        
        # 연결 수립
        await manager.connect(websocket, room_id, user_id)
        
        # 메시지 처리 태스크 시작
        message_task = asyncio.create_task(manager.process_messages(room_id))
        
        # 방 정보 조회
        room = await db.get(Room, room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
            
        # 현재 세션 상태 확인
        current_session = manager.room_sessions.get(room_id)
        connected_users = len(manager.active_connections.get(room_id, {}))
        print(f"[DEBUG] Room {room_id} status - Connected users: {connected_users}, Active session: {current_session is not None}")
        print(f"[DEBUG] Active connections: {manager.active_connections.get(room_id, {})}")
        
        # 두 명이 모두 접속했고 세션이 없는 경우 새 세션 시작
        if connected_users == 2 and not current_session:
            print(f"[DEBUG] Starting new session for room {room_id}")
            
            # 연결된 사용자들의 ID 가져오기
            connected_user_ids = list(manager.active_connections[room_id].keys())
            if len(connected_user_ids) != 2:
                print(f"[ERROR] Expected 2 users, but got {len(connected_user_ids)}: {connected_user_ids}")
                return
                
            user_a_id = int(connected_user_ids[0])
            user_b_id = int(connected_user_ids[1])
            print(f"[DEBUG] Creating session with users: {user_a_id} and {user_b_id}")
            
            try:
                current_session = Session(
                    room_id=room_id,
                    user_a_id=user_a_id,
                    user_b_id=user_b_id,
                    topic="topic_1_situation",
                    start_time=datetime.utcnow()
                )
                db.add(current_session)
                await db.commit()
                await db.refresh(current_session)
                manager.room_sessions[room_id] = current_session
                print(f"[DEBUG] Session created successfully: {current_session.session_id}")
                
                # 세션 타임아웃 체크 태스크 시작 (session_id 전달)
                if room_id in manager.session_tasks: # 만약 이전 태스크가 있다면 취소 (이론상으론 없어야 함)
                    try:
                        print(f"[DEBUG] Cancelling potentially orphaned session task for room {room_id} before starting new one for session {current_session.session_id}.")
                        manager.session_tasks[room_id].cancel()
                        await manager.session_tasks[room_id]
                    except asyncio.CancelledError:
                        pass # 예상된 동작
                    except Exception as e_orphan_cancel:
                        print(f"[ERROR] Error cancelling orphaned session task for room {room_id}: {e_orphan_cancel}")
                manager.session_tasks[room_id] = asyncio.create_task(
                    manager.check_session_timeout(room_id, db, current_session.session_id)
                )
                
                # 시스템 메시지 전송
                system_message = {
                    "type": "system",
                    "content": "안녕하세요, 저는 여러분의 대화를 도와드릴 AI 커플 상담사입니다. \n"
                                "이 공간은 갈등을 원만하게 해결하기 위한 목적의 대화방입니다. \n"
                                "두 분 모두 열린 마음으로 서로를 이해해보려는 노력을 해주셨으면 합니다. \n"
                                "이번 대화는 총 2개의 토픽으로 나뉘며, 각 토픽에 대해 약 20분간 자유롭게 대화하실 수 있습니다. \n"
                                "다만, 원활한 진행을 위해 **해당 토픽과 관련 없는 주제는 잠시 미뤄주시면 좋겠습니다.** \n"
                                "그럼 첫 번째 주제를 안내드릴게요.",
                    "timestamp": datetime.utcnow().isoformat()
                }
                print(f"[DEBUG] Sending system message to room {room_id}")
                await manager.broadcast_to_room(room_id, system_message)
                
                # 세션 시작 메시지 전송
                session_message = {
                    "type": "session",
                    "content": "상황에 대한 대화를 시작하겠습니다.",
                    "session_id": current_session.session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                print(f"[DEBUG] Sending session message to room {room_id}")
                await manager.broadcast_to_room(room_id, session_message)
                
            except Exception as e:
                print(f"[ERROR] Failed to create session: {str(e)}")
                if current_session:
                    await db.rollback()
                raise
        
        try:
            while True:
                try:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    print(f"[WS_ENDPOINT] User {user_id} in room {room_id} RECEIVED: {message_data}")
                    
                    current_session = manager.room_sessions.get(room_id)

                    if message_data.get("type") == "response":
                        if not current_session:
                            print(f"[WS_ENDPOINT] User {user_id} in room {room_id} - WARNING: No active session to process response: {message_data}")
                            continue
                        
                        response_content = message_data.get("content")
                        is_yes = response_content == "네"
                        print(f"[WS_ENDPOINT] User {user_id} in room {room_id} - Calling add_session_response. Session ID: {current_session.session_id}, Topic: {current_session.topic}, Response: {is_yes} (Content: '{response_content}')")
                        await manager.add_session_response(room_id, user_id, is_yes, db)
                        continue
                    
                    # 일반 메시지 처리
                    if current_session:
                        chat_log = ChatLog(
                            room_id=room_id,
                            session_id=current_session.session_id,
                            role=RoleType.USER,
                            speaker=SpeakerType.A if user_id == str(current_session.user_a_id) else SpeakerType.B,
                            content=message_data["content"],
                            timestamp=datetime.utcnow()
                        )
                        db.add(chat_log)
                        await db.commit()
                        
                        # 메시지 브로드캐스트
                        broadcast_message = {
                            "type": "message",
                            "user_id": user_id,
                            "content": message_data["content"],
                            "timestamp": datetime.utcnow().isoformat(),
                            "session_id": current_session.session_id # 현재 세션 ID 포함
                        }
                        await manager.broadcast_to_room(room_id, broadcast_message)
                    else:
                        # 세션이 없는 경우 (예: 한 명만 입장, 또는 세션 시작 전)
                        # 요구사항: 단독 입장 시 DB 저장 안 함, 일반 채팅만 가능
                        print(f"[INFO] No active session for room {room_id}. Broadcasting message without logging to DB. Content: {message_data['content']}")
                        broadcast_message = {
                            "type": "message",
                            "user_id": user_id,
                            "content": message_data["content"],
                            "timestamp": datetime.utcnow().isoformat()
                            # "session_id": None # 또는 이 필드를 생략
                        }
                        await manager.broadcast_to_room(room_id, broadcast_message)
                    
                except WebSocketDisconnect:
                    print(f"[DEBUG] WebSocket disconnected - Room: {room_id}, User: {user_id}")
                    break
                except Exception as e:
                    print(f"[ERROR] Error processing message: {str(e)}")
                    continue
                    
        finally:
            message_task.cancel()
            manager.disconnect(room_id, user_id)
            # 연결 해제 시 최신 세션 정보를 가져옴
            current_session = manager.room_sessions.get(room_id)
            connected_users = len(manager.active_connections.get(room_id, {}))
            print(f"[DEBUG] User {user_id} disconnected. Remaining users in room {room_id}: {connected_users}")
            
            if connected_users == 0 and current_session:
                print(f"[DEBUG] Closing session for room {room_id}")
                current_session.end_time = datetime.utcnow()
                await db.commit()
                del manager.room_sessions[room_id]
                
    except Exception as e:
        print(f"[ERROR] WebSocket error: {str(e)}")
        await websocket.close(code=1000)
        raise HTTPException(status_code=500, detail=str(e))

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str

@app.post("/api/auth/register")
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    # 사용자명 중복 확인
    query = select(User).where(User.username == register_data.username)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # 이메일 중복 확인
    query = select(User).where(User.email == register_data.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 새 사용자 생성
    user = User(
        username=register_data.username,
        email=register_data.email
    )
    user.set_password(register_data.password)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {
        "message": "User registered successfully",
        "user_id": user.user_id,
        "username": user.username
    }

@app.post("/api/auth/login")
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    # 사용자 조회
    query = select(User).where(User.username == login_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not user.verify_password(login_data.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # JWT 토큰 생성
    token_data = {
        "sub": str(user.user_id),
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "username": user.username
    }

class TempTokenRequest(BaseModel):
    user_id: int

@app.post("/api/auth/temp-token")
async def create_temp_token(request: TempTokenRequest):
    """테스트용 임시 토큰을 생성합니다."""
    token_data = {
        "sub": str(request.user_id),
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": request.user_id
    }

class CreateRoomRequest(BaseModel):
    room_name: str
    couple_id: int

    class Config:
        json_schema_extra = {
            "example": {
                "room_name": "테스트 채팅방",
                "couple_id": 1
            }
        }

@app.post("/api/rooms")
async def create_room(
    request: CreateRoomRequest,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """새로운 채팅방을 생성하거나 기존 채팅방을 찾습니다."""
    try:
        # 토큰 검증
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header is missing")
            
        if not authorization.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
            
        token = authorization.split(' ')[1]
        print(f"Received token: {token}")  # 디버깅용 로그
        
        payload = await verify_token(token)
        print(f"Token payload: {payload}")  # 디버깅용 로그
        
        user_id = str(payload.get("sub"))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user_id")
        
        # 입력값 검증
        if not request.room_name:
            raise HTTPException(status_code=400, detail="Room name is required")
        if not request.couple_id:
            raise HTTPException(status_code=400, detail="Couple ID is required")
        
        # 같은 커플 ID로 생성된 활성 채팅방이 있는지 확인
        query = select(Room).where(
            Room.couple_id == request.couple_id,
            Room.is_active == True
        ).order_by(Room.created_at.desc())
        result = await db.execute(query)
        existing_room = result.scalar_one_or_none()
        
        if existing_room:
            print(f"Found existing room for couple {request.couple_id}: {existing_room.room_id}")  # 디버깅용 로그
            return {
                "room_id": existing_room.room_id,
                "room_name": existing_room.room_name,
                "couple_id": existing_room.couple_id,
                "created_at": existing_room.created_at,
                "is_existing": True
            }
        
        # 새 채팅방 생성
        room = Room(
            room_name=request.room_name,
            couple_id=request.couple_id,
            is_active=True
        )
        db.add(room)
        await db.commit()
        await db.refresh(room)
        
        print(f"Created new room for couple {request.couple_id}: {room.room_id}")  # 디버깅용 로그
        return {
            "room_id": room.room_id,
            "room_name": room.room_name,
            "couple_id": room.couple_id,
            "created_at": room.created_at,
            "is_existing": False
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Room creation error: {str(e)}")  # 디버깅용 로그
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 