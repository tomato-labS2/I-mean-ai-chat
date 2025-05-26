from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.schemas import ReportRequest, ReportResponse
from app.services.report_service import (
    parse_report,
    save_report_to_db,
    get_report_by_session_id,
    get_reports_by_room_id,
    get_report_by_id,
    generate_pdf_report
)

router = APIRouter()


@router.post("/generate", response_model=ReportResponse)
async def generate_report(request: ReportRequest, db: Session = Depends(get_db)):
    """
    GPT 응답을 파싱하여 리포트를 생성하고 데이터베이스에 저장합니다.

    Args:
        request (ReportRequest): 리포트 생성 요청 데이터
        db (Session): 데이터베이스 세션

    Returns:
        ReportResponse: 생성된 리포트 데이터
    
    Raises:
        HTTPException: 리포트 생성 또는 저장 중 오류 발생 시
    """
    try:
        # GPT 응답 파싱
        parsed_report = parse_report(request.report_text)

        # 데이터베이스에 저장
        report = save_report_to_db(
            session_id=request.session_id,
            room_id=request.room_id,
            parsed_report=parsed_report,
            db_session=db
        )

        # 리포트 응답 반환
        return ReportResponse(
            id=report.id,
            situation_summary=report.situation_summary,
            emotion_type=report.emotion_type,
            communication_pattern=report.communication_pattern,
            improvement_suggestions=report.improvement_suggestions,
            counseling_recommended=report.counseling_recommended,
            created_at=report.created_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"리포트 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{session_id}", response_model=ReportResponse)
async def get_report(session_id: int, db: Session = Depends(get_db)):
    """
    특정 세션에 대한 GPT 리포트를 조회합니다. (마이페이지용)

    Args:
        session_id (int): 조회할 세션 ID
        db (Session): 데이터베이스 세션

    Returns:
        ReportResponse: 해당 세션의 리포트 데이터

    Raises:
        HTTPException: 리포트가 존재하지 않거나 조회 중 오류 발생 시
    """
    try:
        report = get_report_by_session_id(session_id, db)
        if not report:
            raise HTTPException(status_code=404, detail="해당 세션의 리포트를 찾을 수 없습니다.")

        return ReportResponse(
            id=report.id,
            situation_summary=report.situation_summary,
            emotion_type=report.emotion_type,
            communication_pattern=report.communication_pattern,
            improvement_suggestions=report.improvement_suggestions,
            counseling_recommended=report.counseling_recommended,
            created_at=report.created_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"리포트 조회 중 오류 발생: {str(e)}")


@router.get("/room/{room_id}", response_model=List[ReportResponse])
async def get_room_reports(room_id: int, db: Session = Depends(get_db)):
    """
    특정 채팅방의 모든 리포트를 조회합니다.

    Args:
        room_id (int): 채팅방 ID
        db (Session): 데이터베이스 세션

    Returns:
        List[ReportResponse]: 리포트 목록
    """
    try:
        # 서비스 계층에서 리포트 목록 조회
        reports = get_reports_by_room_id(room_id, db)
        
        # 각 리포트를 ReportResponse 모델로 변환
        return [
            ReportResponse(
                id=report.id,
                situation_summary=report.situation_summary,
                emotion_type=report.emotion_type,
                communication_pattern=report.communication_pattern,
                improvement_suggestions=report.improvement_suggestions,
                counseling_recommended=report.counseling_recommended,
                created_at=report.created_at
            )
            for report in reports
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"리포트 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{report_id}/download")
async def download_report_pdf(report_id: int, db: Session = Depends(get_db)):
    """
    특정 리포트를 PDF 형식으로 다운로드합니다.

    Args:
        report_id (int): 리포트 ID
        db (Session): 데이터베이스 세션

    Returns:
        StreamingResponse: PDF 파일 스트림
    
    Raises:
        HTTPException: 리포트가 존재하지 않거나 PDF 생성 중 오류 발생 시
    """
    try:
        # 리포트 조회
        report = get_report_by_id(report_id, db)
        if not report:
            raise HTTPException(
                status_code=404,
                detail="리포트를 찾을 수 없습니다."
            )
        
        # PDF 생성
        pdf_buffer = generate_pdf_report(report)
        
        # 파일명 설정
        filename = f"report_{report_id}_{report.created_at.strftime('%Y%m%d')}.pdf"
        
        # PDF 스트리밍 응답 반환
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF 생성 중 오류가 발생했습니다: {str(e)}"
        )
