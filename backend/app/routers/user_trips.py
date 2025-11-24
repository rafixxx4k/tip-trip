from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from app.db.session import get_db
from app.models.user import User
from app.models.trip import Trip
from app.models.user_trip import UserTrip
from app.models.trip_date import TripDate
from app.models.user_availability import UserAvailability
from app.schemas.user_trips import UserTripCreate, UserTripRead

router = APIRouter()


def get_user_by_token(db: Session, token: str):
    return db.query(User).filter(User.token == token).first()


def get_authenticated_user(x_user_hash: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    if not x_user_hash:
        raise HTTPException(status_code=401, detail="X-User-Hash header missing")
    user = get_user_by_token(db, x_user_hash)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user hash")
    return user


@router.get("/trips/{hash_id}/members", response_model=List[UserTripRead])
def list_members(hash_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_authenticated_user)):
    trip = db.query(Trip).filter(Trip.hash_id == hash_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    rows = db.query(UserTrip).filter(UserTrip.trip_id == trip.id).all()
    return rows


@router.post("/trips/{hash_id}/members", response_model=UserTripRead)
def add_member(hash_id: str, payload: UserTripCreate, db: Session = Depends(get_db), current_user: User = Depends(get_authenticated_user)):
    trip = db.query(Trip).filter(Trip.hash_id == hash_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    user = get_user_by_token(db, payload.user_hash)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Allow anyone to add themselves if they present their own user_hash (i.e. they are the caller).
    # Adding other users still requires the caller to be a member of the trip.
    adding_self = payload.user_hash == current_user.token
    if not adding_self:
        caller_membership = db.query(UserTrip).filter(UserTrip.trip_id == trip.id, UserTrip.user_id == current_user.id).first()
        if not caller_membership:
            raise HTTPException(status_code=403, detail="Only trip members may add other members")

    # create membership with optional nickname
    membership = UserTrip(user_id=user.id, trip_id=trip.id, user_name=payload.user_name)
    db.add(membership)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="User is already a member of the trip")
    db.refresh(membership)
    # After adding membership, ensure availability rows exist for this user for all trip dates
    try:
        trip_dates = db.query(TripDate).filter(TripDate.trip_id == trip.id).all()
        for td in trip_dates:
            exists = db.query(UserAvailability).filter(UserAvailability.trip_date_id == td.id, UserAvailability.user_id == user.id).first()
            if not exists:
                ua = UserAvailability(trip_date_id=td.id, user_id=user.id, status='unset')
                db.add(ua)
        db.commit()
    except Exception:
        db.rollback()
        # do not fail the membership creation if availability setup fails
    return membership


@router.delete("/trips/{hash_id}/members/{user_id}")
def remove_member(hash_id: str, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_authenticated_user)):
    trip = db.query(Trip).filter(Trip.hash_id == hash_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    membership = db.query(UserTrip).filter(UserTrip.trip_id == trip.id, UserTrip.user_id == user_id).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    # With owner flag removed only the user themself may remove their membership.
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Only the user themself may remove their membership")

    db.delete(membership)
    db.commit()
    return {"status": "deleted"}


@router.put("/trips/{hash_id}/members/{user_id}", response_model=UserTripRead)
def update_member(hash_id: str, user_id: int, payload: UserTripCreate, db: Session = Depends(get_db), current_user: User = Depends(get_authenticated_user)):
    trip = db.query(Trip).filter(Trip.hash_id == hash_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    membership = db.query(UserTrip).filter(UserTrip.trip_id == trip.id, UserTrip.user_id == user_id).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    # Users may update their own nickname; only allow that.
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Only the user themself may modify their membership")

    membership.user_name = payload.user_name
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership
