from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.report import Report
from ..models.schemas.report import ReportResponse

router = APIRouter(
    prefix='/reports',
    tags=["Report"]
)

@router.get("/room/{room_id}", response_model=ReportResponse)
async def get_report_by_room(room_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Report)
        .where(Report.room_id == room_id)
        .order_by(Report.report_generated_at.desc())
    )
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="리포트가 없습니다.")
    return report  
