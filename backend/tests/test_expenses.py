"""Unit tests for expenses API endpoints."""

import pytest
from app.models.expense import Expense, ExpenseShare


class TestCreateExpense:
    """Tests for POST /trips/{trip_hash}/expenses endpoint."""

    def test_create_expense_success(
        self,
        client,
        test_trip_with_multiple_users,
        test_user,
        test_user2,
        auth_headers,
        db_session,
    ):
        """Test successful expense creation."""
        payload = {
            "amount": 100.0,
            "description": "Dinner at restaurant",
            "currency": "USD",
            "debtors": [
                {"userId": str(test_user.id), "shareType": "equal", "value": 50.0},
                {"userId": str(test_user2.id), "shareType": "equal", "value": 50.0},
            ],
        }

        response = client.post(
            f"/api/v1/trips/{test_trip_with_multiple_users.hash_id}/expenses",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 100.0
        assert data["description"] == "Dinner at restaurant"
        assert data["currency"] == "USD"
        assert data["payerId"] == str(test_user.id)
        assert len(data["debtors"]) == 2

        # Verify database records
        expense = db_session.query(Expense).first()
        assert expense is not None
        assert expense.amount == 100.0
        assert expense.payer_user_id == test_user.id

        shares = db_session.query(ExpenseShare).all()
        assert len(shares) == 2

    def test_create_expense_unauthorized(self, client, test_trip):
        """Test creating expense without authentication."""
        payload = {
            "amount": 50.0,
            "description": "Test",
            "currency": "USD",
            "debtors": [],
        }

        response = client.post(
            f"/api/v1/trips/{test_trip.hash_id}/expenses", json=payload
        )

        assert response.status_code == 401

    def test_create_expense_trip_not_found(self, client, auth_headers):
        """Test creating expense for non-existent trip."""
        payload = {
            "amount": 50.0,
            "description": "Test",
            "currency": "USD",
            "debtors": [],
        }

        response = client.post(
            "/api/v1/trips/nonexistent_trip/expenses",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "Trip not found" in response.json()["detail"]

    def test_create_expense_not_a_member(self, client, test_trip, auth_headers2):
        """Test creating expense when user is not a trip member."""
        payload = {
            "amount": 50.0,
            "description": "Test",
            "currency": "USD",
            "debtors": [],
        }

        response = client.post(
            f"/api/v1/trips/{test_trip.hash_id}/expenses",
            json=payload,
            headers=auth_headers2,
        )

        assert response.status_code == 403
        assert "Not a member" in response.json()["detail"]

    def test_create_expense_invalid_debtor(
        self, client, test_trip_with_multiple_users, test_user, auth_headers
    ):
        """Test creating expense with invalid debtor userId."""
        payload = {
            "amount": 100.0,
            "description": "Test",
            "currency": "USD",
            "debtors": [{"userId": "invalid", "shareType": "equal", "value": 50.0}],
        }

        response = client.post(
            f"/api/v1/trips/{test_trip_with_multiple_users.hash_id}/expenses",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Invalid userId" in response.json()["detail"]

    def test_create_expense_debtor_not_member(
        self, client, test_trip, test_user, test_user2, auth_headers, db_session
    ):
        """Test creating expense with debtor who is not a trip member."""
        # test_user2 is not a member of test_trip
        payload = {
            "amount": 100.0,
            "description": "Test",
            "currency": "USD",
            "debtors": [
                {"userId": str(test_user.id), "shareType": "equal", "value": 50.0},
                {"userId": str(test_user2.id), "shareType": "equal", "value": 50.0},
            ],
        }

        response = client.post(
            f"/api/v1/trips/{test_trip.hash_id}/expenses",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "is not a member of this trip" in response.json()["detail"]


class TestGetExpenses:
    """Tests for GET /trips/{trip_hash}/expenses endpoint."""

    def test_get_expenses_empty(self, client, test_trip, auth_headers):
        """Test getting expenses for trip with no expenses."""
        response = client.get(
            f"/api/v1/trips/{test_trip.hash_id}/expenses", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_get_expenses_with_data(
        self,
        client,
        test_trip_with_multiple_users,
        test_user,
        test_user2,
        auth_headers,
        db_session,
    ):
        """Test getting expenses with existing data."""
        # Create an expense directly in the database
        expense = Expense(
            trip_id=test_trip_with_multiple_users.id,
            payer_user_id=test_user.id,
            amount=100.0,
            currency="USD",
            description="Test Expense",
        )
        db_session.add(expense)
        db_session.commit()
        db_session.refresh(expense)

        # Add shares
        share1 = ExpenseShare(
            expense_id=expense.id, user_id=test_user.id, share_type="equal", value=50.0
        )
        share2 = ExpenseShare(
            expense_id=expense.id, user_id=test_user2.id, share_type="equal", value=50.0
        )
        db_session.add_all([share1, share2])
        db_session.commit()

        response = client.get(
            f"/api/v1/trips/{test_trip_with_multiple_users.hash_id}/expenses",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["amount"] == 100.0
        assert data[0]["description"] == "Test Expense"
        assert len(data[0]["debtors"]) == 2

    def test_get_expenses_unauthorized(self, client, test_trip):
        """Test getting expenses without authentication."""
        response = client.get(f"/api/v1/trips/{test_trip.hash_id}/expenses")
        assert response.status_code == 401

    def test_get_expenses_not_a_member(self, client, test_trip, auth_headers2):
        """Test getting expenses when user is not a trip member."""
        response = client.get(
            f"/api/v1/trips/{test_trip.hash_id}/expenses", headers=auth_headers2
        )

        assert response.status_code == 403

    def test_get_expenses_trip_not_found(self, client, auth_headers):
        """Test getting expenses for non-existent trip."""
        response = client.get(
            "/api/v1/trips/nonexistent_trip/expenses", headers=auth_headers
        )

        assert response.status_code == 404


class TestGetSettlements:
    """Tests for GET /trips/{trip_hash}/settlements endpoint."""

    def test_get_settlements_no_expenses(self, client, test_trip, auth_headers):
        """Test settlements calculation with no expenses."""
        response = client.get(
            f"/api/v1/trips/{test_trip.hash_id}/settlements", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["balances"] == []

    def test_get_settlements_balanced(
        self,
        client,
        test_trip_with_multiple_users,
        test_user,
        test_user2,
        auth_headers,
        db_session,
    ):
        """Test settlements when all users have paid their share."""
        # User 1 pays 100, split equally
        expense1 = Expense(
            trip_id=test_trip_with_multiple_users.id,
            payer_user_id=test_user.id,
            amount=100.0,
            currency="USD",
            description="Expense 1",
        )
        db_session.add(expense1)
        db_session.commit()
        db_session.refresh(expense1)

        share1_1 = ExpenseShare(
            expense_id=expense1.id, user_id=test_user.id, share_type="equal", value=50.0
        )
        share1_2 = ExpenseShare(
            expense_id=expense1.id,
            user_id=test_user2.id,
            share_type="equal",
            value=50.0,
        )
        db_session.add_all([share1_1, share1_2])
        db_session.commit()

        # User 2 pays 100, split equally
        expense2 = Expense(
            trip_id=test_trip_with_multiple_users.id,
            payer_user_id=test_user2.id,
            amount=100.0,
            currency="USD",
            description="Expense 2",
        )
        db_session.add(expense2)
        db_session.commit()
        db_session.refresh(expense2)

        share2_1 = ExpenseShare(
            expense_id=expense2.id, user_id=test_user.id, share_type="equal", value=50.0
        )
        share2_2 = ExpenseShare(
            expense_id=expense2.id,
            user_id=test_user2.id,
            share_type="equal",
            value=50.0,
        )
        db_session.add_all([share2_1, share2_2])
        db_session.commit()

        response = client.get(
            f"/api/v1/trips/{test_trip_with_multiple_users.hash_id}/settlements",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Both users paid 100 and owe 100, so no settlements needed
        assert len(data["balances"]) == 0

    def test_get_settlements_unbalanced(
        self,
        client,
        test_trip_with_multiple_users,
        test_user,
        test_user2,
        auth_headers,
        db_session,
    ):
        """Test settlements when one user owes another."""
        # User 1 pays 100, split equally (user2 owes 50)
        expense = Expense(
            trip_id=test_trip_with_multiple_users.id,
            payer_user_id=test_user.id,
            amount=100.0,
            currency="USD",
            description="Expense",
        )
        db_session.add(expense)
        db_session.commit()
        db_session.refresh(expense)

        share1 = ExpenseShare(
            expense_id=expense.id, user_id=test_user.id, share_type="equal", value=50.0
        )
        share2 = ExpenseShare(
            expense_id=expense.id, user_id=test_user2.id, share_type="equal", value=50.0
        )
        db_session.add_all([share1, share2])
        db_session.commit()

        response = client.get(
            f"/api/v1/trips/{test_trip_with_multiple_users.hash_id}/settlements",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["balances"]) == 1

        settlement = data["balances"][0]
        assert settlement["fromUser"] == str(test_user2.id)
        assert settlement["toUser"] == str(test_user.id)
        assert settlement["amount"] == 50.0
        assert settlement["currency"] == "USD"

    def test_get_settlements_unauthorized(self, client, test_trip):
        """Test settlements without authentication."""
        response = client.get(f"/api/v1/trips/{test_trip.hash_id}/settlements")
        assert response.status_code == 401

    def test_get_settlements_not_a_member(self, client, test_trip, auth_headers2):
        """Test settlements when user is not a trip member."""
        response = client.get(
            f"/api/v1/trips/{test_trip.hash_id}/settlements", headers=auth_headers2
        )

        assert response.status_code == 403

    def test_get_settlements_trip_not_found(self, client, auth_headers):
        """Test settlements for non-existent trip."""
        response = client.get(
            "/api/v1/trips/nonexistent_trip/settlements", headers=auth_headers
        )

        assert response.status_code == 404
