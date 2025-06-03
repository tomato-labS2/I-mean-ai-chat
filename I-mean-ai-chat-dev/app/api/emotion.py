from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from typing import List

router = APIRouter()

@router.get("/emotions")
async def get_recent_emotions(
    room_id: int = Query(...),
    redis: Redis = Depends(lambda: router.dependencies[0].dependency()),
) -> List[str]:
    """최근 감정 메시지 로그를 Redis에서 조회 (디버깅용 또는 시각화용)"""
    key = f"emotion_log:{room_id}"
    logs = await redis.lrange(key, 0, -1)
    return [log.decode("utf-8") for log in logs]