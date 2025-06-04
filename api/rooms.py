from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from ..db_connect import get_db
from ..models.models import Room, User, Couple
from .auth import get_current_user

router = APIRouter()

class RoomCreate(BaseModel):
    name: str
    couple_id: int

class RoomResponse(BaseModel):
    room_id: int
    room_name: str
    couple_id: int
    created_at: datetime
    is_existing: bool

    class Config:
        from_attributes = True

@router.post("/", response_model=RoomResponse)
async def create_room(
    room_create_request: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 커플 관계 확인 (현재 사용자가 해당 커플에 속해있는지 확인)
    couple = db.query(Couple).filter(
        Couple.couple_id == room_create_request.couple_id,
        (Couple.user_a_id == current_user.user_id) | (Couple.user_b_id == current_user.user_id),
        Couple.is_active == True
    ).first()
    
    if not couple:  # 커플이 없으면 에러 반환
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="커플 관계가 아니거나 권한이 없습니다"
        )
    
    # 해당 couple_id와 is_active=True 조건으로 기존 채팅방 확인
    existing_room = db.query(Room).filter(
        Room.couple_id == room_create_request.couple_id,
        Room.is_active == True  # 활성화된 방만 찾도록 조건 추가
    ).first()
    
    if existing_room:
        is_existing = True
        final_room_for_response = existing_room

        if existing_room.room_name != room_create_request.name:
            existing_room.room_name = room_create_request.name
            # existing_room은 이미 세션에 의해 관리되므로 db.add()는 불필요합니다.
            db.commit()
            # 변경사항 커밋 후, DB에서 최신 상태의 방 정보를 다시 조회합니다.
            # .one()은 결과가 정확히 하나일 것을 기대하며, 없거나 많으면 예외를 발생시킵니다.
            try:
                final_room_for_response = db.query(Room).filter(Room.room_id == existing_room.room_id).one()
            except Exception as e:
                # 만약 방을 찾지 못하거나 다른 DB 오류 발생 시, 롤백하고 에러를 발생시킵니다.
                db.rollback()
                raise HTTPException(status_code=500, detail=f"채팅방 업데이트 후 조회 중 오류 발생: {str(e)}")
        
        return RoomResponse(
            room_id=final_room_for_response.room_id,
            room_name=final_room_for_response.room_name, # 새로 조회된 (또는 기존) 방의 이름을 사용
            couple_id=final_room_for_response.couple_id,
            created_at=final_room_for_response.created_at,
            is_existing=True # 이 블록에서는 항상 True
        )
    else:
        is_existing = False
        # 새 방 생성
        db_room = Room(
            room_name=room_create_request.name,
            couple_id=room_create_request.couple_id,
            is_active=True  # is_active=True 명시적으로 설정
        )
        db.add(db_room)
        db.commit()
        db.refresh(db_room)
        # RoomResponse 모델에 맞게 반환 객체 생성
        return RoomResponse(
            room_id=db_room.room_id,
            room_name=db_room.room_name,
            couple_id=db_room.couple_id,
            created_at=db_room.created_at,
            is_existing=is_existing
        )

@router.get("/", response_model=List[RoomResponse])
async def get_user_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 사용자가 속한 커플 관계의 채팅방 목록 조회
    rooms = db.query(Room).join(
        Couple,
        Room.couple_id == Couple.couple_id
    ).filter(
        (Couple.user_a_id == current_user.user_id) | (Couple.user_b_id == current_user.user_id),
        Couple.is_active == True
    ).all()
    
    return rooms  # 채팅방 목록 반환

@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 해당 room_id의 방이 현재 사용자의 커플에 속하는지 확인
    room = db.query(Room).join(
        Couple,
        Room.couple_id == Couple.couple_id
    ).filter(
        Room.room_id == room_id,
        (Couple.user_a_id == current_user.user_id) | (Couple.user_b_id == current_user.user_id),
        Couple.is_active == True
    ).first()
    
    if not room:  # 방이 없으면 에러 반환
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="채팅방을 찾을 수 없습니다"
        )
    
    return room  # 방 정보 반환

# 신규 API: GET /api/rooms/couple/{coupleId}
@router.get("/couple/{couple_id}", response_model=RoomResponse)
async def get_room_by_couple_id(
    couple_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    print(f"get_room_by_couple_id 호출")
    # 현재 사용자가 해당 couple_id에 접근 권한이 있는지 확인 (커플의 멤버인지)
    couple_membership = db.query(Couple).filter(
        Couple.couple_id == couple_id,
        (Couple.user_a_id == current_user.user_id) | (Couple.user_b_id == current_user.user_id),
        Couple.is_active == True
    ).first()
    print(f"couple_membership: {couple_membership}")
    if not couple_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 커플의 채팅방에 접근할 권한이 없습니다."
        )

    print(f"couple_id: {couple_id}")
    # 활성화된 방만 조회하도록 조건을 Room.is_active == 1 로 명시적 지정
    room = db.query(Room).filter(
        Room.couple_id == couple_id,
        Room.is_active == 1  # True 대신 1로 변경하여 DB의 정수 값과 직접 비교
    ).first()
    print(f"room: {room}")
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 커플의 채팅방을 찾을 수 없습니다."
        )
    print(f"room: {room}")
    # 방이 존재하므로 RoomResponse로 반환, is_existing는 True로 설정
    return RoomResponse(
        room_id=room.room_id,
        room_name=room.room_name,
        couple_id=room.couple_id,
        created_at=room.created_at,
        is_existing=True # 이 API에서는 방이 존재할 때만 200 응답을 주므로 항상 True
    ) 