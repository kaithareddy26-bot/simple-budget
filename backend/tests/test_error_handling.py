"""
Auth failure, error handling consistency, and failure scenario tests.

Sprint 1 gap closure:
  - Every protected endpoint must return 401 with correct error shape
    when token is missing or invalid.
  - The error envelope must be consistent across all failure types.
  - Simulated DB errors and edge-case inputs must be handled gracefully.

Commit: test: add auth failure, error-handling consistency, and failure scenario tests
"""

import pytest
from unittest.mock import patch, Mock
from uuid import uuid4

from app.main import app
from app.dependencies import get_current_user
from app.schemas.error_schemas import ErrorCodes
from tests.conftest import (
    make_user,
    make_expense,
    make_budget,
    make_income,
    FIXED_USER_ID,
    FIXED_BUDGET_ID,
    assert_error_shape,
    assert_unauthorized,
)


# ===========================================================================
# AUTH FAILURE TESTS — no token / bad token on all protected routes
# ===========================================================================


class TestAuthFailures:
    """
    Every endpoint protected by get_current_user must return 401
    with the Week-4 error envelope when the token is absent or invalid.
    """

    PROTECTED_ENDPOINTS = [
        ("GET", "/api/v1/expenses/current-month"),
        ("POST", "/api/v1/expenses"),
        ("GET", "/api/v1/budgets/current-month"),
        ("POST", "/api/v1/budgets"),
        ("GET", f"/api/v1/budgets/{FIXED_BUDGET_ID}"),
        ("PUT", f"/api/v1/budgets/{FIXED_BUDGET_ID}"),
        ("POST", "/api/v1/incomes"),
        ("GET", "/api/v1/reports/summary?month=2024-03"),
    ]

    @pytest.mark.parametrize("method,url", PROTECTED_ENDPOINTS)
    def test_no_token_returns_401(self, unauth_client, method, url):
        """Request without Authorization header must get 401."""
        client = unauth_client["client"]
        # Restore real get_current_user so JWT validation fires
        app.dependency_overrides.pop(get_current_user, None)

        resp = getattr(client, method.lower())(url)

        assert resp.status_code == 401, (
            f"{method} {url} returned {resp.status_code}, expected 401"
        )
        body = resp.json()
        assert_error_shape(body, 401, ErrorCodes.AUTH_INVALID_TOKEN)

    @pytest.mark.parametrize("method,url", PROTECTED_ENDPOINTS)
    def test_invalid_token_returns_401(self, unauth_client, method, url):
        """Request with a garbage Bearer token must get 401."""
        client = unauth_client["client"]
        app.dependency_overrides.pop(get_current_user, None)

        with patch("app.dependencies.decode_access_token", return_value=None):
            resp = getattr(client, method.lower())(
                url, headers={"Authorization": "Bearer garbage.token.value"}
            )

        assert resp.status_code == 401
        body = resp.json()
        assert_error_shape(body, 401, ErrorCodes.AUTH_INVALID_TOKEN)

    @pytest.mark.parametrize("method,url", PROTECTED_ENDPOINTS)
    def test_expired_token_returns_401(self, unauth_client, method, url):
        """Expired token (decode returns None) must get 401."""
        client = unauth_client["client"]
        app.dependency_overrides.pop(get_current_user, None)

        with patch("app.dependencies.decode_access_token", return_value=None):
            resp = getattr(client, method.lower())(
                url,
                headers={"Authorization": "Bearer expired.token.xxx"},
            )

        assert resp.status_code == 401
        assert_error_shape(resp.json(), 401, ErrorCodes.AUTH_INVALID_TOKEN)

    def test_token_with_malformed_sub_returns_401(self, unauth_client):
        """Token payload where 'sub' is not a valid UUID string must get 401.
        UUID('not-a-uuid') raises ValueError → caught → 401."""
        client = unauth_client["client"]
        app.dependency_overrides.pop(get_current_user, None)

        with patch(
            "app.dependencies.decode_access_token",
            return_value={"sub": "not-a-valid-uuid", "email": "x@example.com"},
        ):
            resp = client.get(
                "/api/v1/expenses/current-month",
                headers={"Authorization": "Bearer token.bad.sub"},
            )

        assert resp.status_code == 401

    def test_token_user_not_in_db_returns_401(self, unauth_client):
        """Valid JWT format but user no longer exists in DB must get 401."""
        client = unauth_client["client"]
        app.dependency_overrides.pop(get_current_user, None)
        svc = unauth_client["auth_service"]
        svc.get_user_by_id.return_value = None

        with patch(
            "app.dependencies.decode_access_token",
            return_value={"sub": str(FIXED_USER_ID), "email": "ghost@example.com"},
        ):
            resp = client.get(
                "/api/v1/expenses/current-month",
                headers={"Authorization": "Bearer valid.structure.token"},
            )

        assert resp.status_code == 401


# ===========================================================================
# ERROR ENVELOPE CONSISTENCY TESTS
# ===========================================================================


class TestErrorEnvelopeConsistency:
    """
    All error responses must share the same Week-4 envelope:
      { timestamp, status, error, errorCode, message, path }
    Regardless of which handler fires (validation, ValueError, HTTPException, etc.)
    """

    REQUIRED_FIELDS = {"timestamp", "status", "error", "errorCode", "message", "path"}

    def test_validation_error_has_full_envelope(self, unauth_client):
        """Pydantic validation error → validation_exception_handler."""
        client = unauth_client["client"]
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "short"},
        )
        assert resp.status_code == 400
        body = resp.json()
        missing = self.REQUIRED_FIELDS - set(body.keys())
        assert not missing, f"Missing fields in validation error envelope: {missing}"

    def test_404_not_found_has_full_envelope(self, auth_client):
        """BUD_NOT_FOUND ValueError → value_error_handler."""
        client = auth_client["client"]
        svc = auth_client["budget_service"]
        svc.get_budget_by_id.side_effect = ValueError(
            f"{ErrorCodes.BUD_NOT_FOUND}: not found"
        )
        resp = client.get(f"/api/v1/budgets/{FIXED_BUDGET_ID}")
        assert resp.status_code == 404
        body = resp.json()
        missing = self.REQUIRED_FIELDS - set(body.keys())
        assert not missing, f"Missing fields in 404 envelope: {missing}"

    def test_401_error_has_full_envelope(self, unauth_client):
        """Missing token → http_exception_handler."""
        client = unauth_client["client"]
        app.dependency_overrides.pop(get_current_user, None)
        resp = client.get("/api/v1/expenses/current-month")
        body = resp.json()
        missing = self.REQUIRED_FIELDS - set(body.keys())
        assert not missing, f"Missing fields in 401 envelope: {missing}"

    def test_409_conflict_has_full_envelope(self, auth_client):
        """BUD_ALREADY_EXISTS → value_error_handler."""
        client = auth_client["client"]
        svc = auth_client["budget_service"]
        svc.create_budget.side_effect = ValueError(
            f"{ErrorCodes.BUD_ALREADY_EXISTS}: already exists"
        )
        resp = client.post("/api/v1/budgets", json={"month": "2024-03", "amount": "500"})
        assert resp.status_code == 409
        body = resp.json()
        missing = self.REQUIRED_FIELDS - set(body.keys())
        assert not missing, f"Missing fields in 409 envelope: {missing}"

    def test_validation_error_includes_details_array(self, unauth_client):
        """Validation errors should include a 'details' list."""
        client = unauth_client["client"]
        resp = client.post("/api/v1/auth/register", json={})
        assert resp.status_code == 400
        body = resp.json()
        assert "details" in body, "Validation error must include 'details' array"
        assert isinstance(body["details"], list)
        assert len(body["details"]) > 0

    def test_error_path_matches_request_url(self, unauth_client):
        """The 'path' field in error must reflect the actual request path."""
        client = unauth_client["client"]
        app.dependency_overrides.pop(get_current_user, None)
        resp = client.get("/api/v1/expenses/current-month")
        body = resp.json()
        assert body["path"] == "/api/v1/expenses/current-month"

    def test_error_status_field_matches_http_status(self, unauth_client):
        """The 'status' field in the JSON body must match the HTTP status code."""
        client = unauth_client["client"]
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 400
        assert resp.json()["status"] == 400


# ===========================================================================
# FAILURE SCENARIOS — DB errors, malformed data, edge cases
# ===========================================================================


class TestFailureScenarios:
    """
    High-value failure paths: simulated DB exceptions, malformed inputs,
    boundary conditions on financial fields.
    """

    # --- DB / integrity errors ---

    def test_db_integrity_error_returns_409(self, auth_client):
        """IntegrityError from DB layer → 409 with SYS-002."""
        from sqlalchemy.exc import IntegrityError

        client = auth_client["client"]
        svc = auth_client["expense_service"]
        svc.add_expense.side_effect = IntegrityError(
            "statement", "params", Exception("unique constraint")
        )

        resp = client.post(
            "/api/v1/expenses",
            json={"amount": "100.00", "category": "Food", "date": "2024-03-10"},
        )

        assert resp.status_code == 409
        assert_error_shape(resp.json(), 409, ErrorCodes.SYS_DATABASE_ERROR)

    def test_db_sqlalchemy_error_returns_500(self, auth_client):
        """General SQLAlchemyError → 500 with SYS-002."""
        from sqlalchemy.exc import SQLAlchemyError

        client = auth_client["client"]
        svc = auth_client["expense_service"]
        svc.add_expense.side_effect = SQLAlchemyError("connection lost")

        resp = client.post(
            "/api/v1/expenses",
            json={"amount": "100.00", "category": "Food", "date": "2024-03-10"},
        )

        assert resp.status_code == 500
        assert_error_shape(resp.json(), 500, ErrorCodes.SYS_DATABASE_ERROR)

    def test_unhandled_exception_returns_500(self, auth_client):
        """Unexpected RuntimeError → 500 with SYS-001."""
        client = auth_client["client"]
        svc = auth_client["expense_service"]
        svc.add_expense.side_effect = RuntimeError("unexpected crash")

        resp = client.post(
            "/api/v1/expenses",
            json={"amount": "100.00", "category": "Food", "date": "2024-03-10"},
        )

        assert resp.status_code == 500
        assert_error_shape(resp.json(), 500, ErrorCodes.SYS_INTERNAL_ERROR)

    # --- Malformed / boundary inputs ---

    def test_expense_string_amount_returns_400(self, auth_client):
        """Non-numeric amount string must be rejected."""
        client = auth_client["client"]
        resp = client.post(
            "/api/v1/expenses",
            json={"amount": "abc", "category": "Food", "date": "2024-03-10"},
        )
        assert resp.status_code == 400

    def test_expense_extremely_large_amount(self, auth_client):
        """Very large decimal amounts should be accepted by the schema."""
        client = auth_client["client"]
        svc = auth_client["expense_service"]
        svc.add_expense.return_value = make_expense(amount=__import__("decimal").Decimal("999999999.99"))

        resp = client.post(
            "/api/v1/expenses",
            json={"amount": "999999999.99", "category": "Food", "date": "2024-03-10"},
        )

        assert resp.status_code == 201

    def test_budget_string_amount_returns_400(self, auth_client):
        client = auth_client["client"]
        resp = client.post(
            "/api/v1/budgets",
            json={"month": "2024-03", "amount": "lots"},
        )
        assert resp.status_code == 400

    def test_income_invalid_date_format_returns_400(self, auth_client):
        client = auth_client["client"]
        resp = client.post(
            "/api/v1/incomes",
            json={"amount": "3500.00", "source": "Salary", "date": "15-03-2024"},
        )
        assert resp.status_code == 400

    def test_report_month_with_day_component_returns_400(self, auth_client):
        """'2024-03-01' has too many components — regex should reject it."""
        client = auth_client["client"]
        resp = client.get("/api/v1/reports/summary?month=2024-03-01")
        assert resp.status_code == 400

    def test_budget_id_wrong_type_returns_400(self, auth_client):
        """Path param that is not a UUID must be rejected."""
        client = auth_client["client"]
        resp = client.get("/api/v1/budgets/12345")
        assert resp.status_code == 400

    # --- Access-control edge cases ---

    def test_expense_unauthorized_access_returns_403(self, auth_client):
        """EXP_UNAUTHORIZED service error → 403."""
        client = auth_client["client"]
        svc = auth_client["expense_service"]
        svc.add_expense.side_effect = ValueError(
            f"{ErrorCodes.EXP_UNAUTHORIZED}: Not your expense"
        )

        resp = client.post(
            "/api/v1/expenses",
            json={"amount": "100.00", "category": "Food", "date": "2024-03-10"},
        )

        assert resp.status_code == 403
        assert_error_shape(resp.json(), 403, ErrorCodes.EXP_UNAUTHORIZED)

    def test_income_unauthorized_access_returns_403(self, auth_client):
        """INC_UNAUTHORIZED service error → 403."""
        client = auth_client["client"]
        svc = auth_client["income_service"]
        svc.add_income.side_effect = ValueError(
            f"{ErrorCodes.INC_UNAUTHORIZED}: Not your income"
        )

        resp = client.post(
            "/api/v1/incomes",
            json={"amount": "3500.00", "source": "Salary", "date": "2024-03-15"},
        )

        assert resp.status_code == 403

    def test_budget_unauthorized_access_returns_403(self, auth_client):
        """BUD_UNAUTHORIZED when another user owns the budget → 403."""
        client = auth_client["client"]
        svc = auth_client["budget_service"]
        svc.update_budget_amount.side_effect = ValueError(
            f"{ErrorCodes.BUD_UNAUTHORIZED}: Forbidden"
        )

        resp = client.put(
            f"/api/v1/budgets/{FIXED_BUDGET_ID}", json={"amount": "9999.00"}
        )

        assert resp.status_code == 403

    # --- Health / public endpoints (no auth required) ---

    def test_health_endpoint_accessible_without_auth(self, unauth_client):
        """Health check must always return 200 — no token required."""
        client = unauth_client["client"]
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_root_endpoint_accessible_without_auth(self, unauth_client):
        client = unauth_client["client"]
        resp = client.get("/")
        assert resp.status_code == 200