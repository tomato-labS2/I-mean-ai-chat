
from app.utils.filters import EMOTION_KEYWORDS
from app.services.emotion_service import tokenize_with_pos
from redis.asyncio import Redis
from typing import Optional
import json

class EmotionService:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def detect_emotion_keyword(self, message: str) -> Optional[str]:
        """형태소 분석 + 감정 키워드 매칭"""
        tokens = tokenize_with_pos(message)
        for word, pos in tokens:
            if word in EMOTION_KEYWORDS:
                return word
        return None

    async def handle_emotion_message(
        self,
        room_id: int,
        user_id: str,
        message: str
    ) -> bool:
        """
        감정 키워드가 감지되면 Redis에 발행

        Returns: 감지 여부 (True/False)
        """
        detected = self.detect_emotion_keyword(message)
        if not detected:
            return False

        payload = {
            "room_id": room_id,
            "user_id": user_id,
            "content": message,
            "detected_keyword": detected
        }

        await self.redis.publish("emotion_channel", json.dumps(payload))
        print(f"[EMOTION_SERVICE] 감정 키워드 감지 및 발행: {payload}")
        return True
