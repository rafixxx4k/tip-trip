from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class TripCreate(BaseModel):
    title: str
    user_name: str
    description: Optional[str] = None
    # owner_id is no longer provided by clients; owner is determined from
    # the client's user hash sent in the request header.


class TripUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    allowed_weekdays: Optional[List[int]] = None
    # owner_id removed; updates are allowed for members (permission checked in router)


class TripRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    hash_id: str
    date_start: Optional[date]
    date_end: Optional[date]
    allowed_weekdays: Optional[List[int]]

    class Config:
        orm_mode = True
