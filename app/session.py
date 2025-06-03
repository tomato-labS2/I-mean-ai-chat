import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Awaitable, Any

from sqlalchemy.ext.asyncio import AsyncSession
from .models.chat import Session
from .config import settings

BroadcasterType = Callable[[int, dict, Optional[str]], Awaitable[None]]
ActiveConnectionsProviderType = Callable[[int], Dict[str, Any]]

class SessionManager:
    def __init__(self, broadcaster: BroadcasterType, active_connections_provider: ActiveConnectionsProviderType):
        self.room_sessions: Dict[int, Session] = {}
        self.session_tasks: Dict[int, asyncio.Task] = {}
        self.session_responses: Dict[int, Dict[str, bool]] = {}
        self.broadcaster = broadcaster
        self.active_connections_provider = active_connections_provider

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
                "content": f"""안녕하세요, 저는 여러분의 대화를 도와드릴 AI 커플 상담사입니다. \n이 공간은 갈등을 원만하게 해결하기 위한 목적의 대화방입니다. \n두 분 모두 열린 마음으로 서로를 이해해보려는 노력을 해주셨으면 합니다. \n이번 대화는 총 2개의 토픽으로 나뉘며, 각 토픽에 대해 약 {settings.SESSION_DURATION_MINUTES}분간 자유롭게 대화하실 수 있습니다. \n다만, 원활한 진행을 위해 **해당 토픽과 관련 없는 주제는 잠시 미뤄주시면 좋겠습니다.** \n그럼 첫 번째 주제를 안내드릴게요.""",
                "timestamp": datetime.utcnow().isoformat()
            }, None)

            await self.broadcaster(room_id, {
                "type": "session",
                "content": "상황에 대한 대화를 시작하겠습니다.",
                "session_id": new_session.session_id,
                "topic": new_session.topic,
                "timestamp": datetime.utcnow().isoformat()
            }, None)

            return new_session

        except Exception as e:
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
                        await self.broadcaster(room_id, {
                            "type": "system",
                            "content": f"{topic_display_name}에 대한 대화 시간이 종료되었습니다. 계속하시겠습니까?",
                            "timestamp": datetime.utcnow().isoformat(),
                            "session_id": session_from_db.session_id
                        }, None)
                        self.session_responses[room_id] = {}
                        break
        except asyncio.CancelledError:
            pass

    async def _transition_to_emotion_topic(self, room_id: int, db: AsyncSession, ended_situation_session: Session):
        ended_situation_session.end_time = datetime.utcnow()
        await db.commit()
        await db.refresh(ended_situation_session)

        active_users = self.active_connections_provider(room_id)
        connected_user_ids = list(active_users.keys())
        if len(connected_user_ids) < 2:
            return

        new_emotion_session = Session(
            room_id=room_id,
            user_a_id=int(connected_user_ids[0]),
            user_b_id=int(connected_user_ids[1]),
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

        await self.broadcaster(room_id, {
            "type": "session",
            "content": "이제 감정에 대한 대화를 시작하겠습니다.",
            "session_id": new_emotion_session.session_id,
            "topic": new_emotion_session.topic,
            "timestamp": datetime.utcnow().isoformat()
        }, None)

    async def _end_chat_after_emotion_extension(self, room_id: int, db: AsyncSession, ended_emotion_session: Session):
        ended_emotion_session.end_time = datetime.utcnow()
        await db.commit()
        await db.refresh(ended_emotion_session)

        await self.broadcaster(room_id, {
            "type": "system",
            "content": "채팅을 종료합니다. 오늘의 대화가 두 분의 관계에 도움이 되기를 바랍니다.",
            "timestamp": datetime.utcnow().isoformat()
        }, None)
        # 리포트 생성 및 전송
        from app.services.report_formatter import format_chat_log  # 상단 import
        report_text = await format_chat_log(room_id, db)
        await self.broadcaster(room_id, {
            "type": "system",
            "content": f"📄 상담 리포트\n\n{report_text}",
            "timestamp": datetime.utcnow().isoformat()
        }, None)
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
            return

        if len(self.session_responses.get(room_id, {})) == 1:
            await self.broadcaster(room_id, {
                "type": "system",
                "content": "다른 사용자가 선택 중입니다..잠시만 기다려주세요",
                "timestamp": datetime.utcnow().isoformat()
            }, user_id)
            return

        if len(self.session_responses[room_id]) == 2:
            responses_map = self.session_responses[room_id]
            all_yes = all(responses_map.values())
            any_yes = any(responses_map.values())
            session_to_modify = await db.get(Session, current_session_in_mgr.session_id)
            if not session_to_modify:
                del self.session_responses[room_id]
                return
            try:
                if all_yes or any_yes:
                    topic_display = "상황" if session_to_modify.topic == "topic_1_situation" else "감정"
                    system_message_content = f"{topic_display}에 대한 대화를 {settings.SESSION_DURATION_MINUTES}분 연장하겠습니다."
                    session_to_modify.extension_used = True
                    session_to_modify.start_time = datetime.utcnow()
                    await db.commit()
                    await db.refresh(session_to_modify)
                    self.room_sessions[room_id] = session_to_modify
                    await self.broadcaster(room_id, {
                        "type": "session",
                        "content": system_message_content,
                        "session_id": session_to_modify.session_id,
                        "topic": session_to_modify.topic,
                        "timestamp": datetime.utcnow().isoformat()
                    }, None)
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
                del self.session_responses[room_id]
            except Exception:
                await db.rollback()

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
            except Exception:
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
