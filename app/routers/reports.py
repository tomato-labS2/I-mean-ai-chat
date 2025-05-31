# app/routers/report.py
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ReportRequest(BaseModel):
    room_id: str

@router.post("/gpt/generate")
async def generate_gpt_report(request: ReportRequest):
    return {"message": f"{request.room_id} GPT 리포트 생성 완료!"}
