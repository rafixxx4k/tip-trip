from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import uuid

from app.db.session import get_db
from app.schemas.users import UserCreate, UserRead
from app.models.user import User

router = APIRouter()


@router.get("/users", response_model=List[UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


def _gen_unique_user_fields(db: Session):
    # generate unique user_id (short) and token (longer)
    for _ in range(5):
        user_id = uuid.uuid4().hex[:8]
        token = uuid.uuid4().hex
        exists = db.query(User).filter((User.user_id == user_id) | (User.token == token)).first()
        if not exists:
            return user_id, token
    # fallback to guaranteed unique tokens
    return uuid.uuid4().hex[:8], uuid.uuid4().hex


@router.post("/users", response_model=UserRead)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Clients send only `name`; generate user_id and token server-side
    user_id, token = _gen_unique_user_fields(db)
    user = User(user_id=user_id, token=token, name=payload.name)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not create user due to DB error")
    db.refresh(user)
    return user
