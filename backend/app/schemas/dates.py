from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class TripDateRead(BaseModel):
    id: int
    date: date

    class Config:
        from_attributes = True


class AvailabilityUpdate(BaseModel):
    date: date
    status: str


class BulkAvailabilityUpdate(BaseModel):
    updates: List[AvailabilityUpdate]


class CalendarResponse(BaseModel):
    dates: List[str]
    users: List[dict]
    availability: dict
