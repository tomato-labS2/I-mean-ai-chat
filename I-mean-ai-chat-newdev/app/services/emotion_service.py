from app.utils.filters import EMOTION_KEYWORDS, BAD_WORDS, MEDIATION_MESSAGES
from typing import Optional, List, Tuple
import random
# import openai # openai 전체 임포트 대신 AsyncOpenAI 사용
from openai import AsyncOpenAI # AsyncOpenAI 직접 임포트
from app.utils.logger import get_logger
from app.utils.exceptions import OpenAIServiceError, ValidationError

logger = get_logger("emotion_service")

# tokenize_with_pos 함수 임시 구현
def tokenize_with_pos(message: str) -> List[Tuple[str, str]]:
    """
    (임시) 단순 공백 기준 토큰화 및 더미 품사 태깅.
    실제 사용을 위해서는 KoNLPy 등을 이용한 형태소 분석기 구현 필요.
    """
    logger.debug(f"Tokenizing message: '{message}'")
    # 간단히 공백으로 분리하고, 모든 단어에 'NOUN' 품사를 임시로 부여합니다.
    tokens = [(word, "NOUN") for word in message.split()]
    logger.debug(f"Tokenization result: {tokens}")
    return tokens

class EmotionService:
    def __init__(self, openai_client: Optional[AsyncOpenAI] = None): # openai_client 주입 받도록 수정, Optional 처리
        self.openai_client = openai_client # 주입받은 클라이언트 저장
        logger.info("EmotionService initialized")
        if not openai_client:
            logger.warning("OpenAI client not provided to EmotionService")

    def detect_emotion_keyword(self, message: str) -> Optional[str]:
        """형태소 분석 + 감정 키워드 매칭"""
        if not message or not isinstance(message, str):
            logger.warning("Invalid message provided for emotion detection")
            return None
            
        logger.debug(f"Detecting emotion keywords in message: '{message[:50]}...'")
        tokens = tokenize_with_pos(message)
        
        for word, pos in tokens:
            if word in EMOTION_KEYWORDS:
                logger.info(f"Emotion keyword detected: '{word}'")
                return word
        
        logger.debug("No emotion keywords detected")
        return None

    def detect_bad_words(self, message: str) -> Optional[str]:
        """비속어/비난 단어 감지"""
        if not message or not isinstance(message, str):
            logger.warning("Invalid message provided for bad word detection")
            return None
            
        logger.debug(f"Detecting bad words in message: '{message[:50]}...'")
        
        # 메시지를 소문자로 변환하여 검사
        message_lower = message.lower()
        
        for bad_word in BAD_WORDS:
            if bad_word in message_lower:
                logger.warning(f"Bad word detected: '{bad_word}' in message")
                return bad_word
        
        logger.debug("No bad words detected")
        return None

    def generate_mediation_message(self) -> str:
        """중재 메시지 생성 (랜덤 선택)"""
        mediation_message = random.choice(MEDIATION_MESSAGES)
        logger.info(f"Generated mediation message: '{mediation_message[:50]}...'")
        return mediation_message

    async def call_gpt(self, prompt: str) -> str:
        """OpenAI GPT API 호출"""
        if not self.openai_client:
            logger.error("OpenAI client is not initialized in EmotionService")
            raise OpenAIServiceError("OpenAI 클라이언트가 설정되지 않았습니다")

        if not prompt or not isinstance(prompt, str):
            raise ValidationError("Invalid prompt provided")

        logger.debug(f"Calling GPT with prompt: '{prompt[:100]}...'")

        # OpenAI API 비동기 호출 (openai >= 1.0.0 방식)
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            gpt_response = response.choices[0].message.content
            logger.info("Successfully received response from GPT")
            logger.debug(f"GPT response: '{gpt_response[:100]}...'")
            return gpt_response
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
            raise OpenAIServiceError(f"GPT 호출 중 오류가 발생했습니다: {e}")

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
        logger.debug(f"Handling emotion message - Room: {room_id}, User: {user_id}, Topic: {session_topic}")
        
        if not self.openai_client:
            logger.warning("GPT 호출 스킵: OpenAI 클라이언트가 EmotionService에 설정되지 않음")
            return None

        if session_topic != "topic_1_situation":
            logger.debug(f"GPT 호출 스킵: 현재 세션 토픽({session_topic})이 'topic_1_situation'이 아님")
            return None

        detected = self.detect_emotion_keyword(message)
        if not detected:
            logger.debug("감정 키워드가 감지되지 않아 GPT 호출을 스킵합니다")
            return None

        try:
            prompt = f"상황에 대한 대화를 나누는 중에 메시지에서 감정 키워드 '{detected}'가 감지되었습니다.'감정이 담긴 키워드가 감지되었습니다. 현재는 상황에 더 집중해주세요'라는 메세지의 AI 답변을 생성해 주세요: {message}"
            gpt_response = await self.call_gpt(prompt)
            logger.info(f"GPT 응답 생성 완료 (토픽: {session_topic}): '{gpt_response[:50]}...'")
            return gpt_response
        except Exception as e:
            logger.error(f"감정 메시지 처리 중 오류 발생: {e}", exc_info=True)
            return None

    async def handle_mediation_message(
        self,
        room_id: int,
        user_id: str,
        message: str,
        session_topic: Optional[str] = None
    ) -> Optional[str]:
        """
        비속어/비난 단어가 감지되고 세션 토픽이 'topic_2_emotion'일 때만 중재 메시지 생성
        Returns: 중재 메시지 문자열 (조건 미충족 또는 감지 안되면 None)
        """
        logger.debug(f"Handling mediation message - Room: {room_id}, User: {user_id}, Topic: {session_topic}")
        
        if session_topic != "topic_2_emotion":
            logger.debug(f"중재 메시지 스킵: 현재 세션 토픽({session_topic})이 'topic_2_emotion'이 아님")
            return None

        detected_bad_word = self.detect_bad_words(message)
        if not detected_bad_word:
            logger.debug("비속어/비난 단어가 감지되지 않아 중재 메시지를 스킵합니다")
            return None

        try:
            mediation_message = self.generate_mediation_message()
            logger.info(f"중재 메시지 생성 완료 (토픽: {session_topic}): '{mediation_message[:50]}...'")
            return mediation_message
        except Exception as e:
            logger.error(f"중재 메시지 처리 중 오류 발생: {e}", exc_info=True)
            return None
