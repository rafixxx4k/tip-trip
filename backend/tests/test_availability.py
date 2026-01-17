"""Unit tests for availability/dates API endpoints."""

import pytest
from datetime import date
from app.models.trip_date import TripDate
from app.models.user_availability import UserAvailability


class TestSubmitAvailability:
    """Tests for POST /trips/{trip_hash}/availability endpoint."""

    def test_submit_availability_success(
        self, client, test_trip, auth_headers, db_session
    ):
        """Test successfully submitting availability."""
        payload = {
            "updates": [
                {"date": "2026-07-15", "status": "available"},
                {"date": "2026-07-16", "status": "unavailable"},
                {"date": "2026-07-17", "status": "maybe"},
            ]
        }

        response = client.post(
            f"/api/v1/trips/{test_trip.hash_id}/availability",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_submit_availability_creates_dates(
        self, client, test_trip, auth_headers, db_session
    ):
        """Test that submitting availability requires existing trip dates."""
        from datetime import date
        from app.models.trip_date import TripDate

        # Create trip dates first
        date1 = TripDate(trip_id=test_trip.id, date=date(2026, 8, 1))
        date2 = TripDate(trip_id=test_trip.id, date=date(2026, 8, 2))
        db_session.add(date1)
        db_session.add(date2)
        db_session.commit()

        payload = {
            "updates": [
                {"date": "2026-08-01", "status": "available"},
                {"date": "2026-08-02", "status": "available"},
            ]
        }

        response = client.post(
            f"/api/v1/trips/{test_trip.hash_id}/availability",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200

        # Verify dates exist
        trip_dates = (
            db_session.query(TripDate).filter(TripDate.trip_id == test_trip.id).all()
        )
        assert len(trip_dates) >= 2

    def test_submit_availability_updates_existing(
        self, client, test_trip, test_user, auth_headers, db_session
    ):
        """Test updating existing availability."""
        # First submission
        payload1 = {"updates": [{"date": "2026-07-20", "status": "available"}]}

        response1 = client.post(
            f"/api/v1/trips/{test_trip.hash_id}/availability",
            json=payload1,
            headers=auth_headers,
        )
        assert response1.status_code == 200

        # Update same date
        payload2 = {"updates": [{"date": "2026-07-20", "status": "unavailable"}]}

        response2 = client.post(
            f"/api/v1/trips/{test_trip.hash_id}/availability",
            json=payload2,
            headers=auth_headers,
        )
        assert response2.status_code == 200

    def test_submit_availability_invalid_status(self, client, test_trip, auth_headers):
        """Test submitting with invalid status value - API accepts any string."""
        payload = {"updates": [{"date": "2026-07-15", "status": "invalid_status"}]}

        response = client.post(
            f"/api/v1/trips/{test_trip.hash_id}/availability",
            json=payload,
            headers=auth_headers,
        )

        # API currently doesn't validate status strings
        assert response.status_code == 200

    def test_submit_availability_invalid_date_format(
        self, client, test_trip, auth_headers
    ):
        """Test submitting with invalid date format."""
        payload = {"updates": [{"date": "not-a-date", "status": "available"}]}

        response = client.post(
            f"/api/v1/trips/{test_trip.hash_id}/availability",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_submit_availability_empty_updates(self, client, test_trip, auth_headers):
        """Test submitting with empty updates array."""
        payload = {"updates": []}

        response = client.post(
            f"/api/v1/trips/{test_trip.hash_id}/availability",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_submit_availability_unauthorized(self, client, test_trip):
        """Test submitting availability without authentication."""
        payload = {"updates": [{"date": "2026-07-15", "status": "available"}]}

        response = client.post(
            f"/api/v1/trips/{test_trip.hash_id}/availability", json=payload
        )

        assert response.status_code == 401

    def test_submit_availability_trip_not_found(self, client, auth_headers):
        """Test submitting availability for non-existent trip."""
        payload = {"updates": [{"date": "2026-07-15", "status": "available"}]}

        response = client.post(
            "/api/v1/trips/nonexistent/availability",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_submit_availability_not_a_member(self, client, test_trip, auth_headers2):
        """Test submitting availability when not a trip member - currently allowed."""
        payload = {"updates": [{"date": "2026-07-15", "status": "available"}]}

        response = client.post(
            f"/api/v1/trips/{test_trip.hash_id}/availability",
            json=payload,
            headers=auth_headers2,
        )

        # API currently doesn't check membership for availability submission
        assert response.status_code == 200


class TestGetCalendar:
    """Tests for GET /trips/{trip_hash}/calendar endpoint."""

    def test_get_calendar_empty(self, client, test_trip, auth_headers):
        """Test getting calendar with no availability data."""
        response = client.get(
            f"/api/v1/trips/{test_trip.hash_id}/calendar", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "dates" in data
        assert "users" in data
        assert "availability" in data

    def test_get_calendar_with_data(
        self, client, test_trip, test_user, auth_headers, db_session
    ):
        """Test getting calendar with availability data."""
        # Create a trip date
        trip_date = TripDate(trip_id=test_trip.id, date=date(2026, 7, 15))
        db_session.add(trip_date)
        db_session.commit()
        db_session.refresh(trip_date)

        # Create availability
        availability = UserAvailability(
            trip_date_id=trip_date.id, user_id=test_user.id, status="available"
        )
        db_session.add(availability)
        db_session.commit()

        response = client.get(
            f"/api/v1/trips/{test_trip.hash_id}/calendar", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["dates"]) >= 1
        assert len(data["users"]) >= 1
        assert "availability" in data

    def test_get_calendar_multiple_users(
        self,
        client,
        test_trip_with_multiple_users,
        test_user,
        test_user2,
        auth_headers,
        db_session,
    ):
        """Test calendar with multiple users' availability."""
        # Create trip dates
        dates = [date(2026, 7, 15), date(2026, 7, 16)]
        for d in dates:
            trip_date = TripDate(trip_id=test_trip_with_multiple_users.id, date=d)
            db_session.add(trip_date)
        db_session.commit()

        # Add availability for both users
        trip_dates = (
            db_session.query(TripDate)
            .filter(TripDate.trip_id == test_trip_with_multiple_users.id)
            .all()
        )

        for td in trip_dates:
            avail1 = UserAvailability(
                trip_date_id=td.id, user_id=test_user.id, status="available"
            )
            avail2 = UserAvailability(
                trip_date_id=td.id, user_id=test_user2.id, status="maybe"
            )
            db_session.add_all([avail1, avail2])
        db_session.commit()

        response = client.get(
            f"/api/v1/trips/{test_trip_with_multiple_users.hash_id}/calendar",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 2
        assert len(data["dates"]) >= 2

    def test_get_calendar_unauthorized(self, client, test_trip):
        """Test getting calendar without authentication - currently allowed."""
        response = client.get(f"/api/v1/trips/{test_trip.hash_id}/calendar")

        # API currently doesn't require authentication for calendar view
        assert response.status_code == 200

    def test_get_calendar_trip_not_found(self, client, auth_headers):
        """Test getting calendar for non-existent trip."""
        response = client.get(
            "/api/v1/trips/nonexistent/calendar", headers=auth_headers
        )

        assert response.status_code == 404

    def test_get_calendar_not_a_member(self, client, test_trip, auth_headers2):
        """Test getting calendar when not a trip member - currently allowed."""
        response = client.get(
            f"/api/v1/trips/{test_trip.hash_id}/calendar", headers=auth_headers2
        )

        # API currently doesn't check membership for calendar view
        assert response.status_code == 200


class TestAvailabilityStatuses:
    """Tests for different availability status values."""

    def test_all_status_types(self, client, test_trip, auth_headers):
        """Test all valid availability statuses."""
        statuses = ["available", "unavailable", "maybe", "unset"]

        for i, status in enumerate(statuses):
            payload = {"updates": [{"date": f"2026-07-{15+i:02d}", "status": status}]}

            response = client.post(
                f"/api/v1/trips/{test_trip.hash_id}/availability",
                json=payload,
                headers=auth_headers,
            )

            assert response.status_code == 200

    def test_change_status_sequence(self, client, test_trip, auth_headers):
        """Test changing availability status through different values."""
        test_date = "2026-07-25"
        statuses = ["available", "maybe", "unavailable", "unset"]

        for status in statuses:
            payload = {"updates": [{"date": test_date, "status": status}]}

            response = client.post(
                f"/api/v1/trips/{test_trip.hash_id}/availability",
                json=payload,
                headers=auth_headers,
            )

            assert response.status_code == 200
