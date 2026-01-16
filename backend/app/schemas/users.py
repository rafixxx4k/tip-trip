from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserRead(BaseModel):
    id: int
    user_id: str
    token: str
    created_at: datetime

    class Config:
        from_attributes = True
