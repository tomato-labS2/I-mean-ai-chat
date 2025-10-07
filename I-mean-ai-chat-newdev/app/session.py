import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Awaitable, Any, List
import traceback
import enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models.chat import Session, ChatLog, RoleType, SpeakerType
from .config import settings
from .services.gpt_service import GPTService
from .services.report_formatter import ReportFormatter

BroadcasterType = Callable[[int, dict, Optional[str]], Awaitable[None]]
ActiveConnectionsProviderType = Callable[[int], Dict[str, Any]]

class SessionManager:
    def __init__(self, broadcaster: BroadcasterType, active_connections_provider: ActiveConnectionsProviderType, gpt_service: Optional[GPTService] = None):
        self.room_sessions: Dict[int, Session] = {}
        self.session_tasks: Dict[int, asyncio.Task] = {}
        self.session_responses: Dict[int, Dict[str, bool]] = {}
        self.broadcaster = broadcaster
        self.active_connections_provider = active_connections_provider
        self.gpt_service = gpt_service

    async def get_current_session(self, room_id: int) -> Optional[Session]:
        return self.room_sessions.get(room_id)

    async def start_new_initial_session(self, room_id: int, user_a_id: int, user_b_id: int, db: AsyncSession) -> Optional[Session]:
        if room_id in self.room_sessions:
            return self.room_sessions[room_id]

        try:
            new_session = Session(
                room_id=room_id,
                user_a_id=user_a_id,
                user_b_id=user_b_id,
                topic="topic_1_situation",
                start_time=datetime.utcnow()
            )
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            self.room_sessions[room_id] = new_session

            if room_id in self.session_tasks:
                try:
                    self.session_tasks[room_id].cancel()
                    await self.session_tasks[room_id]
                except asyncio.CancelledError:
                    pass
            self.session_tasks[room_id] = asyncio.create_task(
                self._check_session_timeout(room_id, db, new_session.session_id)
            )

            await asyncio.sleep(1)
            await self.broadcaster(room_id, {
                "type": "system",
                "content": f"""안녕하세요, 저는 여러분의 대화를 도와드릴 AI 커플 상담사입니다😊 \n이 공간은 갈등을 원만하게 해결하기 위한 목적의 대화방입니다. \n대화는 '상황'과 '감정' 총 2개의 주제로 진행되며, 각 {settings.SESSION_DURATION_MINUTES}분간 서로 생각했던 부분을 자유롭게 나눠주시기 바랍니다. \n충분히 대화를 나누지 못했다면, 각 주제에 대해 최대 1번씩 시간 연장이 가능하니 참고 바랍니다. \n원활한 진행을 위해 해당 토픽과 관련 없는 대화는 잠시 미뤄주시고, 두 분 모두 열린 마음으로 서로를 이해해보려는 노력을 해주셨으면 합니다. \n그럼 첫 번째 주제를 안내드릴게요.""",
                "timestamp": datetime.utcnow().isoformat()
            }, None)

            await self.broadcaster(room_id, {
                "type": "session",
                "content": "우선 갈등이 생긴 상황에 대해 나눠주세요. \n해당 상황에서 어떤 감정을 느꼇는지는 잠시 미뤄두고, 갈등이 생긴 이유에 대해 생각하며 대화를 이어나가주시기 바랍니다.",
                "session_id": new_session.session_id,
                "topic": new_session.topic,
                "timestamp": datetime.utcnow().isoformat()
            }, None)

            return new_session

        except Exception as e:
            print(f"[SESSION_MGR_ERROR] Failed to create initial session for room {room_id}: {str(e)}")
            await db.rollback()
            return None

    async def _check_session_timeout(self, room_id: int, db: AsyncSession, target_session_id: int):
        try:
            while True:
                await asyncio.sleep(10)

                current_session_in_mgr = self.room_sessions.get(room_id)
                if not current_session_in_mgr or current_session_in_mgr.session_id != target_session_id:
                    break

                session = current_session_in_mgr
                if not session.start_time:
                    break

                elapsed_time = datetime.utcnow() - session.start_time
                session_timeout_duration = timedelta(minutes=settings.SESSION_DURATION_MINUTES)

                if elapsed_time >= session_timeout_duration:
                    session_from_db = await db.get(Session, session.session_id)
                    if not session_from_db:
                        break

                    if session_from_db.extension_used:
                        if session_from_db.topic == "topic_1_situation":
                            await self._transition_to_emotion_topic(room_id, db, session_from_db)
                        elif session_from_db.topic == "topic_2_emotion":
                            await self._end_chat_after_emotion_extension(room_id, db, session_from_db)
                        break
                    else:
                        topic_display_name = "상황" if session_from_db.topic == "topic_1_situation" else "감정"
                        extension_prompt_message = {
                            "type": "system",
                            "content": f"{topic_display_name}에 대한 대화 시간이 종료되었습니다. 계속하시겠습니까? \n(한 분이라도 '네'를 선택하면 시간이 연장되니 참고 바랍니다.)",
                            "timestamp": datetime.utcnow().isoformat(),
                            "session_id": session_from_db.session_id
                        }
                        await self.broadcaster(room_id, extension_prompt_message, None)
                        self.session_responses[room_id] = {}
                        break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[SESSION_MGR_ERROR] Error in _check_session_timeout for room {room_id}: {str(e)}")

    async def _send_session_report(self, room_id: int, session_id: int, db: AsyncSession):
        try:
            print(f"[SESSION_MGR] Room {room_id} - Attempting to generate session report for session {session_id}.")
            
            session_obj = await db.get(Session, session_id)
            if not session_obj:
                print(f"[SESSION_MGR_ERROR] Session object {session_id} not found for report generation.")
                return

            stmt = select(ChatLog).where(ChatLog.session_id == session_id).order_by(ChatLog.timestamp.asc())
            result = await db.execute(stmt)
            session_logs = result.scalars().all()

            if session_logs:
                user_a_id_str = str(session_obj.user_a_id)
                user_b_id_str = str(session_obj.user_b_id)

                formatted_session_logs_for_formatter = []
                for log in session_logs:
                    actual_user_id = ""
                    log_role_value = log.role.value if isinstance(log.role, enum.Enum) else str(log.role).lower()
                    
                    if log_role_value == RoleType.USER.value:
                        if log.speaker == SpeakerType.A:
                            actual_user_id = user_a_id_str
                        elif log.speaker == SpeakerType.B:
                            actual_user_id = user_b_id_str
                        else: 
                            actual_user_id = "UnknownUser" 
                    elif log_role_value == RoleType.ASSISTANT.value:
                        actual_user_id = "AI"
                    
                    report_formatter_role = "AI" if log_role_value == RoleType.ASSISTANT.value else "USER"

                    formatted_session_logs_for_formatter.append({
                        "user_id": actual_user_id,
                        "content": log.content,
                        "timestamp": log.timestamp.isoformat(),
                        "role": report_formatter_role,
                        "session_id": log.session_id,
                        "topic": session_obj.topic 
                    })
                
                openai_client_to_use = self.gpt_service.client if self.gpt_service else None
                formatter = ReportFormatter(openai_client=openai_client_to_use)
                
                session_report_string = await formatter.generate_report(formatted_session_logs_for_formatter)
                
                await self.broadcaster(room_id, {
                    "type": "message", 
                    "user_id": "AI_Report", 
                    "content": session_report_string,
                    "timestamp": datetime.utcnow().isoformat(),
                    "role": RoleType.ASSISTANT.value 
                }, None)
                print(f"[SESSION_MGR] Room {room_id} - Session report for session {session_id} broadcasted.")
            else:
                print(f"[SESSION_MGR] Room {room_id} - No chat logs found for session {session_id} to generate report.")
        except Exception as e:
            print(f"[SESSION_MGR_ERROR] Room {room_id} - Failed to generate or send session report for session {session_id}: {e}")
            traceback.print_exc()

    async def _transition_to_emotion_topic(self, room_id: int, db: AsyncSession, ended_situation_session: Session):
        system_message_content = "지금부터는 감정에 대한 내용을 나눠주세요. 그 상황에서 느꼈던 감정들을 서로 공유하고, 상대방을 이해하는 시간을 가져보겠습니다."
        ended_situation_session.end_time = datetime.utcnow()
        await db.commit()
        await db.refresh(ended_situation_session)
        print(f"[SESSION_MGR_DEBUG] Session {ended_situation_session.session_id} (topic_1_situation) ended for room {room_id}.")

        await self._send_session_report(room_id, ended_situation_session.session_id, db)
        
        active_users = self.active_connections_provider(room_id)
        connected_user_ids = list(active_users.keys())
        if len(connected_user_ids) < 2:
            return
        user_a_id_str, user_b_id_str = connected_user_ids[0], connected_user_ids[1]
        new_emotion_session = Session(
            room_id=room_id,
            user_a_id=int(user_a_id_str),
            user_b_id=int(user_b_id_str),
            topic="topic_2_emotion",
            start_time=datetime.utcnow()
        )
        db.add(new_emotion_session)
        await db.commit()
        await db.refresh(new_emotion_session)
        self.room_sessions[room_id] = new_emotion_session

        if room_id in self.session_tasks:
            self.session_tasks[room_id].cancel()
        self.session_tasks[room_id] = asyncio.create_task(
            self._check_session_timeout(room_id, db, new_emotion_session.session_id)
        )

        session_update_message = {
            "type": "session",
            "content": system_message_content,
            "session_id": new_emotion_session.session_id,
            "topic": new_emotion_session.topic,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcaster(room_id, session_update_message, None)

    async def _end_chat_after_emotion_extension(self, room_id: int, db: AsyncSession, ended_emotion_session: Session):
        system_message_content = "채팅 시간이 종료되었습니다. \n서로의 마음을 이해하고 공감하는 뜻깊은 시간이 되셨나요? \n오늘의 대화가 두 분의 관계에 도움이 되기를 바랍니다. \n좀 전의 대화내용을 기반으로 리포트가 생성될 예정이니 방을 나가지 마시고 잠시만 기다려주세요."
        
        ended_emotion_session.end_time = datetime.utcnow()
        await db.commit()
        await db.refresh(ended_emotion_session)
        print(f"[SESSION_MGR_DEBUG] Final session {ended_emotion_session.session_id} (topic_2_emotion) ended for room {room_id}.")

        await self._send_session_report(room_id, ended_emotion_session.session_id, db)

        final_system_message = {"type": "system", "content": system_message_content, "timestamp": datetime.utcnow().isoformat()}
        await self.broadcaster(room_id, final_system_message, None)
        
        if self.gpt_service:
            try:
                print(f"[SESSION_MGR] Room {room_id} - Attempting to generate FINAL GPT report.")
                stmt = select(ChatLog).where(ChatLog.room_id == room_id).order_by(ChatLog.timestamp.asc())
                result = await db.execute(stmt)
                logs_for_final_report = result.scalars().all()

                if logs_for_final_report:
                    formatted_logs_for_gpt_service = [
                        {"role": log.role.value if isinstance(log.role, enum.Enum) else str(log.role).lower(), "content": log.content}
                        for log in logs_for_final_report
                    ]
                    print(f"[SESSION_MGR_DEBUG] Room {room_id} - About to call gpt_service.generate_report with {len(formatted_logs_for_gpt_service)} logs.")
                    report_dict = await self.gpt_service.generate_report(formatted_logs_for_gpt_service)
                    print(f"[SESSION_MGR_DEBUG] Room {room_id} - gpt_service.generate_report returned: {report_dict}")

                    report_items = []
                    if report_dict and report_dict.get("situation_summary") and isinstance(report_dict.get("situation_summary"), str) and report_dict.get("situation_summary").strip(): 
                        report_items.append(f"📊 대화 상황 요약:\n{report_dict['situation_summary']}")
                    if report_dict and report_dict.get("emotion_summary") and isinstance(report_dict.get("emotion_summary"), str) and report_dict.get("emotion_summary").strip(): 
                        report_items.append(f"😊 감정 표현 유형:\n{report_dict['emotion_summary']}")
                    if report_dict and report_dict.get("communication_pattern") and isinstance(report_dict.get("communication_pattern"), str) and report_dict.get("communication_pattern").strip(): 
                        report_items.append(f"🗣️ 소통 패턴:\n{report_dict['communication_pattern']}")
                    if report_dict and report_dict.get("recommendations") and isinstance(report_dict.get("recommendations"), str) and report_dict.get("recommendations").strip(): 
                        report_items.append(f"💡 개선 방안:\n{report_dict['recommendations']}")
                    
                    if report_dict and "suggest_counseling" in report_dict:
                        is_recommended = report_dict.get("suggest_counseling")
                        recommendation_text = "예 (상담을 고려해볼 수 있습니다.)" if is_recommended else "아니요 (현재 필수는 아닐 수 있습니다.)"
                        report_items.append(f"⭐ 상담 추천 여부:\n{recommendation_text}")
                    
                    print(f"[SESSION_MGR_DEBUG] Room {room_id} - Constructed report_items: {report_items}")

                    final_report_string = "✨ 최종 상담 리포트 ✨\n\n" + "\n\n".join(report_items)
                    
                    print(f"[SESSION_MGR_DEBUG] Room {room_id} - Final report string length: {len(final_report_string)}")

                    await self.broadcaster(room_id, {
                        "type": "message",
                        "user_id": "AI",
                        "content": final_report_string,
                        "timestamp": datetime.utcnow().isoformat(),
                        "role": RoleType.ASSISTANT.value 
                    }, None)
                    print(f"[SESSION_MGR] Room {room_id} - FINAL GPT Report generated and broadcasted.")
                else:
                    print(f"[SESSION_MGR] Room {room_id} - No chat logs for FINAL GPT report.")
            except Exception as e:
                print(f"[SESSION_MGR_ERROR] Room {room_id} - Failed to generate or send FINAL GPT report: {e}")
                traceback.print_exc()
        else:
            print(f"[SESSION_MGR_WARNING] Room {room_id} - GPTService not available. Cannot generate FINAL report.")

        self.clear_room_session_data(room_id)

    async def add_session_response(self, room_id: int, user_id: str, response: bool, db: AsyncSession):
        if room_id not in self.session_responses:
            self.session_responses[room_id] = {}
        self.session_responses[room_id][user_id] = response

        current_session_in_mgr = self.room_sessions.get(room_id)
        if not current_session_in_mgr:
            if room_id in self.session_responses:
                del self.session_responses[room_id]
            return

        active_users = self.active_connections_provider(room_id)
        if len(active_users) < 2:
            if room_id in self.session_responses and len(self.session_responses[room_id]) == 1:
                 print(f"[SESSION_MGR_INFO] Room {room_id} - Response received from {user_id}, but only one user. Clearing response for now.")
            return

        if len(self.session_responses.get(room_id, {})) == 1:
            await self.broadcaster(room_id, {
                "type": "system",
                "content": "다른 사용자가 선택 중입니다..잠시만 기다려주세요",
                "timestamp": datetime.utcnow().isoformat()
            }, user_id)
            return

        if len(self.session_responses[room_id]) == 2:
            responses_map = self.session_responses.pop(room_id)
            all_yes = all(responses_map.values())
            any_yes = any(responses_map.values())
            
            session_to_modify = await db.get(Session, current_session_in_mgr.session_id)
            if not session_to_modify: 
                print(f"[SESSION_MGR_WARN] Room {room_id} - Session {current_session_in_mgr.session_id} not found in DB for response processing.")
                return
            try:
                if all_yes or any_yes:
                    topic_display = "상황" if session_to_modify.topic == "topic_1_situation" else "감정"
                    system_message_content = f"{topic_display}에 대한 대화를 {settings.SESSION_DURATION_MINUTES}분 연장하겠습니다. \n더 충분히 대화를 나눠주세요."
                    session_to_modify.extension_used = True
                    session_to_modify.start_time = datetime.utcnow()
                    await db.commit()
                    await db.refresh(session_to_modify)
                    self.room_sessions[room_id] = session_to_modify
                    session_update_msg = {
                        "type": "session", 
                        "content": system_message_content,
                        "session_id": session_to_modify.session_id, 
                        "topic": session_to_modify.topic,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.broadcaster(room_id, session_update_msg, None)
                    
                    if room_id in self.session_tasks:
                        self.session_tasks[room_id].cancel()
                    self.session_tasks[room_id] = asyncio.create_task(
                        self._check_session_timeout(room_id, db, session_to_modify.session_id)
                    )
                else:
                    if session_to_modify.topic == "topic_1_situation":
                        await self._transition_to_emotion_topic(room_id, db, session_to_modify)
                    elif session_to_modify.topic == "topic_2_emotion":
                        await self._end_chat_after_emotion_extension(room_id, db, session_to_modify)
            except Exception as e_resp_proc:
                await db.rollback()
                print(f"[SESSION_MGR_ERROR] Error processing session responses for room {room_id}. Exception type: {type(e_resp_proc)}, Args: {e_resp_proc.args}")
                traceback.print_exc()

    async def end_session_for_room(self, room_id: int, db: AsyncSession):
        current_session = self.room_sessions.get(room_id)
        if current_session and current_session.end_time is None:
            try:
                db_session = await db.get(Session, current_session.session_id)
                if db_session and db_session.end_time is None:
                    db_session.end_time = datetime.utcnow()
                    await db.commit()
                    await db.refresh(db_session)
                    self.room_sessions[room_id] = db_session
            except Exception as e_db_end:
                print(f"[SESSION_MGR_ERROR] Failed to mark session {current_session.session_id} as ended in DB for room {room_id}: {e_db_end}")
                await db.rollback()
        self.clear_room_session_data(room_id)

    def clear_room_session_data(self, room_id: int):
        if room_id in self.room_sessions:
            del self.room_sessions[room_id]
        if room_id in self.session_tasks:
            try:
                self.session_tasks[room_id].cancel()
            except Exception:
                pass
            del self.session_tasks[room_id]
        if room_id in self.session_responses:
            del self.session_responses[room_id]
        print(f"[SESSION_MGR_INFO] All in-memory session data cleared for room {room_id}.")
