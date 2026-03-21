from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies import (
    get_auth_service,
    get_budget_service,
    get_current_user,
    get_expense_service,
    get_income_service,
    get_report_service,
)
from app.main import app
from app.models.base import settings as base_settings
from app.schemas.auth_schemas import TokenData


@pytest.fixture
def sample_user_id():
    return uuid4()


@pytest.fixture
def token_data(sample_user_id):
    return TokenData(user_id=sample_user_id, email="tester@example.com")


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
    original_run_db_init = base_settings.RUN_DB_INIT
    base_settings.RUN_DB_INIT = False

    app.dependency_overrides[get_auth_service] = lambda: service_mocks["auth"]
    app.dependency_overrides[get_budget_service] = lambda: service_mocks["budget"]
    app.dependency_overrides[get_income_service] = lambda: service_mocks["income"]
    app.dependency_overrides[get_expense_service] = lambda: service_mocks["expense"]
    app.dependency_overrides[get_report_service] = lambda: service_mocks["report"]

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    base_settings.RUN_DB_INIT = original_run_db_init


@pytest.fixture
def apply_auth_override(token_data):
    def _apply(user=None):
        current = user or token_data
        app.dependency_overrides[get_current_user] = lambda: current
        return current

    return _apply