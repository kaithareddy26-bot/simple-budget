"""
Integration tests: Error Contract Validation

Every failure mode must produce the Week-4 error envelope:
    { timestamp, status, error, errorCode, message, path }

These tests hit real API endpoints backed by a real PostgreSQL database.
They validate HTTP status codes, error codes, and envelope completeness
across auth, expense, budget, income, and report endpoints.

Run:
    pytest tests/integration/test_integration_errors.py -v
Requires:
    docker-compose -f docker-compose.test.yml up -d
"""

import pytest
from tests.integration.conftest import register_and_login, auth_headers

# All fields required by the Week-4 error contract
ENVELOPE_FIELDS = {"timestamp", "status", "error", "errorCode", "message", "path"}


def assert_contract(resp, expected_status: int, expected_code: str):
    """
    Assert HTTP status + complete envelope shape + correct errorCode.
    Prints the full body on failure so errors are easy to diagnose.
    """
    assert resp.status_code == expected_status, (
        f"Expected HTTP {expected_status}, got {resp.status_code}. "
        f"Body: {resp.json()}"
    )
    body = resp.json()
    missing = ENVELOPE_FIELDS - set(body.keys())
    assert not missing, (
        f"Envelope missing fields {missing}. Body: {body}"
    )
    assert body["errorCode"] == expected_code, (
        f"Expected errorCode '{expected_code}', got '{body.get('errorCode')}'. "
        f"Body: {body}"
    )
    assert body["status"] == expected_status
    assert body["path"] is not None and body["path"] != ""


# ===========================================================================
# AUTH ERROR CONTRACT
# ===========================================================================

class TestAuthErrorContract:
    """Validate auth endpoint error responses against the Week-4 contract."""

    def test_login_wrong_password_returns_401(self, integration_client):
        """Register then login with wrong password — must return AUTH-004."""
        integration_client.post(
            "/api/v1/auth/register",
            json={"email": "wrongpass@int.com", "password": "correct123",
                  "full_name": "Test"},
        )
        resp = integration_client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpass@int.com", "password": "wrongpass999"},
        )
        assert_contract(resp, 401, "AUTH-004")

    def test_login_nonexistent_email_returns_401(self, integration_client):
        resp = integration_client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@nowhere.com", "password": "anypass"},
        )
        assert_contract(resp, 401, "AUTH-004")

    def test_register_duplicate_email_returns_409(self, integration_client):
        """Duplicate registration must return USR-001 with 409."""
        payload = {"email": "dupe@int.com", "password": "password123",
                   "full_name": "First"}
        integration_client.post("/api/v1/auth/register", json=payload)
        resp = integration_client.post("/api/v1/auth/register", json=payload)
        assert_contract(resp, 409, "USR-001")

    def test_no_token_on_protected_endpoint_returns_401(self, integration_client):
        resp = integration_client.get("/api/v1/expenses/current-month")
        assert_contract(resp, 401, "AUTH-001")

    def test_invalid_token_returns_401(self, integration_client):
        resp = integration_client.get(
            "/api/v1/expenses/current-month",
            headers={"Authorization": "Bearer garbage.token.value"},
        )
        assert_contract(resp, 401, "AUTH-001")

    def test_register_short_password_returns_400(self, integration_client):
        resp = integration_client.post(
            "/api/v1/auth/register",
            json={"email": "a@b.invalid", "password": "short", "full_name": "X"},
        )
        assert_contract(resp, 400, "VAL-001")

    def test_register_invalid_email_format_returns_400(self, integration_client):
        resp = integration_client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "password123",
                  "full_name": "X"},
        )
        assert_contract(resp, 400, "VAL-001")

    def test_register_empty_body_returns_400(self, integration_client):
        resp = integration_client.post("/api/v1/auth/register", json={})
        assert resp.status_code == 400

    def test_login_empty_body_returns_400(self, integration_client):
        resp = integration_client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 400


# ===========================================================================
# EXPENSE ERROR CONTRACT
# ===========================================================================

class TestExpenseErrorContract:

    @pytest.fixture(autouse=True)
    def setup_token(self, integration_client):
        self.token = register_and_login(
            integration_client, "exp_err@int.com", "password123"
        )
        self.h = auth_headers(self.token)

    def test_missing_amount_returns_400(self, integration_client):
        resp = integration_client.post(
            "/api/v1/expenses",
            json={"category": "Food", "date": "2024-03-10"},
            headers=self.h,
        )
        assert_contract(resp, 400, "VAL-001")

    def test_missing_category_returns_400(self, integration_client):
        resp = integration_client.post(
            "/api/v1/expenses",
            json={"amount": "50.00", "date": "2024-03-10"},
            headers=self.h,
        )
        assert_contract(resp, 400, "VAL-001")

    def test_missing_date_returns_400(self, integration_client):
        resp = integration_client.post(
            "/api/v1/expenses",
            json={"amount": "50.00", "category": "Food"},
            headers=self.h,
        )
        assert_contract(resp, 400, "VAL-001")

    def test_invalid_date_format_returns_400(self, integration_client):
        resp = integration_client.post(
            "/api/v1/expenses",
            json={"amount": "50.00", "category": "Food", "date": "10-03-2024"},
            headers=self.h,
        )
        assert_contract(resp, 400, "VAL-001")

    def test_zero_amount_returns_400(self, integration_client):
        resp = integration_client.post(
            "/api/v1/expenses",
            json={"amount": "0.00", "category": "Food", "date": "2024-03-10"},
            headers=self.h,
        )
        assert resp.status_code == 400

    def test_no_token_returns_401_with_envelope(self, integration_client):
        resp = integration_client.post(
            "/api/v1/expenses",
            json={"amount": "50.00", "category": "Food", "date": "2024-03-10"},
        )
        assert_contract(resp, 401, "AUTH-001")


# ===========================================================================
# BUDGET ERROR CONTRACT
# ===========================================================================

class TestBudgetErrorContract:

    @pytest.fixture(autouse=True)
    def setup_token(self, integration_client):
        self.token = register_and_login(
            integration_client, "bud_err@int.com", "password123"
        )
        self.h = auth_headers(self.token)

    def test_duplicate_budget_returns_409(self, integration_client):
        """DB unique constraint on (user_id, month) — must return BUD-002."""
        payload = {"month": "2024-03", "amount": "5000.00"}
        integration_client.post("/api/v1/budgets", json=payload, headers=self.h)
        resp = integration_client.post("/api/v1/budgets", json=payload, headers=self.h)
        assert_contract(resp, 409, "BUD-002")

    def test_invalid_month_format_returns_400(self, integration_client):
        resp = integration_client.post(
            "/api/v1/budgets",
            json={"month": "March-2024", "amount": "5000.00"},
            headers=self.h,
        )
        assert resp.status_code == 400

    def test_invalid_month_value_returns_400(self, integration_client):
        """Month 13 violates the validator."""
        resp = integration_client.post(
            "/api/v1/budgets",
            json={"month": "2024-13", "amount": "5000.00"},
            headers=self.h,
        )
        assert resp.status_code == 400

    def test_budget_not_found_returns_404(self, integration_client):
        fake_id = "00000000-0000-0000-0000-000000000001"
        resp = integration_client.get(
            f"/api/v1/budgets/{fake_id}", headers=self.h
        )
        assert_contract(resp, 404, "BUD-001")

    def test_wrong_user_budget_returns_403(self, integration_client):
        """User B cannot read User A's budget — must return BUD-004."""
        token_a = register_and_login(
            integration_client, "bud_a@int.com", "password123"
        )
        resp = integration_client.post(
            "/api/v1/budgets",
            json={"month": "2024-06", "amount": "3000.00"},
            headers=auth_headers(token_a),
        )
        budget_id = resp.json()["budgetId"]

        token_b = register_and_login(
            integration_client, "bud_b@int.com", "password123"
        )
        resp = integration_client.get(
            f"/api/v1/budgets/{budget_id}", headers=auth_headers(token_b)
        )
        assert_contract(resp, 403, "BUD-004")

    def test_no_current_month_budget_returns_404(self, integration_client):
        resp = integration_client.get(
            "/api/v1/budgets/current-month", headers=self.h
        )
        assert_contract(resp, 404, "BUD-001")

    def test_invalid_uuid_budget_id_returns_400(self, integration_client):
        resp = integration_client.get(
            "/api/v1/budgets/not-a-uuid", headers=self.h
        )
        assert resp.status_code == 400

    def test_zero_amount_returns_400(self, integration_client):
        resp = integration_client.post(
            "/api/v1/budgets",
            json={"month": "2024-04", "amount": "0"},
            headers=self.h,
        )
        assert resp.status_code == 400

    def test_negative_amount_returns_400(self, integration_client):
        resp = integration_client.post(
            "/api/v1/budgets",
            json={"month": "2024-04", "amount": "-100"},
            headers=self.h,
        )
        assert resp.status_code == 400


# ===========================================================================
# INCOME ERROR CONTRACT
# ===========================================================================

class TestIncomeErrorContract:

    @pytest.fixture(autouse=True)
    def setup_token(self, integration_client):
        self.token = register_and_login(
            integration_client, "inc_err@int.com", "password123"
        )
        self.h = auth_headers(self.token)

    def test_missing_source_returns_400(self, integration_client):
        resp = integration_client.post(
            "/api/v1/incomes",
            json={"amount": "3500.00", "date": "2024-03-15"},
            headers=self.h,
        )
        assert_contract(resp, 400, "VAL-001")

    def test_missing_date_returns_400(self, integration_client):
        resp = integration_client.post(
            "/api/v1/incomes",
            json={"amount": "3500.00", "source": "Salary"},
            headers=self.h,
        )
        assert_contract(resp, 400, "VAL-001")

    def test_zero_amount_returns_400(self, integration_client):
        resp = integration_client.post(
            "/api/v1/incomes",
            json={"amount": "0", "source": "Salary", "date": "2024-03-15"},
            headers=self.h,
        )
        assert resp.status_code == 400

    def test_negative_amount_returns_400(self, integration_client):
        resp = integration_client.post(
            "/api/v1/incomes",
            json={"amount": "-100", "source": "Salary", "date": "2024-03-15"},
            headers=self.h,
        )
        assert resp.status_code == 400


# ===========================================================================
# REPORT ERROR CONTRACT
# ===========================================================================

class TestReportErrorContract:

    @pytest.fixture(autouse=True)
    def setup_token(self, integration_client):
        self.token = register_and_login(
            integration_client, "rep_err@int.com", "password123"
        )
        self.h = auth_headers(self.token)

    def test_missing_month_param_returns_400(self, integration_client):
        resp = integration_client.get("/api/v1/reports/summary", headers=self.h)
        assert resp.status_code == 400

    def test_invalid_month_format_returns_400(self, integration_client):
        resp = integration_client.get(
            "/api/v1/reports/summary?month=March-2024", headers=self.h
        )
        assert resp.status_code == 400

    def test_empty_month_with_no_data_returns_200_zeros(self, integration_client):
        """An empty month is valid — should return zero totals, not an error."""
        resp = integration_client.get(
            "/api/v1/reports/summary?month=2020-01", headers=self.h
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["month"] == "2020-01"
        assert float(body["totalIncome"]) == 0.0
        assert float(body["totalExpenses"]) == 0.0


# ===========================================================================
# ENVELOPE CONSISTENCY — cross-cutting parametrized check
# ===========================================================================

class TestEnvelopeAlwaysComplete:
    """
    Every error response, regardless of which handler fires, must include
    all six Week-4 fields.  Parametrized so adding a case is one line.
    """

    CASES = [
        ("post", "/api/v1/auth/login",
         {"email": "x@x.com", "password": "wrong"}, 401),
        ("post", "/api/v1/auth/register", {}, 400),
        ("get",  "/api/v1/expenses/current-month", None, 401),
        ("get",  "/api/v1/budgets/current-month", None, 401),
        ("get",  "/api/v1/reports/summary", None, 401),
    ]

    @pytest.mark.parametrize("method,url,body,expected_status", CASES)
    def test_envelope_complete(
        self, integration_client, method, url, body, expected_status
    ):
        resp = (
            getattr(integration_client, method)(url, json=body)
            if body is not None
            else getattr(integration_client, method)(url)
        )
        assert resp.status_code == expected_status
        body_json = resp.json()
        missing = ENVELOPE_FIELDS - set(body_json.keys())
        assert not missing, (
            f"{method.upper()} {url} → missing envelope fields: {missing}. "
            f"Body: {body_json}"
        )