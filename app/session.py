import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Awaitable, Any

from sqlalchemy.ext.asyncio import AsyncSession
from .models.chat import Session # Session 모델 import
from .config import settings # 설정값 import
from sqlalchemy import update

# 타입 힌팅을 위한 정의
BroadcasterType = Callable[[int, dict, Optional[str]], Awaitable[None]]
ActiveConnectionsProviderType = Callable[[int], Dict[str, Any]] # 실제 WebSocket 객체 대신 Any로 단순화

class SessionManager:
    def __init__(self, broadcaster: BroadcasterType, active_connections_provider: ActiveConnectionsProviderType):
        # 방별 현재 진행중인 세션 정보 저장 (room_id: Session 객체)
        self.room_sessions: Dict[int, Session] = {}
        # 방별 세션 타임아웃 체크 비동기 태스크 저장 (room_id: asyncio.Task)
        self.session_tasks: Dict[int, asyncio.Task] = {}
        # 방별 사용자 세션 연장/종료 응답 저장 (room_id: {user_id: bool})
        self.session_responses: Dict[int, Dict[str, bool]] = {}
        
        self.broadcaster = broadcaster
        self.active_connections_provider = active_connections_provider

    async def get_current_session(self, room_id: int) -> Optional[Session]:
        """지정된 방의 현재 활성화된 세션 객체를 반환합니다."""
        return self.room_sessions.get(room_id)

    async def start_new_initial_session(self, room_id: int, user_a_id: int, user_b_id: int, db: AsyncSession) -> Optional[Session]:
        """두 명의 사용자가 방에 모두 접속했을 때 초기 'topic_1_situation' 세션을 시작합니다."""
        print(f"[SESSION_MGR] Attempting to start new initial session for room {room_id} with users {user_a_id}, {user_b_id}")
        if room_id in self.room_sessions: # 이미 세션이 진행 중이면 새로 시작하지 않음
            print(f"[SESSION_MGR] Session already exists for room {room_id}. Cannot start new initial session.")
            return self.room_sessions[room_id]

        try:
            new_session = Session(
                room_id=room_id,
                user_a_id=user_a_id,
                user_b_id=user_b_id,
                topic="topic_1_situation", # 첫 번째 토픽
                start_time=datetime.utcnow()
            )
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            self.room_sessions[room_id] = new_session
            print(f"[SESSION_MGR] Initial session {new_session.session_id} created successfully for room {room_id}")

            # 새 세션에 대한 타임아웃 체크 태스크 시작
            if room_id in self.session_tasks: # 이전 태스크 정리 (이론상 거의 없음)
                try:
                    self.session_tasks[room_id].cancel()
                    await self.session_tasks[room_id]
                except asyncio.CancelledError: pass
                except Exception as e_orphan_cancel: print(f"[SESSION_MGR_ERROR] Error cancelling orphaned task: {e_orphan_cancel}")
            
            self.session_tasks[room_id] = asyncio.create_task(
                self._check_session_timeout(room_id, db, new_session.session_id)
            )
            
            # 초기 시스템 안내 메시지 전송 (1초 지연)
            await asyncio.sleep(1)
            initial_system_message = {
                "type": "system",
                "content": f"""안녕하세요, 저는 여러분의 대화를 도와드릴 AI 커플 상담사입니다. \n
이 공간은 갈등을 원만하게 해결하기 위한 목적의 대화방입니다. \n
두 분 모두 열린 마음으로 서로를 이해해보려는 노력을 해주셨으면 합니다. \n
이번 대화는 총 2개의 토픽으로 나뉘며, 각 토픽에 대해 약 {settings.SESSION_DURATION_MINUTES}분간 자유롭게 대화하실 수 있습니다. \n
다만, 원활한 진행을 위해 **해당 토픽과 관련 없는 주제는 잠시 미뤄주시면 좋겠습니다.** \n
그럼 첫 번째 주제를 안내드릴게요.""",
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.broadcaster(room_id, initial_system_message, None)
            
            # 첫 세션 시작 알림 메시지 전송
            first_session_start_message = {
                "type": "session",
                "content": "상황에 대한 대화를 시작하겠습니다.",
                "session_id": new_session.session_id,
                "topic": new_session.topic,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.broadcaster(room_id, first_session_start_message, None)
            return new_session
            
        except Exception as e:
            print(f"[SESSION_MGR_ERROR] Failed to create initial session for room {room_id}: {str(e)}")
            await db.rollback()
            return None

    async def _check_session_timeout(self, room_id: int, db: AsyncSession, target_session_id: int):
        """(내부용) 채팅 세션의 시간제한을 주기적으로 확인하고, 시간이 다 되면 연장 여부를 묻거나 다음 세션으로 자동 전환합니다."""
        try:
            print(f"[SESSION_MGR_DEBUG] Starting _check_session_timeout for room {room_id}, target session_id {target_session_id}.")
            while True:
                await asyncio.sleep(10)

                current_session_in_mgr = self.room_sessions.get(room_id)
                if not current_session_in_mgr or current_session_in_mgr.session_id != target_session_id:
                    print(f"[SESSION_MGR_DEBUG] Ending timeout task for room {room_id}, target {target_session_id}. Current in mgr: {current_session_in_mgr.session_id if current_session_in_mgr else 'None'}.")
                    break

                session = current_session_in_mgr
                if not session.start_time:
                    print(f"[SESSION_MGR_ERROR] Session {session.session_id} for room {room_id} is missing start_time. Ending timeout check.")
                    break
                
                elapsed_time = datetime.utcnow() - session.start_time
                session_timeout_duration = timedelta(minutes=settings.SESSION_DURATION_MINUTES)

                if elapsed_time >= session_timeout_duration:
                    print(f"[SESSION_MGR_DEBUG] Session {session.session_id} in room {room_id} has timed out.")
                    session_from_db = await db.get(Session, session.session_id)
                    if not session_from_db:
                        print(f"[SESSION_MGR_ERROR] Session {session.session_id} not found in DB during timeout. Ending task.")
                        break
                    
                    if session_from_db.extension_used: # 이미 연장 사용
                        print(f"[SESSION_MGR_DEBUG] Session {session.session_id} (topic: {session_from_db.topic}) already used extension. Auto-transitioning.")
                        if session_from_db.topic == "topic_1_situation":
                            await self._transition_to_emotion_topic(room_id, db, session_from_db)
                        elif session_from_db.topic == "topic_2_emotion":
                            await self._end_chat_after_emotion_extension(room_id, db, session_from_db)
                        break 
                    else: # 연장 질문
                        topic_display_name = "상황" if session_from_db.topic == "topic_1_situation" else "감정"
                        extension_prompt_message = {
                            "type": "system",
                            "content": f"{topic_display_name}에 대한 대화 시간이 종료되었습니다. 계속하시겠습니까?",
                            "timestamp": datetime.utcnow().isoformat(),
                            "session_id": session_from_db.session_id
                        }
                        await self.broadcaster(room_id, extension_prompt_message, None)
                        self.session_responses[room_id] = {} # 응답 받을 준비
                        print(f"[SESSION_MGR_DEBUG] Extension prompt sent for session {session.session_id}. Task for this session instance is now complete.")
                        break
        except asyncio.CancelledError:
            print(f"[SESSION_MGR_DEBUG] Session check task for room {room_id}, target session {target_session_id} was cancelled.")
        except Exception as e:
            print(f"[SESSION_MGR_ERROR] Error in _check_session_timeout for room {room_id}, target session {target_session_id}: {str(e)}")

    async def _transition_to_emotion_topic(self, room_id: int, db: AsyncSession, ended_situation_session: Session):
        """상황 주제 세션 종료 후 감정 주제 세션으로 전환합니다."""
        system_message_content = "이제 감정에 대한 대화를 시작하겠습니다. 상황에 대한 충분한 대화를 나누셨습니다. 이제 그 상황에서 느꼈던 감정들을 서로 공유해보는 시간을 가져보겠습니다."
        
        ended_situation_session.end_time = datetime.utcnow()
        await db.commit()
        await db.refresh(ended_situation_session)
        print(f"[SESSION_MGR_DEBUG] Session {ended_situation_session.session_id} (topic_1_situation) ended for room {room_id}.")

        active_users = self.active_connections_provider(room_id)
        connected_user_ids = list(active_users.keys())
        if len(connected_user_ids) < 2:
            print(f"[SESSION_MGR_ERROR] Less than 2 users in room {room_id} for emotion topic transition. Aborting.")
            return

        user_a_id_str, user_b_id_str = connected_user_ids[0], connected_user_ids[1]
        new_emotion_session = Session(
            room_id=room_id, user_a_id=int(user_a_id_str), user_b_id=int(user_b_id_str),
            topic="topic_2_emotion", start_time=datetime.utcnow()
        )
        db.add(new_emotion_session)
        await db.commit()
        await db.refresh(new_emotion_session)
        self.room_sessions[room_id] = new_emotion_session
        print(f"[SESSION_MGR_INFO] New emotion session {new_emotion_session.session_id} started for room {room_id}.")

        if room_id in self.session_tasks: self.session_tasks[room_id].cancel()
        self.session_tasks[room_id] = asyncio.create_task(
            self._check_session_timeout(room_id, db, new_emotion_session.session_id)
        )
        
        session_update_message = {
            "type": "session", "content": system_message_content,
            "session_id": new_emotion_session.session_id, "topic": new_emotion_session.topic,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcaster(room_id, session_update_message, None)

    async def _end_chat_after_emotion_extension(self, room_id: int, db: AsyncSession, ended_emotion_session: Session):
        """감정 주제 세션의 연장 시간 만료 후 채팅을 최종 종료합니다."""
        system_message_content = "채팅을 종료합니다. 상황과 감정에 대한 충분한 대화를 나누셨습니다. 서로의 마음을 이해하고 공감하는 뜻깊은 시간이었습니다. 오늘의 대화가 두 분의 관계에 도움이 되기를 바랍니다."
        
        ended_emotion_session.end_time = datetime.utcnow()
        await db.commit()
        await db.refresh(ended_emotion_session)
        print(f"[SESSION_MGR_DEBUG] Final session {ended_emotion_session.session_id} (topic_2_emotion) ended for room {room_id}.")

        final_message = {"type": "system", "content": system_message_content, "timestamp": datetime.utcnow().isoformat()}
        await self.broadcaster(room_id, final_message, None)
        
        self.clear_room_session_data(room_id)

    async def add_session_response(self, room_id: int, user_id: str, response: bool, db: AsyncSession):
        """사용자의 세션 연장/종료 응답을 처리하고, 두 사용자 모두 응답하면 다음 단계를 진행합니다."""
        if room_id not in self.session_responses: self.session_responses[room_id] = {}
        self.session_responses[room_id][user_id] = response
        
        current_session_in_mgr = self.room_sessions.get(room_id)
        if not current_session_in_mgr:
            print(f"[SESSION_MGR_WARNING] No active session in manager for room {room_id} to process response. User: {user_id}")
            if room_id in self.session_responses: del self.session_responses[room_id]
            return

        print(f"[SESSION_MGR_DEBUG] User {user_id} responded {response} for room {room_id}. Session {current_session_in_mgr.session_id}, Topic {current_session_in_mgr.topic}. Responses: {self.session_responses.get(room_id, {})}")

        active_users = self.active_connections_provider(room_id)
        if len(active_users) < 2:
            print(f"[SESSION_MGR_WARNING] Not enough users in room {room_id} to process full session response. Users: {len(active_users)}")
            return

        if len(self.session_responses.get(room_id, {})) == 1:
            wait_message_content = "다른 사용자가 선택 중입니다..잠시만 기다려주세요"
            await self.broadcaster(room_id, {"type": "system", "content": wait_message_content, "timestamp": datetime.utcnow().isoformat()}, user_id)
            return

        if len(self.session_responses.get(room_id, {})) == 2:
            print(f"[SESSION_MGR_DEBUG] Both users responded in room {room_id}. Processing responses: {self.session_responses[room_id]}")
            responses_map = self.session_responses[room_id]
            all_yes = all(responses_map.values())
            any_yes = any(responses_map.values())
            
            session_to_modify = await db.get(Session, current_session_in_mgr.session_id)
            if not session_to_modify:
                print(f"[SESSION_MGR_ERROR] Session {current_session_in_mgr.session_id} not found in DB for response processing. Room {room_id}")
                if room_id in self.session_responses: del self.session_responses[room_id]
                return

            try:
                if all_yes or any_yes:
                    system_message_content = ""
                    topic_display = "상황" if session_to_modify.topic == "topic_1_situation" else "감정"
                    if all_yes: system_message_content = f"{topic_display}에 대한 대화를 {settings.SESSION_DURATION_MINUTES}분 연장하겠습니다. 더 깊이 있는 대화를 나누어보세요."
                    else: system_message_content = f"{topic_display}에 대한 대화를 {settings.SESSION_DURATION_MINUTES}분 연장하겠습니다. 한 분이 더 많은 시간이 필요하다고 하셨습니다."

                    session_to_modify.extension_used = True
                    session_to_modify.start_time = datetime.utcnow()
                    await db.commit()
                    await db.refresh(session_to_modify)
                    self.room_sessions[room_id] = session_to_modify
                    
                    print(f"[SESSION_MGR_DEBUG] Session {session_to_modify.session_id} (Topic: {session_to_modify.topic}) extended for room {room_id}.")
                    
                    session_update_msg = {
                        "type": "session", "content": system_message_content,
                        "session_id": session_to_modify.session_id, "topic": session_to_modify.topic,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.broadcaster(room_id, session_update_msg, None)

                    if room_id in self.session_tasks: self.session_tasks[room_id].cancel()
                    self.session_tasks[room_id] = asyncio.create_task(
                        self._check_session_timeout(room_id, db, session_to_modify.session_id)
                    )
                else: # 모두 연장 거부
                    print(f"[SESSION_MGR_DEBUG] Both users selected 'no' for session {session_to_modify.session_id} (Topic: {session_to_modify.topic}). Transitioning or ending.")
                    if session_to_modify.topic == "topic_1_situation":
                        await self._transition_to_emotion_topic(room_id, db, session_to_modify)
                    elif session_to_modify.topic == "topic_2_emotion":
                        await self._end_chat_after_emotion_extension(room_id, db, session_to_modify)

                if room_id in self.session_responses: del self.session_responses[room_id]
            
            except Exception as e_resp_proc:
                print(f"[SESSION_MGR_ERROR] Error processing session responses for room {room_id}: {e_resp_proc}")
                await db.rollback()

    async def end_session_for_room(self, room_id: int, db: AsyncSession):
        """특정 방의 현재 활성화된 세션을 DB에 종료 상태로 업데이트합니다 (예: 마지막 사용자가 나갈 때)."""
        current_session = self.room_sessions.get(room_id)
        if current_session and current_session.end_time is None:
            try:
                db_session = await db.get(Session, current_session.session_id)
                if db_session and db_session.end_time is None:
                    db_session.end_time = datetime.utcnow()
                    await db.commit()
                    await db.refresh(db_session)
                    self.room_sessions[room_id] = db_session 
                    print(f"[SESSION_MGR_INFO] Session {db_session.session_id} for room {room_id} marked as ended in DB.")
            except Exception as e_db_end:
                print(f"[SESSION_MGR_ERROR] Failed to mark session {current_session.session_id} as ended in DB for room {room_id}: {e_db_end}")
                await db.rollback()
        
        self.clear_room_session_data(room_id)

    def clear_room_session_data(self, room_id: int):
        """지정된 방과 관련된 모든 인메모리 세션 데이터를 정리합니다 (타임아웃 태스크 포함)."""
        if room_id in self.room_sessions:
            del self.room_sessions[room_id]
        if room_id in self.session_tasks:
            try:
                self.session_tasks[room_id].cancel()
            except Exception as e_task_cancel:
                print(f"[SESSION_MGR_DEBUG] Error cancelling session task for room {room_id} during clear: {e_task_cancel}")
            del self.session_tasks[room_id]
        if room_id in self.session_responses:
            del self.session_responses[room_id]
        print(f"[SESSION_MGR_INFO] All in-memory session data cleared for room {room_id}.") 