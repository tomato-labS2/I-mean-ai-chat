from app.utils.filters import EMOTION_KEYWORDS
from typing import Optional, List, Tuple
# import openai # openai 전체 임포트 대신 AsyncOpenAI 사용
from openai import AsyncOpenAI # AsyncOpenAI 직접 임포트

# tokenize_with_pos 함수 임시 구현
def tokenize_with_pos(message: str) -> List[Tuple[str, str]]:
    """
    (임시) 단순 공백 기준 토큰화 및 더미 품사 태깅.
    실제 사용을 위해서는 KoNLPy 등을 이용한 형태소 분석기 구현 필요.
    """
    print(f"[DEBUG] 임시 tokenize_with_pos 호출됨. 입력: \'{message}\'")
    # 간단히 공백으로 분리하고, 모든 단어에 'NOUN' 품사를 임시로 부여합니다.
    tokens = [(word, "NOUN") for word in message.split()]
    print(f"[DEBUG] 임시 tokenize_with_pos 결과: {tokens}")
    return tokens

class EmotionService:
    def __init__(self, openai_client: Optional[AsyncOpenAI] = None): # openai_client 주입 받도록 수정, Optional 처리
        self.openai_client = openai_client # 주입받은 클라이언트 저장

    def detect_emotion_keyword(self, message: str) -> Optional[str]:
        """형태소 분석 + 감정 키워드 매칭"""
        tokens = tokenize_with_pos(message)
        for word, pos in tokens:
            if word in EMOTION_KEYWORDS:
                return word
        return None

    async def call_gpt(self, prompt: str) -> str:
        if not self.openai_client:
            # OpenAI 클라이언트가 초기화되지 않은 경우, 에러 메시지를 반환하거나 예외를 발생시킬 수 있습니다.
            # 여기서는 간단히 경고 메시지를 출력하고 빈 문자열을 반환합니다.
            print("[EMOTION_SERVICE_ERROR] OpenAI client is not initialized in EmotionService.")
            return "OpenAI 클라이언트가 설정되지 않아 응답을 생성할 수 없습니다."

        # OpenAI API 비동기 호출 (openai >= 1.0.0 방식)
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[EMOTION_SERVICE_ERROR] Error calling OpenAI API: {e}")
            return "GPT 호출 중 오류가 발생했습니다."

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
        if not self.openai_client:
            print(f"[EMOTION_SERVICE] GPT 호출 스킵: OpenAI 클라이언트가 EmotionService에 설정되지 않음.")
            return None

        if session_topic != "topic_1_situation":
            print(f"[EMOTION_SERVICE] GPT 호출 스킵: 현재 세션 토픽({session_topic})이 'topic_1_situation'이 아님.")
            return None

        detected = self.detect_emotion_keyword(message)
        if not detected:
            return None

        prompt = f"상황에 대한 대화를 나누는 중에 메시지에서 감정 키워드 \'{detected}\'가 감지되었습니다.'감정이 담긴 키워드가 감지되었습니다. 현재는 상황에 더 집중해주세요\'라는 메세지의 AI 답변을 생성해 주세요: {message}"
        gpt_response = await self.call_gpt(prompt)
        print(f"[EMOTION_SERVICE] GPT 응답 (토픽: {session_topic}): {gpt_response}")
        return gpt_response
