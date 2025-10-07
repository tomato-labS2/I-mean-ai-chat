from sqlalchemy import Column, Integer, String
from app.models.base import Base

class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    room_name = Column(String(255), nullable=False)