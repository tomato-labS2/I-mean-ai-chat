from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fpdf import FPDF
from io import BytesIO
from app.models.report_model import Report
import os


def extract_section(text: str, section_title: str) -> Optional[str]:
    """
    GPT 응답에서 특정 섹션의 내용을 추출합니다.
    """
    try:
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if section_title in line and ':' in line:
                content = line.split(':', 1)[1].strip()
                j = i + 1
                while j < len(lines) and (lines[j].strip().startswith('-') or lines[j].strip() == ''):
                    content_line = lines[j].strip()
                    if content_line and not content_line.startswith('-'):
                        content += ' ' + content_line
                    j += 1
                return content
        return None
    except Exception as e:
        print(f"섹션 추출 중 오류 발생: {str(e)}")
        return None


def parse_report(gpt_response: str) -> dict:
    """
    GPT 응답을 파싱하여 구조화된 리포트 데이터로 변환합니다.
    """
    try:
        parsed_data = {
            "situation_summary": extract_section(gpt_response, "상황 요약") or "",
            "emotion_type": extract_section(gpt_response, "감정 표현 유형") or "",
            "communication_pattern": extract_section(gpt_response, "소통 패턴") or "",
            "improvement_suggestions": extract_section(gpt_response, "개선 방안") or "",
            "counseling_recommended": "추천" in (extract_section(gpt_response, "상담 추천") or "")
        }

        if not all([
            parsed_data["situation_summary"],
            parsed_data["emotion_type"],
            parsed_data["communication_pattern"],
            parsed_data["improvement_suggestions"]
        ]):
            raise ValueError("필수 필드가 누락되었습니다.")

        return parsed_data

    except Exception as e:
        raise Exception(f"리포트 파싱 중 오류 발생: {str(e)}")


def save_report_to_db(session_id: int, room_id: int, parsed_report: dict, db_session: Session) -> Report:
    """
    파싱된 리포트 데이터를 데이터베이스에 저장합니다.
    """
    try:
        report = Report(
            session_id=session_id,
            room_id=room_id,
            situation_summary=parsed_report["situation_summary"],
            emotion_type=parsed_report["emotion_type"],
            communication_pattern=parsed_report["communication_pattern"],
            improvement_suggestions=parsed_report["improvement_suggestions"],
            counseling_recommended=parsed_report["counseling_recommended"],
            created_at=datetime.utcnow()
        )

        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)

        return report

    except Exception as e:
        db_session.rollback()
        raise Exception(f"리포트 저장 중 오류 발생: {str(e)}")


def get_report_by_session_id(session_id: int, db_session: Session) -> Optional[Report]:
    """
    특정 세션 ID로 리포트를 조회합니다.
    """
    return db_session.query(Report).filter(Report.session_id == session_id).first()


def get_reports_by_room_id(room_id: int, db_session: Session) -> list[Report]:
    """
    특정 채팅방의 모든 리포트를 조회합니다.
    """
    try:
        reports = db_session.query(Report)\
            .filter(Report.room_id == room_id)\
            .order_by(Report.created_at.desc())\
            .all()
        return reports
    except Exception as e:
        raise Exception(f"리포트 조회 중 오류 발생: {str(e)}")


def generate_pdf_report(report: Report) -> BytesIO:
    """
    리포트 데이터를 기반으로 PDF 파일을 생성합니다.
    """
    pdf = FPDF()
    pdf.add_page()

    font_path = os.path.join("app", "fonts", "NanumGothic.ttf")
    pdf.add_font("Nanum", '', font_path, uni=True)  # ✅ 수정: 등록명과 일치

    pdf.set_font('Nanum', size=20)  # ✅ 수정됨
    pdf.cell(0, 20, '감정 분석 리포트', ln=True, align='C')
    pdf.ln(10)

    pdf.set_font('Nanum', size=12)

    sections = [
        ('상황 요약', report.situation_summary),
        ('감정 표현 유형', report.emotion_type),
        ('소통 패턴', report.communication_pattern),
        ('개선 방안', report.improvement_suggestions),
        ('상담 추천', '추천' if report.counseling_recommended else '불필요')
    ]

    for title, content in sections:
        pdf.set_font('Nanum', size=14)
        pdf.cell(0, 10, f'■ {title}', ln=True)
        pdf.ln(5)

        pdf.set_font('Nanum', size=12)
        pdf.multi_cell(0, 10, content)
        pdf.ln(10)

    pdf.set_font('Nanum', size=10)
    pdf.cell(0, 10, f'생성일시: {report.created_at.strftime("%Y-%m-%d %H:%M:%S")}', ln=True, align='R')

    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer


def get_report_by_id(report_id: int, db_session: Session) -> Optional[Report]:
    """
    ID로 리포트를 조회합니다.
    """
    return db_session.query(Report).filter(Report.id == report_id).first()
