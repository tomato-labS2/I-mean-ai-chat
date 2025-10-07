# app/services/report_formatter.py

from typing import List, Dict, Optional
from datetime import datetime
from openai import AsyncOpenAI # AsyncOpenAI 임포트

class ReportFormatter:
    def __init__(self, openai_client: Optional[AsyncOpenAI] = None):
        self.openai_client = openai_client

    async def _summarize_chat_logs_with_gpt(self, chat_logs: List[Dict], session_topic_display: str) -> str:
        if not self.openai_client:
            return "대화 내용을 요약하기 위한 AI 모델이 준비되지 않았습니다. 관리자에게 문의하세요."

        # GPT에 전달할 대화 내용 형식화 (간단하게)
        conversation_text = ""
        for log in chat_logs:
            speaker = "AI" if log.get("role") == "AI" else f"사용자 {log.get('user_id', '알 수 없음')}"
            conversation_text += f"{speaker}: {log['content']}\n"
        
        if not conversation_text.strip():
            return "요약할 대화 내용이 없습니다."

        prompt = f"""
        다음은 '{session_topic_display}' 주제로 진행된 커플 상담 대화 내용입니다.
        이 대화의 핵심 내용을 간결하게 요약해주세요.
        사용자들이 어떤 이야기를 나누었고, 어떤 감정을 표현했는지, 그리고 대화의 전반적인 흐름이 어떠했는지 중심으로 요약합니다.
        AI 상담사에 대한 내용은 언급하지 않습니다.
        사용자의 이름은 언급하지 않고 한명, 다른 한 명으로 표현해주세요.
        분량은 2-3문장으로 작성해주세요.

        <대화 내용>
        {conversation_text}
        </대화 내용>

        요약:
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo", # 또는 "gpt-4" 등 사용 가능한 모델
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200, # 요약 길이에 맞게 조절
                temperature=0.5, # 요약의 창의성 조절
            )
            summary = response.choices[0].message.content.strip()
            return summary if summary else "대화 내용 요약에 실패했습니다."
        except Exception as e:
            print(f"[ReportFormatter_ERROR] GPT 요약 생성 중 오류 발생: {e}")
            return "GPT 모델 호출 중 오류가 발생하여 대화 내용을 요약할 수 없습니다."

    async def generate_report(self, chat_logs: List[Dict]) -> str:
        """
        채팅 로그를 기반으로 GPT 요약을 포함한 리포트 메시지를 생성합니다.
        
        Args:
            chat_logs (List[Dict]): {"user_id": str, "content": str, "timestamp": str, "role": str, "session_id": int, "topic": str}
        
        Returns:
            str: 포맷된 리포트 메시지 (요약 위주)
        """
        report_lines = []
        report_lines.append("📄 <AI 커플상담사 세션 리포트>")
        
        if not chat_logs:
            report_lines.append("해당 세션의 대화 기록이 없어 리포트를 생성할 수 없습니다.")
            return " ".join(report_lines)

        # 모든 로그가 동일한 세션 ID와 토픽을 가진다고 가정 (세션별 리포트이므로)
        # 실제로는 _send_session_report에서 특정 세션의 로그만 필터링해서 chat_logs로 전달됨
        session_id_for_report = chat_logs[0].get("session_id", "알 수 없는")
        session_topic_for_report = chat_logs[0].get("topic", "")
        
        topic_name_display = "상황" if "situation" in session_topic_for_report else "감정"
        if not session_topic_for_report: # 혹시 topic 정보가 없을 경우
            topic_name_display = "현재"

        # GPT를 사용한 요약 생성
        summary = await self._summarize_chat_logs_with_gpt(chat_logs, topic_name_display)
        report_lines.append(f"💡 {topic_name_display} 대화 요약:\n{summary}")

        return "\n".join(report_lines)