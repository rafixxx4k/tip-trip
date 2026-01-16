"""Unit tests for trips API endpoints."""

import pytest
from app.models.trip import Trip
from app.models.user_trip import UserTrip


class TestCreateTrip:
    """Tests for POST /trips endpoint."""

    def test_create_trip_success(self, client, auth_headers, db_session):
        """Test successful trip creation."""
        payload = {
            "title": "Summer Vacation",
            "user_name": "John Doe",
            "description": "Beach trip with friends",
        }

        response = client.post("/api/v1/trips", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Summer Vacation"
        assert data["description"] == "Beach trip with friends"
        assert "hash_id" in data
        assert len(data["hash_id"]) > 0

        # Verify database
        trip = db_session.query(Trip).filter(Trip.hash_id == data["hash_id"]).first()
        assert trip is not None
        assert trip.title == "Summer Vacation"

        # Verify creator is added as member
        membership = (
            db_session.query(UserTrip).filter(UserTrip.trip_id == trip.id).first()
        )
        assert membership is not None
        assert membership.user_name == "John Doe"

    def test_create_trip_minimal(self, client, auth_headers, db_session):
        """Test creating trip with minimal required fields."""
        payload = {"title": "Quick Trip", "user_name": "Alice"}

        response = client.post("/api/v1/trips", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Quick Trip"
        assert data["description"] is None

    def test_create_trip_unauthorized(self, client):
        """Test creating trip without authentication."""
        payload = {"title": "Test Trip", "user_name": "Test User"}

        response = client.post("/api/v1/trips", json=payload)

        assert response.status_code == 401

    def test_create_trip_missing_title(self, client, auth_headers):
        """Test creating trip without required title."""
        payload = {"user_name": "Test User"}

        response = client.post("/api/v1/trips", json=payload, headers=auth_headers)

        assert response.status_code == 422

    def test_create_trip_missing_user_name(self, client, auth_headers):
        """Test creating trip without user name."""
        payload = {"title": "Test Trip"}

        response = client.post("/api/v1/trips", json=payload, headers=auth_headers)

        assert response.status_code == 422

    def test_create_trip_empty_title(self, client, auth_headers):
        """Test creating trip with empty title (currently allowed)."""
        payload = {"title": "", "user_name": "Test User"}

        response = client.post("/api/v1/trips", json=payload, headers=auth_headers)

        # API currently doesn't validate empty title
        assert response.status_code == 200
        assert response.json()["title"] == ""


class TestGetTrip:
    """Tests for GET /trips/{hash_id} endpoint."""

    def test_get_trip_success(self, client, test_trip, auth_headers):
        """Test successfully retrieving a trip."""
        response = client.get(
            f"/api/v1/trips/{test_trip.hash_id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["hash_id"] == test_trip.hash_id
        assert data["title"] == test_trip.title
        assert data["description"] == test_trip.description

    def test_get_trip_with_dates(self, client, auth_headers, db_session, test_user):
        """Test retrieving trip with date fields."""
        from datetime import date

        trip = Trip(
            title="Dated Trip",
            hash_id="dated_trip",
            date_start=date(2026, 7, 1),
            date_end=date(2026, 7, 15),
            # Don't set allowed_weekdays to avoid SQLite/Pydantic validation issues
        )
        db_session.add(trip)
        db_session.flush()

        # Add user as member
        membership = UserTrip(
            user_id=test_user.id, trip_id=trip.id, user_name="Test User"
        )
        db_session.add(membership)
        db_session.commit()

        response = client.get(f"/api/v1/trips/{trip.hash_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Dated Trip"
        assert data["date_start"] == "2026-07-01"
        assert data["date_end"] == "2026-07-15"
        # allowed_weekdays is None since we didn't set it

    def test_get_trip_not_found(self, client, auth_headers):
        """Test retrieving non-existent trip."""
        response = client.get("/api/v1/trips/nonexistent", headers=auth_headers)

        assert response.status_code == 404

    def test_get_trip_unauthorized(self, client, test_trip):
        """Test retrieving trip without authentication."""
        response = client.get(f"/api/v1/trips/{test_trip.hash_id}")

        assert response.status_code == 401


class TestListMyTrips:
    """Tests for GET /trips endpoint."""

    def test_list_trips_empty(self, client, auth_headers):
        """Test listing trips when user has none."""
        response = client.get("/api/v1/trips", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_list_trips_single(self, client, test_trip, auth_headers):
        """Test listing trips with one trip."""
        response = client.get("/api/v1/trips", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["hash_id"] == test_trip.hash_id
        assert data[0]["title"] == test_trip.title

    def test_list_trips_multiple(self, client, test_user, auth_headers, db_session):
        """Test listing multiple trips."""
        # Create multiple trips
        for i in range(3):
            trip = Trip(title=f"Trip {i}", hash_id=f"trip_{i}")
            db_session.add(trip)
            db_session.commit()

            membership = UserTrip(
                user_id=test_user.id, trip_id=trip.id, user_name="Test User"
            )
            db_session.add(membership)

        db_session.commit()

        response = client.get("/api/v1/trips", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_trips_only_users_trips(
        self, client, test_trip, test_user2, auth_headers2, db_session
    ):
        """Test that user only sees their own trips."""
        # test_trip belongs to test_user, not test_user2
        response = client.get("/api/v1/trips", headers=auth_headers2)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_list_trips_unauthorized(self, client):
        """Test listing trips without authentication."""
        response = client.get("/api/v1/trips")

        assert response.status_code == 401


class TestUpdateTrip:
    """Tests for PUT /trips/{hash_id} endpoint."""

    def test_update_trip_title(self, client, test_trip, auth_headers, db_session):
        """Test updating trip title."""
        payload = {"title": "Updated Title"}

        response = client.put(
            f"/api/v1/trips/{test_trip.hash_id}", json=payload, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

        # Verify database
        db_session.refresh(test_trip)
        assert test_trip.title == "Updated Title"

    def test_update_trip_description(self, client, test_trip, auth_headers):
        """Test updating trip description."""
        payload = {"description": "Updated description"}

        response = client.put(
            f"/api/v1/trips/{test_trip.hash_id}", json=payload, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    def test_update_trip_dates(self, client, test_trip, auth_headers):
        """Test updating trip date range."""
        payload = {"date_start": "2026-08-01", "date_end": "2026-08-15"}

        response = client.put(
            f"/api/v1/trips/{test_trip.hash_id}", json=payload, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["date_start"] == "2026-08-01"
        assert data["date_end"] == "2026-08-15"

    def test_update_trip_allowed_weekdays(self, client, test_trip, auth_headers):
        """Test updating allowed weekdays - skipped due to SQLite ARRAY incompatibility."""
        pytest.skip("SQLite doesn't support ARRAY type properly in tests")

    def test_update_trip_multiple_fields(self, client, test_trip, auth_headers):
        """Test updating multiple fields at once (excluding allowed_weekdays due to SQLite)."""
        payload = {
            "title": "New Title",
            "description": "New description",
            "date_start": "2026-09-01",
            "date_end": "2026-09-10",
        }

        response = client.put(
            f"/api/v1/trips/{test_trip.hash_id}", json=payload, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["description"] == "New description"
        assert data["date_start"] == "2026-09-01"

    def test_update_trip_not_found(self, client, auth_headers):
        """Test updating non-existent trip."""
        payload = {"title": "New Title"}

        response = client.put(
            "/api/v1/trips/nonexistent", json=payload, headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_trip_not_a_member(self, client, test_trip, auth_headers2):
        """Test updating trip when not a member."""
        payload = {"title": "Hacked Title"}

        response = client.put(
            f"/api/v1/trips/{test_trip.hash_id}", json=payload, headers=auth_headers2
        )

        assert response.status_code == 403

    def test_update_trip_unauthorized(self, client, test_trip):
        """Test updating trip without authentication."""
        payload = {"title": "New Title"}

        response = client.put(f"/api/v1/trips/{test_trip.hash_id}", json=payload)

        assert response.status_code == 401


class TestTripMembers:
    """Tests for trip membership endpoints."""

    def test_add_member_to_trip(self, client, test_trip, test_user2, db_session):
        """Test adding a new member to a trip."""
        payload = {"user_hash": test_user2.token, "user_name": "New Member"}

        # Use test_user2's auth headers
        auth_headers = {"X-User-Hash": test_user2.token}

        response = client.post(
            f"/api/v1/trips/{test_trip.hash_id}/members",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200

        # Verify membership in database
        membership = (
            db_session.query(UserTrip)
            .filter(UserTrip.trip_id == test_trip.id, UserTrip.user_id == test_user2.id)
            .first()
        )
        assert membership is not None
        assert membership.user_name == "New Member"

    def test_get_trip_members(self, client, test_trip, auth_headers):
        """Test retrieving trip members."""
        response = client.get(
            f"/api/v1/trips/{test_trip.hash_id}/members", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["user_name"] == "Test User"
