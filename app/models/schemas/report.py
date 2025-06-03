from pydantic import BaseModel
from datetime import datetime

class ReportResponse(BaseModel):
    id: int
    room_id: int
    session_id: int
    situation_summary: str
    emotion_summary: str
    communication_pattern: str
    recommendations: str
    suggest_counseling: bool
    report_generated: bool
    report_generated_at: datetime

    class Config:
        orm_mode = True
