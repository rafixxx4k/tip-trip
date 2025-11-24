from pydantic import BaseModel
from typing import Optional


class UserTripCreate(BaseModel):
    user_hash: str
    user_name: str


class UserTripRead(BaseModel):
    id: int
    user_id: int
    trip_id: int
    user_name: str

    class Config:
        orm_mode = True
