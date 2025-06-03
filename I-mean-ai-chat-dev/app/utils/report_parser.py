
import re

def extract_section(text: str, section_title: str) -> str:
    pattern = rf"{section_title}[:：]\s*(.*?)(?=\n\d+\.\s|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

def parse_report(gpt_response: str) -> dict:
    return {
        "situation_summary": extract_section(gpt_response, "대화 상황 요약"),
        "emotion_summary": extract_section(gpt_response, "감정 표현 유형"),
        "communication_pattern": extract_section(gpt_response, "소통 패턴"),
        "recommendations": extract_section(gpt_response, "개선 방안"),
        "suggest_counseling": "추천" in extract_section(gpt_response, "상담 추천 여부"),
    }
