from fastapi import APIRouter, Depends, HTTPException # Header 제거
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# from typing import Optional # Optional 제거 또는 필요시 유지
from pydantic import BaseModel

from ..database import get_db
from ..models.chat import Room
# from ..security import verify_token # verify_token import 삭제

router = APIRouter()

class CreateRoomRequest(BaseModel):
    room_name: str
    couple_id: int
    user_id: int # str에서 int로 변경

    class Config:
        json_schema_extra = {
            "example": {
                "room_name": "테스트 채팅방",
                "couple_id": 1,
                "user_id": 123 # 문자열에서 숫자로 변경
            }
        }

@router.post("/api/rooms", tags=["Rooms"])
async def create_room(
    request_data: CreateRoomRequest,
    # authorization: Optional[str] = Header(None), # Authorization 헤더 파라미터 제거
    db: AsyncSession = Depends(get_db)
):
    print("create_room 호출")
    """새로운 채팅방을 생성하거나 기존 채팅방을 찾습니다. 프론트엔드 서버로부터 사용자 ID를 전달받습니다."""
    try:
        # 프론트엔드 서버가 user_id를 검증하고 전달한다고 가정
        if not request_data.user_id:
            raise HTTPException(status_code=400, detail="User ID is missing in the request from frontend server")
        
        print(f"Received request to create/join room for user_id: {request_data.user_id} from frontend server.")

        # 기존의 JWT 검증 로직 삭제
        # if not authorization:
        #     raise HTTPException(status_code=401, detail="Authorization header is missing")
        # payload = await verify_token(authorization) 
        # print(f"Token payload: {payload}")
        # actual_user_id = str(payload.get("sub")) # 이 부분 대신 request_data.user_id 사용
        # if not actual_user_id:
        #     raise HTTPException(status_code=401, detail="Invalid token: missing user_id")
        
        if not request_data.room_name:
            raise HTTPException(status_code=400, detail="Room name is required")
        if not request_data.couple_id:
            raise HTTPException(status_code=400, detail="Couple ID is required")
        
        query = select(Room).where(
            Room.couple_id == request_data.couple_id,
            Room.is_active == True
        ).order_by(Room.created_at.desc())
        result = await db.execute(query)
        existing_room = result.scalar_one_or_none()
        
        if existing_room:
            print(f"Found existing room for couple {request_data.couple_id} (requested by user {request_data.user_id}): {existing_room.room_id}")
            return {
                "room_id": existing_room.room_id,
                "room_name": existing_room.room_name,
                "couple_id": existing_room.couple_id,
                "created_at": existing_room.created_at,
                "is_existing": True
            }
        
        room = Room(
            room_name=request_data.room_name,
            couple_id=request_data.couple_id,
            is_active=True
            # created_by_user_id=request_data.user_id # Room 모델에 해당 필드가 있다면 추가 가능
        )
        db.add(room)
        await db.commit()
        await db.refresh(room)
        
        print(f"Created new room for couple {request_data.couple_id} (requested by user {request_data.user_id}): {room.room_id}")
        return {
            "room_id": room.room_id,
            "room_name": room.room_name,
            "couple_id": room.couple_id,
            "created_at": room.created_at,
            "is_existing": False
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Room creation error for user {request_data.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 