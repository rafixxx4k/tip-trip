from pydantic import BaseModel
from typing import Optional


class TripCreate(BaseModel):
    title: str
    description: Optional[str] = None
    # owner_id is no longer provided by clients; owner is determined from
    # the client's user hash sent in the request header.


class TripUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None


class TripRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    owner_id: Optional[int]
    hash_id: str

    class Config:
        orm_mode = True
