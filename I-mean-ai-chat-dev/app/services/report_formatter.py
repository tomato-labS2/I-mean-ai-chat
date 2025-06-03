# app/services/report_formatter.py

from typing import List, Dict
from datetime import datetime

class ReportFormatter:
    @staticmethod
    def generate_report(chat_logs: List[Dict]) -> str:
        """
        채팅 로그를 기반으로 리포트 메시지를 생성합니다.
        
        Args:
            chat_logs (List[Dict]): {"user_id": str, "content": str, "timestamp": str, "role": str, "session_id": int}
        
        Returns:
            str: 포맷된 리포트 메시지
        """
        report_lines = []
        report_lines.append("📄 <AI 커플상담사 리포트>\n")
        report_lines.append(f"총 대화 수: {len(chat_logs)}회\n")
        
        sessions = {}
        for log in chat_logs:
            sessions.setdefault(log["session_id"], []).append(log)

        for session_id, logs in sessions.items():
            topic_name = "상황" if "situation" in logs[0].get("topic", "") else "감정"
            report_lines.append(f"\n🧩 세션 {session_id} ({topic_name} 주제):\n")

            for entry in logs:
                timestamp = datetime.fromisoformat(entry["timestamp"]).strftime('%H:%M:%S')
                speaker = "🤖AI" if entry["role"] == "AI" else f"👤사용자 {entry['user_id']}"
                content = entry["content"]
                report_lines.append(f"[{timestamp}] {speaker}: {content}")

        report_lines.append("\n\n💡 요약: 이번 대화를 통해 두 분은 각자의 시각에서 상황과 감정을 공유하고 이해하는 시간을 가졌습니다.\n")
        report_lines.append("🔚 대화가 종료되었습니다. 다음에도 도움이 필요하면 언제든 찾아주세요.")

        return "\n".join(report_lines)