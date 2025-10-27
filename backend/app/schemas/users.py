from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    # Clients only provide a name; user_id and token are generated server-side.
    name: str


class UserRead(BaseModel):
    id: int
    user_id: str
    token: str
    name: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
