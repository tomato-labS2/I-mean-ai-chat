from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.chat import Session, ChatLog

router = APIRouter()

@router.get("/sessions/{room_id}", response_model=List[int])
async def get_session_ids_for_room(room_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session.session_id).where(Session.room_id == room_id))
    return [row[0] for row in result.all()]

@router.get("/logs/{session_id}")
async def get_chat_logs_for_session(session_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChatLog).where(ChatLog.session_id == session_id).order_by(ChatLog.timestamp))
    logs = result.scalars().all()
    return [{
        "role": log.role.value,
        "speaker": log.speaker.name if log.speaker else None,
        "content": log.content,
        "timestamp": log.timestamp.isoformat()
    } for log in logs]