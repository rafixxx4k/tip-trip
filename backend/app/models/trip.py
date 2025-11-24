from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date
from sqlalchemy.dialects.postgresql import ARRAY
from app.db.session import Base


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    hash_id = Column(String(64), nullable=False, unique=True, index=True)
    date_start = Column(Date, nullable=True)
    date_end = Column(Date, nullable=True)
    # store allowed weekdays as array of ints 0..6 (Sunday..Saturday)
    allowed_weekdays = Column(ARRAY(Integer), nullable=True)
