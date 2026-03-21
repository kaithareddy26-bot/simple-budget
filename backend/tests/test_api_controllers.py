from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.dependencies import get_current_user
from app.main import app


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Budgeting Application API"
    assert data["docs"] == "/docs"


def test_register_user_success(client, service_mocks):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "person@example.com",
            "password": "strongpassword",
            "full_name": "Person Name",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["full_name"] == "New User"


def test_register_user_validation_error_returns_week4_shape(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "bad-email", "password": "short", "full_name": ""},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["errorCode"] == "VAL-001"
    assert body["status"] == 400
    assert body["path"] == "/api/v1/auth/register"
    assert len(body["details"]) >= 1


def test_login_user_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.com", "password": "strongpassword"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_budget_create_success(client, apply_auth_override, sample_user_id):
    apply_auth_override()
    now = datetime.now(timezone.utc)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        user_id=sample_user_id, email="tester@example.com"
    )

    response = client.post(
        "/api/v1/budgets",
        json={"month": "2026-03", "amount": "1200.00"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["month"] == "2026-03"
    assert body["totalAmount"] == "1200.00"
    assert "budgetId" in body
    assert "createdAt" in body
    assert now.tzinfo is not None


def test_budget_create_invalid_month_returns_400(client, apply_auth_override):
    apply_auth_override()
    response = client.post(
        "/api/v1/budgets",
        json={"month": "2026/03", "amount": "1200.00"},
    )

    assert response.status_code == 400
    assert response.json()["errorCode"] == "VAL-001"


def test_budget_service_error_maps_to_conflict(client, apply_auth_override, service_mocks):
    apply_auth_override()
    service_mocks["budget"].create_budget = lambda **_: (_ for _ in ()).throw(
        ValueError("BUD-002:Budget already exists for this month")
    )

    response = client.post(
        "/api/v1/budgets",
        json={"month": "2026-03", "amount": "1200.00"},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["errorCode"] == "BUD-002"
    assert body["error"] == "Conflict"


def test_budget_get_by_id_success(client, apply_auth_override):
    apply_auth_override()
    response = client.get(f"/api/v1/budgets/{uuid4()}")

    assert response.status_code == 200
    body = response.json()
    assert "budgetId" in body
    assert body["month"] == "2026-03"


def test_budget_update_success(client, apply_auth_override):
    apply_auth_override()
    response = client.put(
        f"/api/v1/budgets/{uuid4()}",
        json={"amount": "1400.00"},
    )

    assert response.status_code == 200
    assert response.json()["totalAmount"] == "1400.00"


def test_income_add_success(client, apply_auth_override):
    apply_auth_override()
    response = client.post(
        "/api/v1/incomes",
        json={"amount": "3000.00", "source": "Salary", "date": "2026-03-10"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "Salary"
    assert body["amount"] == "3000.00"


def test_expense_add_success(client, apply_auth_override):
    apply_auth_override()
    response = client.post(
        "/api/v1/expenses",
        json={
            "amount": "45.00",
            "category": "Food",
            "date": "2026-03-10",
            "note": "Lunch",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "Food"
    assert body["amount"] == "45.00"


def test_expense_current_month_success(client, apply_auth_override):
    apply_auth_override()
    response = client.get("/api/v1/expenses/current-month")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["category"] == "Food"


def test_report_summary_success(client, apply_auth_override):
    apply_auth_override()
    response = client.get("/api/v1/reports/summary?month=2026-03")

    assert response.status_code == 200
    body = response.json()
    assert body["month"] == "2026-03"
    assert body["totalIncome"] == "3000.00"
    assert body["byCategory"]["Food"] == "45.00"


def test_report_summary_invalid_query_shape(client, apply_auth_override):
    apply_auth_override()
    response = client.get("/api/v1/reports/summary?month=2026/03")

    assert response.status_code == 400
    body = response.json()
    assert body["errorCode"] == "VAL-001"
    assert body["path"] == "/api/v1/reports/summary"


def test_general_exception_maps_to_500(client, apply_auth_override, service_mocks):
    apply_auth_override()
    service_mocks["expense"].add_expense = lambda **_: (_ for _ in ()).throw(
        RuntimeError("boom")
    )

    response = client.post(
        "/api/v1/expenses",
        json={
            "amount": "45.00",
            "category": "Food",
            "date": "2026-03-10",
            "note": "Lunch",
        },
    )

    assert response.status_code == 500
    body = response.json()
    assert body["errorCode"] == "SYS-001"
    assert body["message"] == "Internal server error"


PROTECTED_ENDPOINT_CASES = [
    ("post", "/api/v1/budgets", {"json": {"month": "2026-03", "amount": "10.00"}}),
    ("get", "/api/v1/budgets/current-month", {}),
    ("get", f"/api/v1/budgets/{uuid4()}", {}),
    ("put", f"/api/v1/budgets/{uuid4()}", {"json": {"amount": "20.00"}}),
    (
        "post",
        "/api/v1/incomes",
        {"json": {"amount": "100.00", "source": "Salary", "date": "2026-03-10"}},
    ),
    (
        "post",
        "/api/v1/expenses",
        {
            "json": {
                "amount": "55.00",
                "category": "Food",
                "date": "2026-03-10",
                "note": "Lunch",
            }
        },
    ),
    ("get", "/api/v1/expenses/current-month", {}),
    ("get", "/api/v1/reports/summary?month=2026-03", {}),
]


@pytest.mark.parametrize("method,path,kwargs", PROTECTED_ENDPOINT_CASES)
def test_missing_token_protected_endpoints(method, path, kwargs, client):
    app.dependency_overrides.pop(get_current_user, None)
    response = client.request(method=method.upper(), url=path, **kwargs)

    assert response.status_code == 401
    body = response.json()
    assert body["errorCode"] == "AUTH-001"
    assert body["message"] == "Missing or invalid token"


@pytest.mark.parametrize("method,path,kwargs", PROTECTED_ENDPOINT_CASES)
def test_invalid_token_protected_endpoints(method, path, kwargs, client):
    app.dependency_overrides.pop(get_current_user, None)
    headers = {"Authorization": "Bearer not-a-valid-token"}
    response = client.request(method=method.upper(), url=path, headers=headers, **kwargs)

    assert response.status_code == 401
    body = response.json()
    assert body["errorCode"] == "AUTH-001"
    assert body["message"] == "Missing or invalid token"


def test_budget_current_month_success(client, apply_auth_override):
    apply_auth_override()
    response = client.get("/api/v1/budgets/current-month")

    assert response.status_code == 200
    body = response.json()
    assert body["month"] == "2026-03"
    assert body["totalAmount"] == "1200.00"


def test_login_user_invalid_email_shape(client, service_mocks):
    service_mocks["auth"].login_user = lambda **_: (_ for _ in ()).throw(
        ValueError("AUTH-004:Invalid credentials")
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.com", "password": "wrongpass"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["errorCode"] == "AUTH-004"
    assert body["error"] == "Unauthorized"


def test_income_input_validation_shape(client, apply_auth_override):
    apply_auth_override()
    response = client.post(
        "/api/v1/incomes",
        json={"amount": "0", "source": "", "date": "bad-date"},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["errorCode"] == "VAL-001"
    assert isinstance(body.get("details"), list)


def test_expense_input_validation_shape(client, apply_auth_override):
    apply_auth_override()
    response = client.post(
        "/api/v1/expenses",
        json={"amount": "x", "category": "", "date": "bad-date"},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["errorCode"] == "VAL-001"
