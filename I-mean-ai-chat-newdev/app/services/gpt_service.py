from typing import List
from openai import AsyncOpenAI
from app.utils.report_parser import parse_report
from app.utils.logger import get_logger
from app.utils.exceptions import OpenAIServiceError, ValidationError

logger = get_logger("gpt_service")

class GPTService:
    def __init__(self, openai_client: AsyncOpenAI):
        self.client = openai_client
        logger.info("GPTService initialized")

    async def generate_report(self, chat_logs: List[dict]) -> dict:
        """
        GPT에 대화 로그를 전달하여 리포트를 생성하고, 파싱 결과를 반환한다.
        """
        logger.info(f"Generating report for {len(chat_logs)} chat logs")
        
        # 입력 검증
        if not isinstance(chat_logs, list):
            raise ValidationError("chat_logs must be a list")
        
        # 시스템 메시지를 명확하게 수정하여 GPT의 역할을 정의하고 오해를 방지
        system_message = (
            "당신은 입력된 커플 대화 내용을 분석하여 구조화된 리포트를 생성하는 AI 상담 전문가입니다. "
            "당신은 대화 내용을 저장하거나 기록하지 않으며, 오직 제공된 텍스트만을 기반으로 분석을 수행합니다. "
            "AI 상담사에 대한 내용은 언급하지 않습니다. "
            "다음 항목에 따라 분석 결과를 정리해주세요."
        )
        messages = [{"role": "system", "content": system_message}]
        
        # 대화 로그를 하나의 문자열로 묶어서 전달하는 방식을 시도해볼 수 있음 (컨텍스트 길이 제한 주의)
        # 또는 기존처럼 각 로그를 메시지로 추가
        conversation_history = ""
        for log in chat_logs:
            # 프론트엔드에서 실제 사용자 ID를 보여주는 것과 별개로, GPT에게는 일관된 역할 이름 사용
            # log["role"]에는 "USER" 또는 "ASSISTANT" 등이 올 것으로 예상됨 (SessionManager에서 그렇게 준비)
            speaker_role = "사용자" if log["role"].upper() == "USER" else "AI상담사"
            conversation_history += f"{speaker_role}: {log['content']}\n"

        if not conversation_history.strip():
            logger.warning("No conversation history provided to generate report")
            # 빈 로그에 대한 기본 반환 값 (기존 parse_report가 빈 문자열에 대해 처리하는 방식과 유사하게)
            return {
                "situation_summary": "분석할 대화 내용이 없습니다.",
                "emotion_summary": "",
                "communication_pattern": "",
                "recommendations": "",
                "suggest_counseling": False
            }

        # GPT에게 작업을 지시하는 명확한 사용자 메시지
        user_prompt = (
            f"다음은 분석할 커플 대화 내용입니다:\n\n" 
            f"<대화 시작>\n{conversation_history}<대화 끝>\n\n"
            f"위 대화 내용을 바탕으로 다음 형식에 맞춰 리포트를 작성해주세요 (각 항목의 내용은 반드시 채워주세요):\n"
            f"1. 대화 상황 요약: [여기에 요약 내용 작성]\n"
            f"2. 감정 표현 유형: [여기에 유형 분석 내용 작성]\n"
            f"3. 소통 패턴: [여기에 패턴 분석 내용 작성]\n"
            f"4. 개선 방안: [여기에 방안 제시 내용 작성]\n"
            f"5. 상담 추천 여부: [여기에 '추천함' 또는 '추천하지 않음' 또는 '고려해볼 수 있음' 등으로 답변]"
        )
        messages.append({"role": "user", "content": user_prompt})
        
        logger.debug(f"Prepared {len(messages)} messages for OpenAI API call")

        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo", # 또는 gpt-4o-mini 등 최신 모델 사용 고려
                messages=messages,
                temperature=0.5, # 약간 더 일관된 응답을 위해 temperature 조절
                # max_tokens 등을 설정하여 응답 길이 제어 가능
            )
            gpt_content = response.choices[0].message.content
            logger.info("Successfully received response from OpenAI API")
            logger.debug(f"Raw GPT content length: {len(gpt_content)} characters")
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}", exc_info=True)
            raise OpenAIServiceError(f"OpenAI API 호출 실패: {e}")

        try:
            parsed_report = parse_report(gpt_content)
            logger.info("Successfully parsed GPT response into report")
            return parsed_report
        except Exception as e:
            logger.error(f"Failed to parse GPT response: {e}", exc_info=True)
            # 파싱 실패 시 원본 응답을 포함한 기본 구조 반환
            return {
                "situation_summary": "리포트 파싱 중 오류가 발생했습니다.",
                "emotion_summary": "",
                "communication_pattern": "",
                "recommendations": "",
                "suggest_counseling": False,
                "raw_response": gpt_content[:500] + "..." if len(gpt_content) > 500 else gpt_content
            }