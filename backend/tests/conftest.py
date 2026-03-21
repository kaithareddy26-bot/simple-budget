"""
Shared fixtures/helpers for controller and error-path tests.

This unified file supports both the original Week 2 controller suites from
origin/main and the expanded API/error/dependency tests on this branch.
"""

import os
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import pytest

# Ensure app imports don't try to connect to real Postgres during test startup.
os.environ.setdefault("DATABASE_URL", "postgresql://fake:fake@localhost/fake")

from fastapi.testclient import TestClient  # noqa: E402

with patch("app.models.init_db", return_value=None):
    from app.main import app  # noqa: E402

from app.dependencies import (  # noqa: E402
    get_auth_service,
    get_budget_service,
    get_current_user,
    get_expense_service,
    get_income_service,
    get_report_service,
)
from app.models.base import get_db  # noqa: E402
from app.schemas.auth_schemas import TokenData  # noqa: E402


def _fake_db():
    yield Mock()


FIXED_USER_ID: UUID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
FIXED_EXPENSE_ID: UUID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
FIXED_BUDGET_ID: UUID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
FIXED_INCOME_ID: UUID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


def make_user(
    user_id: UUID = FIXED_USER_ID,
    email: str = "test@example.com",
    full_name: str = "Test User",
    hashed_password: str = "hashed_password_value",
):
    user = Mock()
    user.id = user_id
    user.email = email
    user.hashed_password = hashed_password
    user.full_name = full_name
    return user


def make_expense(
    expense_id: UUID = FIXED_EXPENSE_ID,
    user_id: UUID = FIXED_USER_ID,
    amount: Decimal = Decimal("150.00"),
    category: str = "Groceries",
    expense_date: date = date(2024, 3, 10),
    note=None,
):
    expense = Mock()
    expense.id = expense_id
    expense.user_id = user_id
    expense.amount = amount
    expense.category = category
    expense.date = expense_date
    expense.note = note
    expense.created_at = None
    return expense


def make_budget(
    budget_id: UUID = FIXED_BUDGET_ID,
    user_id: UUID = FIXED_USER_ID,
    month: str = "2024-03",
    amount: Decimal = Decimal("5000.00"),
):
    budget = Mock()
    budget.id = budget_id
    budget.user_id = user_id
    budget.month = month
    budget.amount = amount
    budget.created_at = None
    budget.updated_at = None
    return budget


def make_income(
    income_id: UUID = FIXED_INCOME_ID,
    user_id: UUID = FIXED_USER_ID,
    amount: Decimal = Decimal("3500.00"),
    source: str = "Monthly Salary",
    income_date: date = date(2024, 3, 15),
):
    income = Mock()
    income.id = income_id
    income.user_id = user_id
    income.amount = amount
    income.source = source
    income.date = income_date
    income.created_at = None
    return income


@pytest.fixture
def sample_user_id():
    return FIXED_USER_ID


@pytest.fixture
def token_data(sample_user_id) -> TokenData:
    return TokenData(user_id=sample_user_id, email="test@example.com")


@pytest.fixture
def service_mocks(sample_user_id):
    now = datetime.now(timezone.utc)

    auth_service = SimpleNamespace(
        register_user=lambda **_: SimpleNamespace(
            id=sample_user_id,
            email="new@example.com",
            full_name="New User",
        ),
        login_user=lambda **_: "fake.jwt.token",
        get_user_by_id=lambda *_: SimpleNamespace(
            id=sample_user_id,
            email="tester@example.com",
            full_name="Test User",
        ),
    )

    budget_service = SimpleNamespace(
        create_budget=lambda **_: SimpleNamespace(
            id=uuid4(),
            user_id=sample_user_id,
            month="2026-03",
            amount=Decimal("1200.00"),
            created_at=now,
            updated_at=now,
        ),
        get_current_month_budget=lambda **_: SimpleNamespace(
            id=uuid4(),
            user_id=sample_user_id,
            month="2026-03",
            amount=Decimal("1200.00"),
            created_at=now,
            updated_at=now,
        ),
        get_budget_by_id=lambda **_: SimpleNamespace(
            id=uuid4(),
            user_id=sample_user_id,
            month="2026-03",
            amount=Decimal("1200.00"),
            created_at=now,
            updated_at=now,
        ),
        update_budget_amount=lambda **_: SimpleNamespace(
            id=uuid4(),
            user_id=sample_user_id,
            month="2026-03",
            amount=Decimal("1400.00"),
            created_at=now,
            updated_at=now,
        ),
    )

    income_service = SimpleNamespace(
        add_income=lambda **_: SimpleNamespace(
            id=uuid4(),
            user_id=sample_user_id,
            amount=Decimal("3000.00"),
            source="Salary",
            date=date(2026, 3, 10),
            created_at=now,
        )
    )

    expense_service = SimpleNamespace(
        add_expense=lambda **_: SimpleNamespace(
            id=uuid4(),
            user_id=sample_user_id,
            amount=Decimal("45.00"),
            category="Food",
            date=date(2026, 3, 10),
            note="Lunch",
            created_at=now,
        ),
        get_current_month_expenses=lambda **_: [
            SimpleNamespace(
                id=uuid4(),
                user_id=sample_user_id,
                amount=Decimal("45.00"),
                category="Food",
                date=date(2026, 3, 10),
                note="Lunch",
                created_at=now,
            )
        ],
    )

    report_service = SimpleNamespace(
        get_monthly_summary=lambda **_: {
            "month": "2026-03",
            "total_income": Decimal("3000.00"),
            "total_expenses": Decimal("45.00"),
            "net_balance": Decimal("2955.00"),
            "expenses_by_category": {"Food": Decimal("45.00")},
        },
        utc_now=lambda: now,
    )

    return {
        "auth": auth_service,
        "budget": budget_service,
        "income": income_service,
        "expense": expense_service,
        "report": report_service,
    }


@pytest.fixture
def client(service_mocks):
    app.dependency_overrides[get_db] = _fake_db
    app.dependency_overrides[get_auth_service] = lambda: service_mocks["auth"]
    app.dependency_overrides[get_budget_service] = lambda: service_mocks["budget"]
    app.dependency_overrides[get_income_service] = lambda: service_mocks["income"]
    app.dependency_overrides[get_expense_service] = lambda: service_mocks["expense"]
    app.dependency_overrides[get_report_service] = lambda: service_mocks["report"]

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(token_data):
    """Authenticated client with all services mocked for testing protected endpoints."""
    mock_auth_service = Mock()
    mock_expense_service = Mock()
    mock_budget_service = Mock()
    mock_income_service = Mock()
    mock_report_service = Mock()

    app.dependency_overrides[get_db] = _fake_db
    app.dependency_overrides[get_current_user] = lambda: token_data
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_expense_service] = lambda: mock_expense_service
    app.dependency_overrides[get_budget_service] = lambda: mock_budget_service
    app.dependency_overrides[get_income_service] = lambda: mock_income_service
    app.dependency_overrides[get_report_service] = lambda: mock_report_service

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield {
            "client": test_client,
            "auth_service": mock_auth_service,
            "expense_service": mock_expense_service,
            "budget_service": mock_budget_service,
            "income_service": mock_income_service,
            "report_service": mock_report_service,
        }

    app.dependency_overrides.clear()


@pytest.fixture
def unauth_client():
    """Unauthenticated client with all services mocked for testing public endpoints."""
    mock_auth_service = Mock()
    mock_expense_service = Mock()
    mock_budget_service = Mock()
    mock_income_service = Mock()
    mock_report_service = Mock()

    app.dependency_overrides[get_db] = _fake_db
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_expense_service] = lambda: mock_expense_service
    app.dependency_overrides[get_budget_service] = lambda: mock_budget_service
    app.dependency_overrides[get_income_service] = lambda: mock_income_service
    app.dependency_overrides[get_report_service] = lambda: mock_report_service

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield {
            "client": test_client,
            "auth_service": mock_auth_service,
            "expense_service": mock_expense_service,
            "budget_service": mock_budget_service,
            "income_service": mock_income_service,
            "report_service": mock_report_service,
        }

    app.dependency_overrides.clear()


def assert_error_shape(body: dict, expected_status: int, expected_error_code: str):
    assert body.get("status") == expected_status, (
        f"Expected status {expected_status}, got {body.get('status')}"
    )
    assert body.get("errorCode") == expected_error_code, (
        f"Expected errorCode '{expected_error_code}', got {body.get('errorCode')}"
    )
    for field in ("timestamp", "error", "message", "path"):
        assert field in body, f"Missing '{field}' in error response"


def assert_validation_error(body: dict):
    assert_error_shape(body, 400, "VAL-001")


def assert_unauthorized(body: dict):
    assert_error_shape(body, 401, "AUTH-001")
