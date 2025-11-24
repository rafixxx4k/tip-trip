from datetime import date
from sqlalchemy import Column, Integer, Date, ForeignKey

from app.db.session import Base


class TripDate(Base):
    __tablename__ = "trip_dates"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
