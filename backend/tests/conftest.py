"""Pytest configuration and fixtures for testing."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.session import Base, get_db
from app.main import app
from app.models.user import User
from app.models.trip import Trip
from app.models.user_trip import UserTrip


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Workaround for SQLite not supporting ARRAY type
import json
from sqlalchemy.types import TypeDecorator, String as SQLString
from sqlalchemy.dialects.postgresql import ARRAY


class JSONEncodedArray(TypeDecorator):
    """Converts ARRAY to JSON string for SQLite."""

    impl = SQLString
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None


@event.listens_for(Trip.__table__, "before_create", propagate=True)
def _set_sqlite_pragma(target, connection, **kw):
    """Handle ARRAY columns for SQLite by converting to JSON string"""
    if connection.dialect.name == "sqlite":
        for column in target.columns:
            if column.name == "allowed_weekdays":
                if (
                    hasattr(column.type, "__visit_name__")
                    and column.type.__visit_name__ == "ARRAY"
                ):
                    column.type = JSONEncodedArray()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(token="test_token_123", user_id="test_user_123")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user2(db_session):
    """Create a second test user."""
    user = User(token="test_token_456", user_id="test_user_456")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_trip(db_session, test_user):
    """Create a test trip with the test user as a member."""
    trip = Trip(title="Test Trip", description="A test trip", hash_id="test_trip_123")
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    # Add user as member
    membership = UserTrip(user_id=test_user.id, trip_id=trip.id, user_name="Test User")
    db_session.add(membership)
    db_session.commit()

    return trip


@pytest.fixture
def test_trip_with_multiple_users(db_session, test_user, test_user2):
    """Create a test trip with multiple users."""
    trip = Trip(
        title="Multi-User Trip",
        description="A trip with multiple users",
        hash_id="multi_trip_123",
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    # Add users as members
    for user, name in [(test_user, "User One"), (test_user2, "User Two")]:
        membership = UserTrip(user_id=user.id, trip_id=trip.id, user_name=name)
        db_session.add(membership)

    db_session.commit()
    return trip


@pytest.fixture
def auth_headers(test_user):
    """Return authentication headers for the test user."""
    return {"X-User-Hash": test_user.token}


@pytest.fixture
def auth_headers2(test_user2):
    """Return authentication headers for the second test user."""
    return {"X-User-Hash": test_user2.token}
