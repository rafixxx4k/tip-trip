from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserTrip(Base):
    __tablename__ = "user_trips"
    __table_args__ = (UniqueConstraint('user_id', 'trip_id', name='uq_user_trip'),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    user_name = Column(String(128), nullable=False)

    # optional relationships for convenience
    # define them as backrefs are not declared here to avoid import cycles
    # relationship('User') and relationship('Trip') can be used in queries if needed
