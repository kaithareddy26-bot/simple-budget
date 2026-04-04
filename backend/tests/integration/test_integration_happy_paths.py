"""
Integration tests: Happy path end-to-end flows

These tests verify correct system behaviour, not just error handling.
Each test asserts both:
  1. The HTTP response (status code + body)
  2. The resulting database state (via direct SQL query)

This catches bugs where the API returns 200 but nothing was persisted,
or where data is stored incorrectly (wrong user_id, wrong amount, etc.).

Run:
    pytest tests/integration/test_integration_happy_paths.py -v
Requires:
    docker-compose -f docker-compose.test.yml up -d
"""

import pytest
from sqlalchemy import text
from tests.integration.conftest import register_and_login, auth_headers


class TestAuthHappyPath:

    def test_register_creates_user_in_db(self, integration_client, db_session):
        """POST /register → user row exists in DB with correct values."""
        resp = integration_client.post(
            "/api/v1/auth/register",
            json={"email": "reg_happy@int.com", "password": "securepass123",
                  "full_name": "Happy User"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "reg_happy@int.com"
        assert "id" in body

        row = db_session.execute(
            text("SELECT email, full_name FROM users WHERE email = :e"),
            {"e": "reg_happy@int.com"},
        ).fetchone()
        assert row is not None
        assert row.full_name == "Happy User"

    def test_password_stored_as_bcrypt_hash(self, integration_client, db_session):
        """The stored password must be a bcrypt hash, never plaintext."""
        integration_client.post(
            "/api/v1/auth/register",
            json={"email": "hash_check@int.com", "password": "plaintext123",
                  "full_name": "Hash"},
        )
        row = db_session.execute(
            text("SELECT hashed_password FROM users WHERE email = :e"),
            {"e": "hash_check@int.com"},
        ).fetchone()
        assert row is not None
        assert row.hashed_password != "plaintext123", (
            "Password stored in plaintext — critical security bug"
        )
        assert row.hashed_password.startswith("$2b$"), (
            "Password is not a bcrypt hash"
        )

    def test_login_returns_bearer_token(self, integration_client):
        """Successful login returns access_token with token_type bearer."""
        integration_client.post(
            "/api/v1/auth/register",
            json={"email": "login_happy@int.com", "password": "password123",
                  "full_name": "Login"},
        )
        resp = integration_client.post(
            "/api/v1/auth/login",
            json={"email": "login_happy@int.com", "password": "password123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 20


class TestExpenseHappyPath:

    @pytest.fixture(autouse=True)
    def setup(self, integration_client):
        self.token = register_and_login(
            integration_client, "exp_happy@int.com", "password123"
        )
        self.h = auth_headers(self.token)

    def test_add_expense_persists_to_db(self, integration_client, db_session):
        """POST /expenses → row in DB with correct values."""
        resp = integration_client.post(
            "/api/v1/expenses",
            json={"amount": "149.99", "category": "Groceries",
                  "date": "2024-03-10", "note": "Weekly shop"},
            headers=self.h,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert "expenseId" in body
        expense_id = body["expenseId"]

        row = db_session.execute(
            text("SELECT amount, category, note FROM expenses WHERE id = :id"),
            {"id": expense_id},
        ).fetchone()
        assert row is not None
        assert float(row.amount) == 149.99
        assert row.category == "Groceries"
        assert row.note == "Weekly shop"

    def test_expense_belongs_to_correct_user(self, integration_client, db_session):
        """Expense must be stored with the authenticated user's ID."""
        resp = integration_client.post(
            "/api/v1/expenses",
            json={"amount": "50.00", "category": "Transport", "date": "2024-03-05"},
            headers=self.h,
        )
        expense_id = resp.json()["expenseId"]

        row = db_session.execute(
            text("SELECT user_id FROM expenses WHERE id = :id"),
            {"id": expense_id},
        ).fetchone()
        assert row is not None

        user_row = db_session.execute(
            text("SELECT id FROM users WHERE email = :e"),
            {"e": "exp_happy@int.com"},
        ).fetchone()
        assert str(row.user_id) == str(user_row.id), (
            "Expense stored with wrong user_id"
        )

    def test_user_only_sees_own_expenses(self, integration_client):
        """GET /expenses/current-month must not return other users' data."""
        integration_client.post(
            "/api/v1/expenses",
            json={"amount": "50.00", "category": "Transport", "date": "2024-03-05"},
            headers=self.h,
        )
        # Another user adds a larger expense
        other_token = register_and_login(
            integration_client, "other_exp@int.com", "password123"
        )
        integration_client.post(
            "/api/v1/expenses",
            json={"amount": "9999.00", "category": "Luxury", "date": "2024-03-05"},
            headers=auth_headers(other_token),
        )

        resp = integration_client.get(
            "/api/v1/expenses/current-month", headers=self.h
        )
        assert resp.status_code == 200
        amounts = [float(e["amount"]) for e in resp.json()]
        assert 9999.00 not in amounts, "Saw another user's expense"


class TestBudgetHappyPath:

    @pytest.fixture(autouse=True)
    def setup(self, integration_client):
        self.token = register_and_login(
            integration_client, "bud_happy@int.com", "password123"
        )
        self.h = auth_headers(self.token)

    def test_create_then_retrieve_budget(self, integration_client, db_session):
        """POST then GET by ID — both response and DB must agree."""
        resp = integration_client.post(
            "/api/v1/budgets",
            json={"month": "2024-05", "amount": "4500.00"},
            headers=self.h,
        )
        assert resp.status_code == 201
        budget_id = resp.json()["budgetId"]

        # Retrieve via API
        resp = integration_client.get(
            f"/api/v1/budgets/{budget_id}", headers=self.h
        )
        assert resp.status_code == 200
        assert resp.json()["month"] == "2024-05"
        assert float(resp.json()["totalAmount"]) == 4500.00

        # Verify in DB
        row = db_session.execute(
            text("SELECT month, amount FROM budgets WHERE id = :id"),
            {"id": budget_id},
        ).fetchone()
        assert row is not None
        assert row.month == "2024-05"
        assert float(row.amount) == 4500.00

    def test_update_budget_reflected_in_db(self, integration_client, db_session):
        """PUT budget amount → DB row must show new value."""
        resp = integration_client.post(
            "/api/v1/budgets",
            json={"month": "2024-07", "amount": "3000.00"},
            headers=self.h,
        )
        budget_id = resp.json()["budgetId"]

        put_resp = integration_client.put(
            f"/api/v1/budgets/{budget_id}",
            json={"amount": "5500.00"},
            headers=self.h,
        )
        assert put_resp.status_code == 200
        assert float(put_resp.json()["totalAmount"]) == 5500.00

        row = db_session.execute(
            text("SELECT amount FROM budgets WHERE id = :id"),
            {"id": budget_id},
        ).fetchone()
        assert float(row.amount) == 5500.00

    def test_get_current_month_budget(self, integration_client):
        """Create a budget for the current month and retrieve it."""
        import datetime
        current_month = datetime.date.today().strftime("%Y-%m")
        integration_client.post(
            "/api/v1/budgets",
            json={"month": current_month, "amount": "2000.00"},
            headers=self.h,
        )
        resp = integration_client.get(
            "/api/v1/budgets/current-month", headers=self.h
        )
        assert resp.status_code == 200
        assert resp.json()["month"] == current_month


class TestReportHappyPath:

    @pytest.fixture(autouse=True)
    def setup(self, integration_client):
        self.token = register_and_login(
            integration_client, "rep_happy@int.com", "password123"
        )
        self.h = auth_headers(self.token)

    def test_report_aggregates_real_data_correctly(self, integration_client):
        """
        Add income + expenses to the DB via API.
        Assert the report totals exactly match what was inserted.
        This is the most important integration test: it proves the
        aggregation logic is correct end-to-end, not just mocked.
        """
        integration_client.post(
            "/api/v1/incomes",
            json={"amount": "5000.00", "source": "Salary", "date": "2024-03-01"},
            headers=self.h,
        )
        integration_client.post(
            "/api/v1/expenses",
            json={"amount": "200.00", "category": "Groceries", "date": "2024-03-05"},
            headers=self.h,
        )
        integration_client.post(
            "/api/v1/expenses",
            json={"amount": "150.00", "category": "Transport", "date": "2024-03-10"},
            headers=self.h,
        )

        resp = integration_client.get(
            "/api/v1/reports/summary?month=2024-03", headers=self.h
        )
        assert resp.status_code == 200
        body = resp.json()
        assert float(body["totalIncome"]) == 5000.00
        assert float(body["totalExpenses"]) == 350.00
        assert float(body["net"]) == 4650.00
        assert "Groceries" in body["byCategory"]
        assert "Transport" in body["byCategory"]
        assert float(body["byCategory"]["Groceries"]) == 200.00
        assert float(body["byCategory"]["Transport"]) == 150.00

    def test_report_only_includes_own_data(self, integration_client):
        """Report for user A must not include user B's transactions."""
        other_token = register_and_login(
            integration_client, "other_rep@int.com", "password123"
        )
        integration_client.post(
            "/api/v1/incomes",
            json={"amount": "99999.00", "source": "Other", "date": "2024-04-01"},
            headers=auth_headers(other_token),
        )

        resp = integration_client.get(
            "/api/v1/reports/summary?month=2024-04", headers=self.h
        )
        assert resp.status_code == 200
        assert float(resp.json()["totalIncome"]) == 0.0, (
            "Report included another user's income"
        )