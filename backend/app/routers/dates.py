from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.trip import Trip
from app.models.trip_date import TripDate
from app.models.user_availability import UserAvailability
from app.models.user_trip import UserTrip
from app.models.user import User
from app.routers.user_trips import get_authenticated_user
from app.schemas.dates import TripDateRead, BulkAvailabilityUpdate, CalendarResponse

router = APIRouter()


def _parse_weekdays(allowed_weekdays):
    # expected array of ints 0..6 (Sunday..Saturday)
    return set(allowed_weekdays) if allowed_weekdays else None


@router.post('/trips/{hash_id}/dates/generate')
def generate_dates(hash_id: str, payload: dict = None, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.hash_id == hash_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail='Trip not found')

    body = payload or {}
    start = body.get('date_start') or getattr(trip, 'date_start', None)
    end = body.get('date_end') or getattr(trip, 'date_end', None)
    weekdays = body.get('allowed_weekdays') or getattr(trip, 'allowed_weekdays', None)

    if not start or not end:
        raise HTTPException(status_code=400, detail='date_start and date_end required')

    # save range to trip
    trip.date_start = datetime.fromisoformat(start).date() if isinstance(start, str) else start
    trip.date_end = datetime.fromisoformat(end).date() if isinstance(end, str) else end
    trip.allowed_weekdays = weekdays
    db.add(trip)
    db.commit()

    ws = _parse_weekdays(weekdays)
    d = trip.date_start
    added = 0
    while d <= trip.date_end:
        if (ws is None) or (d.weekday() in ws):
            exists = db.query(TripDate).filter(TripDate.trip_id == trip.id, TripDate.date == d).first()
            if not exists:
                td = TripDate(trip_id=trip.id, date=d)
                db.add(td)
                added += 1
        d = d + timedelta(days=1)
    db.commit()
    return { 'generated': added }


@router.get('/trips/{hash_id}/dates', response_model=List[TripDateRead])
def list_dates(hash_id: str, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.hash_id == hash_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail='Trip not found')
    rows = db.query(TripDate).filter(TripDate.trip_id == trip.id).order_by(TripDate.date).all()
    return rows


@router.post('/trips/{hash_id}/availability')
def bulk_update_availability(hash_id: str, payload: BulkAvailabilityUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_authenticated_user)):
    trip = db.query(Trip).filter(Trip.hash_id == hash_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail='Trip not found')

    # Map dates to trip_date ids
    trip_dates = db.query(TripDate).filter(TripDate.trip_id == trip.id).all()
    date_map = { td.date.isoformat(): td.id for td in trip_dates }

    updated = 0
    from datetime import datetime
    for u in payload.updates:
        date_str = u.date.isoformat() if hasattr(u.date, 'isoformat') else str(u.date)
        td_id = date_map.get(date_str)
        if not td_id:
            continue
        # find existing availability
        row = db.query(UserAvailability).filter(UserAvailability.trip_date_id == td_id, UserAvailability.user_id == current_user.id).first()
        if row:
            row.status = u.status
            row.updated_at = datetime.utcnow()
        else:
            row = UserAvailability(trip_date_id=td_id, user_id=current_user.id, status=u.status)
            db.add(row)
        updated += 1
    db.commit()
    return { 'updated': updated }


@router.get('/trips/{hash_id}/calendar')
def get_calendar(hash_id: str, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.hash_id == hash_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail='Trip not found')

    # dates
    dates = db.query(TripDate).filter(TripDate.trip_id == trip.id).order_by(TripDate.date).all()
    dates_list = [d.date.isoformat() for d in dates]

    # members
    members = db.query(UserTrip).filter(UserTrip.trip_id == trip.id).all()
    users = []
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        users.append({ 'id': str(u.id), 'displayName': m.user_name or u.user_id })

    # availability map
    availability = {}
    for m in members:
        availability[str(m.user_id)] = { d.date.isoformat(): 'unset' for d in dates }

    rows = db.query(UserAvailability).join(TripDate, UserAvailability.trip_date_id == TripDate.id).filter(TripDate.trip_id == trip.id).all()
    for r in rows:
        # find date string
        td = db.query(TripDate).filter(TripDate.id == r.trip_date_id).first()
        if not td:
            continue
        availability.setdefault(str(r.user_id), {})[td.date.isoformat()] = r.status

    return { 'dates': dates_list, 'users': users, 'availability': availability }
