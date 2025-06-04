from fastapi import APIRouter, Depends, HTTPException # Header 제거
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# from typing import Optional # Optional 제거 또는 필요시 유지
from pydantic import BaseModel
from datetime import datetime # datetime 추가

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

# Room 정보를 반환하기 위한 Pydantic 모델
class RoomResponseModel(BaseModel):
    room_id: int
    room_name: str
    couple_id: int
    created_at: datetime
    is_existing: bool

    class Config:
        from_attributes = True

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

@router.get("/api/rooms/couple/{couple_id}", response_model=RoomResponseModel, tags=["Rooms"])
async def get_room_by_couple_id(
    couple_id: int,
    db: AsyncSession = Depends(get_db)
    # 현재 create_room과 마찬가지로 JWT 토큰 인증은 생략된 상태입니다.
    # 필요하다면 사용자 인증 로직을 추가해야 합니다.
):
    print(f"GET /api/rooms/couple/{couple_id} 호출됨")

    # User 인증/권한 검증 로직 (현재 생략. 필요시 추가)
    # 예: couple_membership 확인 등

    query = select(Room).where(
        Room.couple_id == couple_id,
        Room.is_active == True  # 활성화된 방만 조회
    )
    result = await db.execute(query)
    room = result.scalar_one_or_none()

    if not room:
        print(f"Couple ID {couple_id}에 해당하는 활성화된 방을 찾을 수 없습니다.")
        raise HTTPException(
            status_code=404,
            detail="해당 커플의 채팅방을 찾을 수 없습니다."
        )
    
    print(f"Couple ID {couple_id}에 대한 방 찾음: {room.room_id}, 이름: {room.room_name}")
    # Room 모델에 created_at 필드가 datetime 타입으로 존재한다고 가정합니다.
    return RoomResponseModel(
        room_id=room.room_id,
        room_name=room.room_name,
        couple_id=room.couple_id,
        created_at=room.created_at, # Room 모델에 created_at이 있어야 함
        is_existing=True # 이 API는 방이 존재할 때만 200 응답
    ) 