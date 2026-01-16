# Running Tests

## Setup

Install test dependencies (if not already installed):
```bash
pip install -r requirements.txt
```

## Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=app --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_expenses.py
```

Run specific test class or function:
```bash
pytest tests/test_expenses.py::TestCreateExpense
pytest tests/test_expenses.py::TestCreateExpense::test_create_expense_success
```

Run tests in verbose mode:
```bash
pytest -v
```

Run tests and stop at first failure:
```bash
pytest -x
```

## Running Tests in Docker

To run tests inside the Docker container:

```bash
docker compose exec backend pytest
```

Or with coverage:
```bash
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

## Test Structure

- `tests/conftest.py` - Pytest fixtures and configuration
- `tests/test_expenses.py` - Tests for expenses endpoints

## Test Coverage

The test suite covers:

### Create Expense Endpoint
- ✅ Successful expense creation
- ✅ Unauthorized access
- ✅ Trip not found
- ✅ User not a member of trip
- ✅ Invalid debtor userId
- ✅ Debtor not a member of trip

### Get Expenses Endpoint
- ✅ Empty expenses list
- ✅ Expenses with data
- ✅ Unauthorized access
- ✅ User not a member
- ✅ Trip not found

### Get Settlements Endpoint
- ✅ No expenses (empty settlements)
- ✅ Balanced expenses (no settlements needed)
- ✅ Unbalanced expenses (settlements required)
- ✅ Unauthorized access
- ✅ User not a member
- ✅ Trip not found
