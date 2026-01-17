"""Unit tests for users API endpoints."""

import pytest
from app.models.user import User


class TestCreateUser:
    """Tests for POST /users endpoint."""

    def test_create_user_success(self, client, db_session):
        """Test successful user creation."""
        response = client.post("/api/v1/users")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "user_id" in data
        assert "token" in data
        assert "created_at" in data

        # Verify database
        user = db_session.query(User).filter(User.id == data["id"]).first()
        assert user is not None
        assert user.token == data["token"]
        assert user.user_id == data["user_id"]

    def test_create_user_generates_unique_token(self, client, db_session):
        """Test that each created user gets a unique token."""
        response1 = client.post("/api/v1/users")
        response2 = client.post("/api/v1/users")

        assert response1.status_code == 200
        assert response2.status_code == 200

        token1 = response1.json()["token"]
        token2 = response2.json()["token"]

        assert token1 != token2

    def test_create_user_generates_unique_user_id(self, client, db_session):
        """Test that each created user gets a unique user_id."""
        response1 = client.post("/api/v1/users")
        response2 = client.post("/api/v1/users")

        assert response1.status_code == 200
        assert response2.status_code == 200

        user_id1 = response1.json()["user_id"]
        user_id2 = response2.json()["user_id"]

        assert user_id1 != user_id2

    def test_create_multiple_users(self, client, db_session):
        """Test creating multiple users in sequence."""
        user_ids = []

        for _ in range(5):
            response = client.post("/api/v1/users")
            assert response.status_code == 200
            user_ids.append(response.json()["id"])

        # Verify all users in database
        users = db_session.query(User).filter(User.id.in_(user_ids)).all()
        assert len(users) == 5


class TestAuthentication:
    """Tests for authentication mechanism."""

    def test_authentication_with_valid_token(self, client, test_user):
        """Test that valid token allows access to protected endpoints."""
        headers = {"X-User-Hash": test_user.token}

        response = client.get("/api/v1/trips", headers=headers)

        # Should return 200, not 401
        assert response.status_code == 200

    def test_authentication_with_invalid_token(self, client):
        """Test that invalid token is rejected."""
        headers = {"X-User-Hash": "invalid_token_123"}

        response = client.get("/api/v1/trips", headers=headers)

        assert response.status_code == 401

    def test_authentication_without_token(self, client):
        """Test that missing token is rejected."""
        response = client.get("/api/v1/trips")

        assert response.status_code == 401

    def test_authentication_with_empty_token(self, client):
        """Test that empty token is rejected."""
        headers = {"X-User-Hash": ""}

        response = client.get("/api/v1/trips", headers=headers)

        assert response.status_code == 401
