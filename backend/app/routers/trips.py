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
    trip = Trip(title=payload.title, description=payload.description, owner_id=current_user.id, hash_id=hash_id)
    db.add(trip)
    try:
        # flush so trip.id is available for the association
        db.flush()
        membership = UserTrip(user_id=current_user.id, trip_id=trip.id, is_owner=True)
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
    return trip


@router.get("/trips", response_model=List[TripRead])
def list_my_trips(db: Session = Depends(get_db), current_user: User = Depends(get_authenticated_user)):
    """Return trips where the authenticated user is owner or a member.

    Requires X-User-Hash header.
    """
    # Join against user_trips to find memberships
    q = db.query(Trip).join(UserTrip, UserTrip.trip_id == Trip.id).filter(UserTrip.user_id == current_user.id)
    # Include trips where user is owner (in case there is no membership row)
    q2 = db.query(Trip).filter(Trip.owner_id == current_user.id)
    # Union the two queries and return distinct trips
    trips = q.union(q2).all()
    return trips


@router.put("/trips/{hash_id}", response_model=TripRead)
def update_trip(hash_id: str, payload: TripUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_authenticated_user)):
    """Update a trip. Only the trip owner (authenticated) may update the trip."""
    trip = db.query(Trip).filter(Trip.hash_id == hash_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Only owner allowed to update
    if trip.owner_id is None or trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this trip")

    if payload.title is not None:
        trip.title = payload.title
    if payload.description is not None:
        trip.description = payload.description

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid update or constraint violation")
    db.refresh(trip)
    return trip
