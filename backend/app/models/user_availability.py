from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from app.db.session import Base


class UserAvailability(Base):
    __tablename__ = "user_availability"

    id = Column(Integer, primary_key=True, index=True)
    trip_date_id = Column(Integer, ForeignKey("trip_dates.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(32), nullable=False, default="unset")
    updated_at = Column(DateTime, default=datetime.utcnow)
