from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.db.session import Base


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    hash_id = Column(String(64), nullable=False, unique=True, index=True)
