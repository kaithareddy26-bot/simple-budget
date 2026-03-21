"""
HTTP Controller-layer tests: API endpoint behaviour across all controllers.

Consolidated test suite covering:
  - Success paths (correct HTTP status and response shape)
  - Validation errors (malformed request bodies)
  - Authentication failures (missing/invalid tokens on protected endpoints)
  - Service-layer errors (business logic failures mapped to HTTP status)
  - Error envelope consistency (Week-4 specification shape on all errors)

Tests exercise FastAPI routes directly through TestClient.
Service dependencies are mocked — we are testing HTTP wiring, not business logic.

Merged from: test_controllers.py + unique tests from test_api_controllers.py
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from app.main import app
from app.schemas.error_schemas import ErrorCodes
from tests.conftest import (
    make_user,
    make_expense,
    make_budget,
    make_income,
    FIXED_USER_ID,
    FIXED_EXPENSE_ID,
    FIXED_BUDGET_ID,
    FIXED_INCOME_ID,
    assert_error_shape,
    assert_validation_error,
    assert_unauthorized,
)


# ===========================================================================
# HEALTH / ROOT ENDPOINTS
# ===========================================================================


def test_health_endpoint(client):
    """GET /health returns service health status."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint(client):
    """GET / returns API information."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Budgeting Application API"
    assert data["docs"] == "/docs"


# ===========================================================================
# AUTH CONTROLLER
# ===========================================================================


class TestAuthController:
    """Tests for /api/v1/auth endpoints."""

    # --- POST /auth/register ---

    def test_register_success(self, unauth_client):
        client = unauth_client["client"]
        svc = unauth_client["auth_service"]
        svc.register_user.return_value = make_user()

        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "securepass123",
                "full_name": "New User",
            },
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "test@example.com"
        assert "id" in body
        assert "full_name" in body

    def test_register_duplicate_email_returns_409(self, unauth_client):
        client = unauth_client["client"]
        svc = unauth_client["auth_service"]
        svc.register_user.side_effect = ValueError(
            f"{ErrorCodes.USER_EXISTS}: User already exists"
        )

        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "dupe@example.com",
                "password": "securepass123",
                "full_name": "Dupe User",
            },
        )

        assert resp.status_code == 409
        assert_error_shape(resp.json(), 409, ErrorCodes.USER_EXISTS)

    def test_register_missing_email_returns_422_or_400(self, unauth_client):
        """Pydantic validation — missing required field."""
        client = unauth_client["client"]

        resp = client.post(
            "/api/v1/auth/register",
            json={"password": "securepass123", "full_name": "No Email"},
        )

        assert resp.status_code == 400  # mapped by validation_exception_handler

    def test_register_short_password_returns_400(self, unauth_client):
        client = unauth_client["client"]

        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "x@example.com",
                "password": "short",  # < 8 chars
                "full_name": "Test",
            },
        )

        assert resp.status_code == 400
        assert_validation_error(resp.json())

    def test_register_invalid_email_format_returns_400(self, unauth_client):
        client = unauth_client["client"]

        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "securepass123",
                "full_name": "Test",
            },
        )

        assert resp.status_code == 400
        assert_validation_error(resp.json())

    def test_register_empty_body_returns_400(self, unauth_client):
        client = unauth_client["client"]
        resp = client.post("/api/v1/auth/register", json={})
        assert resp.status_code == 400

    # --- POST /auth/login ---

    def test_login_success(self, unauth_client):
        client = unauth_client["client"]
        svc = unauth_client["auth_service"]
        svc.login_user.return_value = "jwt.access.token"

        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"] == "jwt.access.token"
        assert body["token_type"] == "bearer"

    def test_login_invalid_credentials_returns_401(self, unauth_client):
        client = unauth_client["client"]
        svc = unauth_client["auth_service"]
        svc.login_user.side_effect = ValueError(
            f"{ErrorCodes.AUTH_INVALID_CREDENTIALS}: Invalid email or password"
        )

        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "x@example.com", "password": "wrongpass"},
        )

        assert resp.status_code == 401
        assert_error_shape(resp.json(), 401, ErrorCodes.AUTH_INVALID_CREDENTIALS)

    def test_login_missing_password_returns_400(self, unauth_client):
        client = unauth_client["client"]
        resp = client.post(
            "/api/v1/auth/login", json={"email": "test@example.com"}
        )
        assert resp.status_code == 400

    def test_login_empty_body_returns_400(self, unauth_client):
        client = unauth_client["client"]
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 400


# ===========================================================================
# EXPENSE CONTROLLER
# ===========================================================================


class TestExpenseController:
    """Tests for /api/v1/expenses endpoints."""

    # --- POST /expenses (add expense) ---

    def test_add_expense_success(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["expense_service"]
        svc.add_expense.return_value = make_expense()

        resp = client.post(
            "/api/v1/expenses",
            json={"amount": "150.00", "category": "Groceries", "date": "2024-03-10"},
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["amount"] == "150.00"
        assert body["category"] == "Groceries"
        assert "expenseId" in body
        assert "userId" in body

    def test_add_expense_with_note(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["expense_service"]
        svc.add_expense.return_value = make_expense(note="Weekly shop")

        resp = client.post(
            "/api/v1/expenses",
            json={
                "amount": "150.00",
                "category": "Groceries",
                "date": "2024-03-10",
                "note": "Weekly shop",
            },
        )

        assert resp.status_code == 201
        assert resp.json()["note"] == "Weekly shop"

    def test_add_expense_missing_amount_returns_400(self, auth_client):
        client = auth_client["client"]

        resp = client.post(
            "/api/v1/expenses",
            json={"category": "Groceries", "date": "2024-03-10"},
        )

        assert resp.status_code == 400
        assert_validation_error(resp.json())

    def test_add_expense_missing_category_returns_400(self, auth_client):
        client = auth_client["client"]

        resp = client.post(
            "/api/v1/expenses",
            json={"amount": "50.00", "date": "2024-03-10"},
        )

        assert resp.status_code == 400

    def test_add_expense_missing_date_returns_400(self, auth_client):
        client = auth_client["client"]

        resp = client.post(
            "/api/v1/expenses",
            json={"amount": "50.00", "category": "Food"},
        )

        assert resp.status_code == 400

    def test_add_expense_invalid_date_format_returns_400(self, auth_client):
        client = auth_client["client"]

        resp = client.post(
            "/api/v1/expenses",
            json={"amount": "50.00", "category": "Food", "date": "not-a-date"},
        )

        assert resp.status_code == 400

    def test_add_expense_empty_body_returns_400(self, auth_client):
        client = auth_client["client"]
        resp = client.post("/api/v1/expenses", json={})
        assert resp.status_code == 400

    def test_add_expense_service_invalid_amount_returns_400(self, auth_client):
        """Service-layer business rule: zero/negative amount."""
        client = auth_client["client"]
        svc = auth_client["expense_service"]
        svc.add_expense.side_effect = ValueError(
            f"{ErrorCodes.EXP_INVALID_AMOUNT}: Amount must be positive"
        )

        resp = client.post(
            "/api/v1/expenses",
            json={"amount": "0.00", "category": "Food", "date": "2024-03-10"},
        )

        assert resp.status_code == 400
        assert_error_shape(resp.json(), 400, ErrorCodes.EXP_INVALID_AMOUNT)

    def test_add_expense_service_invalid_category_returns_400(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["expense_service"]
        svc.add_expense.side_effect = ValueError(
            f"{ErrorCodes.EXP_INVALID_CATEGORY}: Category cannot be blank"
        )

        resp = client.post(
            "/api/v1/expenses",
            json={"amount": "50.00", "category": "   ", "date": "2024-03-10"},
        )

        assert resp.status_code == 400
        assert_error_shape(resp.json(), 400, ErrorCodes.EXP_INVALID_CATEGORY)

    # --- GET /expenses/current-month ---

    def test_get_current_month_expenses_success(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["expense_service"]
        svc.get_current_month_expenses.return_value = [
            make_expense(),
            make_expense(expense_id=uuid4(), amount=Decimal("75.00"), category="Transport"),
        ]

        resp = client.get("/api/v1/expenses/current-month")

        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) == 2

    def test_get_current_month_expenses_empty_list(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["expense_service"]
        svc.get_current_month_expenses.return_value = []

        resp = client.get("/api/v1/expenses/current-month")

        assert resp.status_code == 200
        assert resp.json() == []


# ===========================================================================
# BUDGET CONTROLLER
# ===========================================================================


class TestBudgetController:
    """Tests for /api/v1/budgets endpoints."""

    # --- POST /budgets ---

    def test_create_budget_success(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["budget_service"]
        svc.create_budget.return_value = make_budget()

        resp = client.post(
            "/api/v1/budgets",
            json={"month": "2024-03", "amount": "5000.00"},
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["month"] == "2024-03"
        assert "budgetId" in body
        assert "userId" in body

    def test_create_budget_duplicate_returns_409(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["budget_service"]
        svc.create_budget.side_effect = ValueError(
            f"{ErrorCodes.BUD_ALREADY_EXISTS}: Budget already exists"
        )

        resp = client.post(
            "/api/v1/budgets",
            json={"month": "2024-03", "amount": "5000.00"},
        )

        assert resp.status_code == 409
        assert_error_shape(resp.json(), 409, ErrorCodes.BUD_ALREADY_EXISTS)

    def test_create_budget_invalid_month_format_returns_400(self, auth_client):
        client = auth_client["client"]

        resp = client.post(
            "/api/v1/budgets",
            json={"month": "03-2024", "amount": "5000.00"},  # wrong format
        )

        assert resp.status_code == 400

    def test_create_budget_invalid_month_value_returns_400(self, auth_client):
        """Month 13 is invalid."""
        client = auth_client["client"]

        resp = client.post(
            "/api/v1/budgets",
            json={"month": "2024-13", "amount": "5000.00"},
        )

        assert resp.status_code == 400

    def test_create_budget_negative_amount_returns_400(self, auth_client):
        client = auth_client["client"]

        resp = client.post(
            "/api/v1/budgets",
            json={"month": "2024-03", "amount": "-100.00"},
        )

        assert resp.status_code == 400

    def test_create_budget_zero_amount_returns_400(self, auth_client):
        client = auth_client["client"]

        resp = client.post(
            "/api/v1/budgets",
            json={"month": "2024-03", "amount": "0"},
        )

        assert resp.status_code == 400

    def test_create_budget_missing_fields_returns_400(self, auth_client):
        client = auth_client["client"]
        resp = client.post("/api/v1/budgets", json={})
        assert resp.status_code == 400

    # --- GET /budgets/current-month ---

    def test_get_current_month_budget_success(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["budget_service"]
        svc.get_current_month_budget.return_value = make_budget()

        resp = client.get("/api/v1/budgets/current-month")

        assert resp.status_code == 200
        body = resp.json()
        assert "budgetId" in body
        assert body["month"] == "2024-03"

    def test_get_current_month_budget_not_found_returns_404(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["budget_service"]
        svc.get_current_month_budget.side_effect = ValueError(
            f"{ErrorCodes.BUD_NOT_FOUND}: Budget not found"
        )

        resp = client.get("/api/v1/budgets/current-month")

        assert resp.status_code == 404
        assert_error_shape(resp.json(), 404, ErrorCodes.BUD_NOT_FOUND)

    # --- GET /budgets/{budgetId} ---

    def test_get_budget_by_id_success(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["budget_service"]
        svc.get_budget_by_id.return_value = make_budget()

        resp = client.get(f"/api/v1/budgets/{FIXED_BUDGET_ID}")

        assert resp.status_code == 200
        assert resp.json()["budgetId"] == str(FIXED_BUDGET_ID)

    def test_get_budget_by_id_not_found_returns_404(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["budget_service"]
        svc.get_budget_by_id.side_effect = ValueError(
            f"{ErrorCodes.BUD_NOT_FOUND}: Budget not found"
        )

        resp = client.get(f"/api/v1/budgets/{FIXED_BUDGET_ID}")

        assert resp.status_code == 404

    def test_get_budget_by_id_wrong_user_returns_403(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["budget_service"]
        svc.get_budget_by_id.side_effect = ValueError(
            f"{ErrorCodes.BUD_UNAUTHORIZED}: Access forbidden"
        )

        resp = client.get(f"/api/v1/budgets/{FIXED_BUDGET_ID}")

        assert resp.status_code == 403

    def test_get_budget_invalid_uuid_returns_400(self, auth_client):
        client = auth_client["client"]
        resp = client.get("/api/v1/budgets/not-a-uuid")
        assert resp.status_code == 400

    # --- PUT /budgets/{budgetId} ---

    def test_update_budget_success(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["budget_service"]
        svc.update_budget_amount.return_value = make_budget(amount=Decimal("6000.00"))

        resp = client.put(
            f"/api/v1/budgets/{FIXED_BUDGET_ID}",
            json={"amount": "6000.00"},
        )

        assert resp.status_code == 200
        assert resp.json()["totalAmount"] == "6000.00"

    def test_update_budget_not_found_returns_404(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["budget_service"]
        svc.update_budget_amount.side_effect = ValueError(
            f"{ErrorCodes.BUD_NOT_FOUND}: Budget not found"
        )

        resp = client.put(
            f"/api/v1/budgets/{FIXED_BUDGET_ID}", json={"amount": "6000.00"}
        )

        assert resp.status_code == 404

    def test_update_budget_zero_amount_returns_400(self, auth_client):
        client = auth_client["client"]
        resp = client.put(
            f"/api/v1/budgets/{FIXED_BUDGET_ID}", json={"amount": "0"}
        )
        assert resp.status_code == 400

    def test_update_budget_missing_amount_returns_400(self, auth_client):
        client = auth_client["client"]
        resp = client.put(f"/api/v1/budgets/{FIXED_BUDGET_ID}", json={})
        assert resp.status_code == 400


# ===========================================================================
# INCOME CONTROLLER
# ===========================================================================


class TestIncomeController:
    """Tests for /api/v1/incomes endpoints."""

    def test_add_income_success(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["income_service"]
        svc.add_income.return_value = make_income()

        resp = client.post(
            "/api/v1/incomes",
            json={"amount": "3500.00", "source": "Monthly Salary", "date": "2024-03-15"},
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["amount"] == "3500.00"
        assert body["source"] == "Monthly Salary"
        assert "incomeId" in body

    def test_add_income_missing_amount_returns_400(self, auth_client):
        client = auth_client["client"]
        resp = client.post(
            "/api/v1/incomes",
            json={"source": "Salary", "date": "2024-03-15"},
        )
        assert resp.status_code == 400

    def test_add_income_missing_source_returns_400(self, auth_client):
        client = auth_client["client"]
        resp = client.post(
            "/api/v1/incomes",
            json={"amount": "3500.00", "date": "2024-03-15"},
        )
        assert resp.status_code == 400

    def test_add_income_missing_date_returns_400(self, auth_client):
        client = auth_client["client"]
        resp = client.post(
            "/api/v1/incomes",
            json={"amount": "3500.00", "source": "Salary"},
        )
        assert resp.status_code == 400

    def test_add_income_zero_amount_returns_400(self, auth_client):
        """Schema enforces gt=0."""
        client = auth_client["client"]
        resp = client.post(
            "/api/v1/incomes",
            json={"amount": "0", "source": "Salary", "date": "2024-03-15"},
        )
        assert resp.status_code == 400

    def test_add_income_negative_amount_returns_400(self, auth_client):
        client = auth_client["client"]
        resp = client.post(
            "/api/v1/incomes",
            json={"amount": "-100.00", "source": "Salary", "date": "2024-03-15"},
        )
        assert resp.status_code == 400

    def test_add_income_service_invalid_source_returns_400(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["income_service"]
        svc.add_income.side_effect = ValueError(
            f"{ErrorCodes.INC_INVALID_SOURCE}: Source cannot be blank"
        )

        resp = client.post(
            "/api/v1/incomes",
            json={"amount": "100.00", "source": "   ", "date": "2024-03-15"},
        )

        assert resp.status_code == 400
        assert_error_shape(resp.json(), 400, ErrorCodes.INC_INVALID_SOURCE)

    def test_add_income_empty_body_returns_400(self, auth_client):
        client = auth_client["client"]
        resp = client.post("/api/v1/incomes", json={})
        assert resp.status_code == 400


# ===========================================================================
# REPORT CONTROLLER
# ===========================================================================


class TestReportController:
    """Tests for /api/v1/reports endpoints."""

    def _make_summary(self):
        return {
            "month": "2024-03",
            "total_income": Decimal("3500.00"),
            "total_expenses": Decimal("1500.00"),
            "net_balance": Decimal("2000.00"),
            "expenses_by_category": {"Groceries": Decimal("500.00")},
        }

    def test_get_monthly_summary_success(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["report_service"]
        svc.get_monthly_summary.return_value = self._make_summary()
        svc.utc_now.return_value = "2024-03-31T00:00:00Z"

        resp = client.get("/api/v1/reports/summary?month=2024-03")

        assert resp.status_code == 200
        body = resp.json()
        assert body["month"] == "2024-03"
        assert "totalIncome" in body
        assert "totalExpenses" in body
        assert "net" in body
        assert "byCategory" in body

    def test_get_monthly_summary_missing_month_returns_400(self, auth_client):
        client = auth_client["client"]
        resp = client.get("/api/v1/reports/summary")
        assert resp.status_code == 400

    def test_get_monthly_summary_invalid_month_format_returns_400(self, auth_client):
        client = auth_client["client"]
        resp = client.get("/api/v1/reports/summary?month=March-2024")
        assert resp.status_code == 400

    def test_get_monthly_summary_invalid_month_partial_returns_400(self, auth_client):
        """e.g. just '2024' without the month part."""
        client = auth_client["client"]
        resp = client.get("/api/v1/reports/summary?month=2024")
        assert resp.status_code == 400

    def test_get_monthly_summary_service_error_returns_400(self, auth_client):
        client = auth_client["client"]
        svc = auth_client["report_service"]
        svc.get_monthly_summary.side_effect = ValueError(
            f"{ErrorCodes.RPT_INVALID_MONTH}: Invalid month format"
        )

        resp = client.get("/api/v1/reports/summary?month=2024-03")

        assert resp.status_code == 400
        assert_error_shape(resp.json(), 400, ErrorCodes.RPT_INVALID_MONTH)
