"""
Shared test fixtures and utilities for all test suites.

These fixtures are automatically discovered by pytest and available
to every test file without explicit imports.
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4, UUID
from decimal import Decimal
from datetime import date, datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import (
    get_auth_service,
    get_expense_service,
    get_budget_service,
    get_income_service,
    get_report_service,
    get_current_user,
)
from app.schemas.auth_schemas import TokenData
from app.models.user import User
from app.models.expense import Expense
from app.models.budget import Budget
from app.models.income import Income


# ---------------------------------------------------------------------------
# Reusable ID constants — use these instead of generating new UUIDs per test
# ---------------------------------------------------------------------------

FIXED_USER_ID: UUID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
FIXED_EXPENSE_ID: UUID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
FIXED_BUDGET_ID: UUID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
FIXED_INCOME_ID: UUID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")

VALID_TOKEN = "Bearer valid.test.token"
INVALID_TOKEN = "Bearer invalid.token.here"

# ---------------------------------------------------------------------------
# Model factory helpers — build ORM-like objects with sensible defaults
# ---------------------------------------------------------------------------


def make_user(
    user_id: UUID = FIXED_USER_ID,
    email: str = "test@example.com",
    full_name: str = "Test User",
    hashed_password: str = "hashed_password_value",
) -> User:
    """Return a User model instance with defaults."""
    return User(
        id=user_id,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
    )


def make_expense(
    expense_id: UUID = FIXED_EXPENSE_ID,
    user_id: UUID = FIXED_USER_ID,
    amount: Decimal = Decimal("150.00"),
    category: str = "Groceries",
    expense_date: date = date(2024, 3, 10),
    note: str | None = "Test note",
) -> Expense:
    """Return an Expense model instance with defaults."""
    return Expense(
        id=expense_id,
        user_id=user_id,
        amount=amount,
        category=category,
        date=expense_date,
        note=note,
    )


def make_budget(
    budget_id: UUID = FIXED_BUDGET_ID,
    user_id: UUID = FIXED_USER_ID,
    month: str = "2024-03",
    amount: Decimal = Decimal("5000.00"),
) -> Budget:
    """Return a Budget model instance with defaults."""
    return Budget(
        id=budget_id,
        user_id=user_id,
        month=month,
        amount=amount,
    )


def make_income(
    income_id: UUID = FIXED_INCOME_ID,
    user_id: UUID = FIXED_USER_ID,
    amount: Decimal = Decimal("3500.00"),
    source: str = "Monthly Salary",
    income_date: date = date(2024, 3, 15),
) -> Income:
    """Return an Income model instance with defaults."""
    return Income(
        id=income_id,
        user_id=user_id,
        amount=amount,
        source=source,
        date=income_date,
    )


# ---------------------------------------------------------------------------
# TokenData fixture — the object returned by get_current_user
# ---------------------------------------------------------------------------


@pytest.fixture
def token_data() -> TokenData:
    """Return a TokenData for the fixed test user."""
    return TokenData(user_id=FIXED_USER_ID, email="test@example.com")


# ---------------------------------------------------------------------------
# Mock service fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_auth_service():
    return Mock()


@pytest.fixture
def mock_expense_service():
    return Mock()


@pytest.fixture
def mock_budget_service():
    return Mock()


@pytest.fixture
def mock_income_service():
    return Mock()


@pytest.fixture
def mock_report_service():
    return Mock()


# ---------------------------------------------------------------------------
# Authenticated test client — all service deps replaced with mocks,
# get_current_user bypassed to avoid DB/JWT overhead.
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_client(
    token_data,
    mock_auth_service,
    mock_expense_service,
    mock_budget_service,
    mock_income_service,
    mock_report_service,
):
    """
    TestClient with:
      - All service dependencies mocked
      - get_current_user overridden to return token_data directly
    Returns a dict with 'client' and each mock service for assertion use.
    """
    app.dependency_overrides[get_current_user] = lambda: token_data
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_expense_service] = lambda: mock_expense_service
    app.dependency_overrides[get_budget_service] = lambda: mock_budget_service
    app.dependency_overrides[get_income_service] = lambda: mock_income_service
    app.dependency_overrides[get_report_service] = lambda: mock_report_service

    with TestClient(app, raise_server_exceptions=False) as client:
        yield {
            "client": client,
            "auth_service": mock_auth_service,
            "expense_service": mock_expense_service,
            "budget_service": mock_budget_service,
            "income_service": mock_income_service,
            "report_service": mock_report_service,
        }

    app.dependency_overrides.clear()


@pytest.fixture
def unauth_client(
    mock_auth_service,
    mock_expense_service,
    mock_budget_service,
    mock_income_service,
    mock_report_service,
):
    """
    TestClient with service mocks but NO get_current_user override.
    Use this to test authentication failures (missing/invalid tokens).
    """
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_expense_service] = lambda: mock_expense_service
    app.dependency_overrides[get_budget_service] = lambda: mock_budget_service
    app.dependency_overrides[get_income_service] = lambda: mock_income_service
    app.dependency_overrides[get_report_service] = lambda: mock_report_service

    with TestClient(app, raise_server_exceptions=False) as client:
        yield {
            "client": client,
            "auth_service": mock_auth_service,
            "expense_service": mock_expense_service,
            "budget_service": mock_budget_service,
            "income_service": mock_income_service,
            "report_service": mock_report_service,
        }

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Assertion helpers — reusable checks for consistent error shapes
# ---------------------------------------------------------------------------


def assert_error_shape(body: dict, expected_status: int, expected_error_code: str):
    """
    Assert that a response body matches the Week-4 error envelope shape:
      { timestamp, status, error, errorCode, message, path }
    """
    assert body["status"] == expected_status, (
        f"Expected status {expected_status}, got {body.get('status')}"
    )
    assert body["errorCode"] == expected_error_code, (
        f"Expected errorCode '{expected_error_code}', got {body.get('errorCode')}"
    )
    assert "timestamp" in body, "Missing 'timestamp' in error response"
    assert "error" in body, "Missing 'error' field in error response"
    assert "message" in body, "Missing 'message' field in error response"
    assert "path" in body, "Missing 'path' field in error response"


def assert_validation_error(body: dict):
    """Assert a 400 VAL-001 validation error shape."""
    assert_error_shape(body, 400, "VAL-001")


def assert_unauthorized(body: dict):
    """Assert a 401 AUTH-001 error shape."""
    assert_error_shape(body, 401, "AUTH-001")