from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DebtorCreate(BaseModel):
    userId: str
    shareType: str = "equal"  # equal, percent, amount
    value: float


class ExpenseCreate(BaseModel):
    amount: float
    description: str
    currency: str = "USD"
    debtors: List[DebtorCreate]


class DebtorRead(BaseModel):
    userId: str
    shareType: str
    value: float


class ExpenseRead(BaseModel):
    id: str
    tripId: str
    payerId: str
    amount: float
    currency: str
    description: str
    debtors: List[DebtorRead]
    createdAt: datetime

    class Config:
        from_attributes = True


class SettlementRead(BaseModel):
    fromUser: str
    toUser: str
    amount: float
    currency: str


class SettlementsResponse(BaseModel):
    balances: List[SettlementRead]
