from datetime import datetime
from pydantic import BaseModel


class ReportRequest(BaseModel):
    report_text: str


class ReportResponse(BaseModel):
    id: int
    situation_summary: str
    emotion_type: str
    communication_pattern: str
    improvement_suggestions: str
    counseling_recommended: bool
    created_at: datetime

    class Config:
        from_attributes = True
