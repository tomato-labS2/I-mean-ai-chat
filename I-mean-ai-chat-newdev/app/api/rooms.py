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
    room_name: str
    couple_id: int

class RoomResponse(BaseModel):
    room_id: int
    room_name: str
    couple_id: int
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=RoomResponse)
async def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 커플 관계 확인 (현재 사용자가 해당 커플에 속해있는지 확인)
    couple = db.query(Couple).filter(
        Couple.couple_id == room.couple_id,
        (Couple.user_a_id == current_user.user_id) | (Couple.user_b_id == current_user.user_id),
        Couple.is_active == True
    ).first()
    
    if not couple:  # 커플이 없으면 에러 반환
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="커플 관계가 아니거나 권한이 없습니다"
        )
    
    # 이미 존재하는 채팅방 확인 (같은 커플, 같은 이름의 방이 있는지)
    existing_room = db.query(Room).filter(
        Room.couple_id == room.couple_id,
        Room.room_name == room.room_name
    ).first()
    
    if existing_room:  # 이미 있으면 에러 반환
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 채팅방입니다"
        )
    
    db_room = Room(
        room_name=room.room_name,  # 방 이름 저장
        couple_id=room.couple_id  # 커플 ID 저장
    )
    db.add(db_room)  # DB에 추가
    db.commit()  # 변경사항 저장
    db.refresh(db_room)  # 새로 생성된 방의 정보를 다시 읽어옴
    return db_room  # 생성된 방 정보 반환

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