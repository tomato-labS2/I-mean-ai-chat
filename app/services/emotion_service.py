from app.utils.filters import EMOTION_KEYWORDS
from typing import Optional, List, Tuple
import openai

# tokenize_with_pos 함수 임시 구현
def tokenize_with_pos(message: str) -> List[Tuple[str, str]]:
    """
    (임시) 단순 공백 기준 토큰화 및 더미 품사 태깅.
    실제 사용을 위해서는 KoNLPy 등을 이용한 형태소 분석기 구현 필요.
    """
    print(f"[DEBUG] 임시 tokenize_with_pos 호출됨. 입력: '{message}'")
    # 간단히 공백으로 분리하고, 모든 단어에 'NOUN' 품사를 임시로 부여합니다.
    tokens = [(word, "NOUN") for word in message.split()]
    print(f"[DEBUG] 임시 tokenize_with_pos 결과: {tokens}")
    return tokens

class EmotionService:
    def __init__(self):
        pass  # 더 이상 redis_client 필요 없음

    def detect_emotion_keyword(self, message: str) -> Optional[str]:
        """형태소 분석 + 감정 키워드 매칭"""
        tokens = tokenize_with_pos(message)
        for word, pos in tokens:
            if word in EMOTION_KEYWORDS:
                return word
        return None

    async def call_gpt(self, prompt: str) -> str:
        # OpenAI API 비동기 호출
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    async def handle_emotion_message(
        self,
        room_id: int,
        user_id: str,
        message: str,
        session_topic: Optional[str] = None
    ) -> Optional[str]:
        """
        감정 키워드가 감지되고 세션 토픽이 'topic_1_situation'일 때만 GPT 호출
        Returns: GPT 응답 문자열 (조건 미충족 또는 감지 안되면 None)
        """
        if session_topic != "topic_1_situation":
            print(f"[EMOTION_SERVICE] GPT 호출 스킵: 현재 세션 토픽({session_topic})이 'topic_1_situation'이 아님.")
            return None

        detected = self.detect_emotion_keyword(message)
        if not detected:
            return None

        prompt = f"다음 메시지에서 감정 키워드 '{detected}'가 감지되었습니다. 공감은 하지말고 지금은 감정을 가라앉히고 상황에 집중하는 시간이기 때문에 감정이 담긴 대화를 하지 않도록 AI 답변을 생성해 주세요: {message}"
        gpt_response = await self.call_gpt(prompt)
        print(f"[EMOTION_SERVICE] GPT 응답 (토픽: {session_topic}): {gpt_response}")
        return gpt_response
