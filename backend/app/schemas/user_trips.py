from pydantic import BaseModel
from typing import Optional


class UserTripCreate(BaseModel):
    user_hash: str
    is_owner: Optional[bool] = False


class UserTripRead(BaseModel):
    id: int
    user_id: int
    trip_id: int
    is_owner: bool

    class Config:
        orm_mode = True
