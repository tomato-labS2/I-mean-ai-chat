from typing import List
from openai import AsyncOpenAI
from app.utils.report_parser import parse_report

class GPTService:
    def __init__(self, openai_client: AsyncOpenAI):
        self.client = openai_client

    async def generate_report(self, chat_logs: List[dict]) -> dict:
        """
        GPT에 대화 로그를 전달하여 리포트를 생성하고, 파싱 결과를 반환한다.
        """
        messages = [{"role": "system", "content": "너는 커플의 대화 분석을 도와주는 상담 전문가야."}]
        for log in chat_logs:
            role = "user" if log["role"] == "USER" else "assistant"
            messages.append({"role": role, "content": log["content"]})

        messages.append({
            "role": "user",
            "content": (
                "지금까지의 대화를 다음 형식의 리포트로 요약해주세요:\n"
                "1. 대화 상황 요약: ...\n"
                "2. 감정 표현 유형: ...\n"
                "3. 소통 패턴: ...\n"
                "4. 개선 방안: ...\n"
                "5. 상담 추천 여부: ..."
            )
        })

        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
        )

        gpt_content = response.choices[0].message.content
        return parse_report(gpt_content)