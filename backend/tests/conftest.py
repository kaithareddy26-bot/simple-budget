"""
Shared test fixtures and utilities for all test suites.

Key design:
  1. DATABASE_URL env var set before any app import — prevents SQLAlchemy
     connecting to Postgres at import time.
  2. init_db patched out — startup event does nothing.
  3. get_db overridden with a no-op in every test client.
  4. All service dependencies are Mocks — no DB needed.
  5. Model factories return Mock objects with the right attributes —
     avoids SQLAlchemy mapper issues while still feeding realistic data
     to the serializer.
"""

import os
import pytest
from unittest.mock import Mock, patch
from uuid import UUID
from decimal import Decimal
from datetime import date, datetime

# ── MUST be before ALL app imports ──────────────────────────────────────────
os.environ.setdefault("DATABASE_URL", "postgresql://fake:fake@localhost/fake")

from fastapi.testclient import TestClient          # noqa: E402

with patch("app.models.init_db", return_value=None):
    from app.main import app                       # noqa: E402

from app.models.base import get_db                # noqa: E402
from app.dependencies import (                    # noqa: E402
    get_auth_service,
    get_expense_service,
    get_budget_service,
    get_income_service,
    get_report_service,
    get_current_user,
)
from app.schemas.auth_schemas import TokenData    # noqa: E402


# ── Dummy DB override ────────────────────────────────────────────────────────
def _fake_db():
    yield Mock()


# ── Stable test IDs ──────────────────────────────────────────────────────────
FIXED_USER_ID: UUID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
FIXED_EXPENSE_ID: UUID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
FIXED_BUDGET_ID: UUID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
FIXED_INCOME_ID: UUID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


# ── Model factories ──────────────────────────────────────────────────────────
# Return plain Mock objects with attributes set — avoids SQLAlchemy mapper
# issues while still producing realistic data for Pydantic serialisation.

def make_user(
    user_id: UUID = FIXED_USER_ID,
    email: str = "test@example.com",
    full_name: str = "Test User",
    hashed_password: str = "hashed_password_value",
):
    u = Mock()
    u.id = user_id
    u.email = email
    u.hashed_password = hashed_password
    u.full_name = full_name
    return u


def make_expense(
    expense_id: UUID = FIXED_EXPENSE_ID,
    user_id: UUID = FIXED_USER_ID,
    amount: Decimal = Decimal("150.00"),
    category: str = "Groceries",
    expense_date: date = date(2024, 3, 10),
    note=None,
):
    e = Mock()
    e.id = expense_id
    e.user_id = user_id
    e.amount = amount
    e.category = category
    e.date = expense_date
    e.note = note
    e.created_at = None
    return e


def make_budget(
    budget_id: UUID = FIXED_BUDGET_ID,
    user_id: UUID = FIXED_USER_ID,
    month: str = "2024-03",
    amount: Decimal = Decimal("5000.00"),
):
    b = Mock()
    b.id = budget_id
    b.user_id = user_id
    b.month = month
    b.amount = amount
    b.created_at = None
    b.updated_at = None
    return b


def make_income(
    income_id: UUID = FIXED_INCOME_ID,
    user_id: UUID = FIXED_USER_ID,
    amount: Decimal = Decimal("3500.00"),
    source: str = "Monthly Salary",
    income_date: date = date(2024, 3, 15),
):
    i = Mock()
    i.id = income_id
    i.user_id = user_id
    i.amount = amount
    i.source = source
    i.date = income_date
    i.created_at = None
    return i


# ── Pytest fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def token_data() -> TokenData:
    return TokenData(user_id=FIXED_USER_ID, email="test@example.com")


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


@pytest.fixture
def auth_client(token_data, mock_auth_service, mock_expense_service,
                mock_budget_service, mock_income_service, mock_report_service):
    """
    Authenticated TestClient — all services mocked, auth bypassed, no DB.
    """
    app.dependency_overrides[get_db] = _fake_db
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
def unauth_client(mock_auth_service, mock_expense_service, mock_budget_service,
                  mock_income_service, mock_report_service):
    """
    TestClient WITHOUT get_current_user override — JWT fires → real 401s.
    Still no Postgres.
    """
    app.dependency_overrides[get_db] = _fake_db
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


# ── Assertion helpers ────────────────────────────────────────────────────────

def assert_error_shape(body: dict, expected_status: int, expected_error_code: str):
    assert body.get("status") == expected_status, \
        f"Expected status {expected_status}, got {body.get('status')}"
    assert body.get("errorCode") == expected_error_code, \
        f"Expected errorCode '{expected_error_code}', got {body.get('errorCode')}"
    for field in ("timestamp", "error", "message", "path"):
        assert field in body, f"Missing '{field}' in error response"


def assert_validation_error(body: dict):
    assert_error_shape(body, 400, "VAL-001")


def assert_unauthorized(body: dict):
    assert_error_shape(body, 401, "AUTH-001")