from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.models.trip import Trip
from app.models.user_trip import UserTrip
from app.models.user import User
from app.schemas.trips import TripCreate, TripRead, TripUpdate
from app.models.trip_date import TripDate
from datetime import timedelta, datetime

router = APIRouter()


def _generate_hash(db: Session) -> str:
    # generate a short unique hash_id (hex) and ensure uniqueness
    for _ in range(5):
        h = uuid.uuid4().hex[:12]
        exists = db.query(Trip).filter(Trip.hash_id == h).first()
        if not exists:
            return h
    # fallback to full uuid if collisions occur
    return uuid.uuid4().hex


def get_authenticated_user(x_user_hash: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """Dependency that authenticates a request using X-User-Hash header (user token).

    The header value must match a `User.token` in the DB. Raises 401 if missing/invalid.
    """
    if not x_user_hash:
        raise HTTPException(status_code=401, detail="X-User-Hash header missing")
    user = db.query(User).filter(User.token == x_user_hash).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user hash")
    return user


@router.post("/trips", response_model=TripRead)
def create_trip(payload: TripCreate, db: Session = Depends(get_db), current_user: User = Depends(get_authenticated_user)):
    """Create a trip. The owner is taken from the authenticated user (X-User-Hash).

    Clients must send header: X-User-Hash: <their token/hash>
    """
    hash_id = _generate_hash(db)
    trip = Trip(title=payload.title, description=payload.description, hash_id=hash_id)
    # optional initial dates provided by clients are not part of TripCreate currently;
    # if you want creation to accept dates, extend TripCreate accordingly.
    db.add(trip)
    try:
        # flush so trip.id is available for the association
        db.flush()
        # create a membership for the creator; nickname can be provided later via membership update
        membership = UserTrip(user_id=current_user.id, trip_id=trip.id, user_name=payload.user_name)
        db.add(membership)
        db.commit()
    except IntegrityError:
        db.rollback()
        # rare collision on hash or FK issue
        raise HTTPException(status_code=500, detail="Could not create trip due to DB error")
    db.refresh(trip)
    return trip


@router.get("/trips/{hash_id}", response_model=TripRead)
def get_trip(hash_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_authenticated_user)):
    """Get a trip by hash. Request must include X-User-Hash header for auditing/authentication.
    """
    trip = db.query(Trip).filter(Trip.hash_id == hash_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    # include date fields — Pydantic will read them from the ORM model
    return trip


@router.get("/trips", response_model=List[TripRead])
def list_my_trips(db: Session = Depends(get_db), current_user: User = Depends(get_authenticated_user)):
    """Return trips where the authenticated user is owner or a member.

    Requires X-User-Hash header.
    """
    # Join against user_trips to find memberships (owner field removed)
    trips = db.query(Trip).join(UserTrip, UserTrip.trip_id == Trip.id).filter(UserTrip.user_id == current_user.id).all()
    return trips


@router.put("/trips/{hash_id}", response_model=TripRead)
def update_trip(hash_id: str, payload: TripUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_authenticated_user)):
    """Update a trip. Only the trip owner (authenticated) may update the trip."""
    trip = db.query(Trip).filter(Trip.hash_id == hash_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # owner_id/is_owner removed; allow updates only for members of the trip
    membership = db.query(UserTrip).filter(UserTrip.trip_id == trip.id, UserTrip.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not authorized to update this trip")

    # capture original date-range values to detect changes
    orig_start = getattr(trip, 'date_start', None)
    orig_end = getattr(trip, 'date_end', None)
    orig_weekdays = getattr(trip, 'allowed_weekdays', None)

    if payload.title is not None:
        trip.title = payload.title
    if payload.description is not None:
        trip.description = payload.description

    # apply date-range updates if provided
    updated_dates = False
    if payload.date_start is not None:
        trip.date_start = payload.date_start
        updated_dates = True
    if payload.date_end is not None:
        trip.date_end = payload.date_end
        updated_dates = True
    if payload.allowed_weekdays is not None:
        trip.allowed_weekdays = payload.allowed_weekdays
        updated_dates = True

    try:
        # commit basic trip changes first so trip.id is stable
        db.add(trip)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid update or constraint violation")

    # If date range changed, regenerate TripDate rows to match the new range
    if updated_dates:
        # reload trip to ensure we have latest values
        db.refresh(trip)
        # compute desired dates between start and end
        if trip.date_start and trip.date_end and trip.date_start <= trip.date_end:
            ws = set(trip.allowed_weekdays) if trip.allowed_weekdays else None
            desired = set()
            d = trip.date_start
            while d <= trip.date_end:
                if (ws is None) or (d.weekday() in ws):
                    desired.add(d)
                d = d + timedelta(days=1)

            # fetch existing dates
            existing = db.query(TripDate).filter(TripDate.trip_id == trip.id).all()
            existing_dates = {r.date for r in existing}

            # dates to remove
            to_remove = [r for r in existing if r.date not in desired]
            for r in to_remove:
                db.delete(r)

            # dates to add
            for d in sorted(desired):
                if d not in existing_dates:
                    db.add(TripDate(trip_id=trip.id, date=d))
        else:
            # if no valid range provided, remove existing trip_dates
            db.query(TripDate).filter(TripDate.trip_id == trip.id).delete()

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to regenerate trip dates")

    db.refresh(trip)
    return trip
