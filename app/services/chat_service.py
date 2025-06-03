from app.services.gpt_service import generate_report_from_gpt
from app.utils.parse_report import parse_report, save_report_to_db

async def end_chat_and_generate_report(room_id, db, ended_emotion_session):
    chat_logs = await get_all_logs_by_room(room_id, db)  # SELECT * FROM logs WHERE room_id=...
    gpt_response = await generate_report_from_gpt(chat_logs)  # GPT 호출하여 리포트 생성
    parsed_data = parse_report(gpt_response)  # GPT 응답 파싱
    await save_report_to_db(session_id=ended_emotion_session.session_id, room_id=room_id, parsed_report=parsed_data, db=db)
