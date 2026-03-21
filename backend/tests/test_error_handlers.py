"""
Error handling and dependency path tests.

Consolidated test suite covering:
  - Middleware error handlers (validation, ValueError, IntegrityError, SQLAlchemy, general, HTTP)
  - Authentication failures (missing/invalid tokens on protected endpoints)
  - Error envelope consistency (Week-4 specification shape on all errors)
  - Failure scenarios (DB errors, malformed data, edge cases)
  - Token dependency validation (get_current_user error paths)

Tests validate the error handling chain from exception through HTTP response,
and auth dependency token validation paths.

Merged from: test_error_handling.py + error/dependency tests from test_error_and_dependencies.py
"""

import json
import pytest
from unittest.mock import patch, Mock
from uuid import uuid4
from datetime import date as date_type

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.requests import Request

from app.main import app
from app.dependencies import get_current_user
import app.dependencies as dependencies
from app.schemas.error_schemas import ErrorCodes
from app.middleware.error_handler import (
    general_exception_handler,
    http_exception_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
    validation_exception_handler,
    value_error_handler,
)
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
# MIDDLEWARE ERROR HANDLER TESTS
# ===========================================================================


def _make_request(path: str = "/api/v1/test") -> Request:
    """Helper to create a mock Request object for error handler testing."""
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_validation_exception_handler_returns_week4_shape():
    """Pydantic validation error returns proper Week-4 envelope."""
    request = _make_request("/api/v1/reports/summary")
    exc = RequestValidationError(
        [
            {
                "loc": ("query", "month"),
                "msg": "String should match pattern",
                "type": "string_pattern_mismatch",
            },
            {
                "loc": ("body", "amount"),
                "msg": "Input should be greater than 0",
                "type": "greater_than",
            },
        ]
    )

    response = await validation_exception_handler(request, exc)

    assert response.status_code == 400
    body = json.loads(response.body)
    assert body["errorCode"] == ErrorCodes.VAL_INVALID_INPUT
    assert body["path"] == "/api/v1/reports/summary"
    assert body["status"] == 400
    assert len(body["details"]) == 2


@pytest.mark.parametrize(
    "message,expected_status,expected_code",
    [
        ("AUTH-004:Invalid credentials", 401, "AUTH-004"),
        ("USR-002:User not found", 404, "USR-002"),
        ("BUD-004:Not your budget", 403, "BUD-004"),
        ("INC-004:Invalid source", 400, "INC-004"),
        ("EXP-001:Expense not found", 404, "EXP-001"),
        ("RPT-001:Invalid month", 400, "RPT-001"),
        (
            "Unrecognized domain failure",
            500,
            ErrorCodes.SYS_INTERNAL_ERROR,
        ),
    ],
)
@pytest.mark.asyncio
async def test_value_error_handler_maps_status_codes(
    message, expected_status, expected_code
):
    """ValueError with error code prefix maps to correct HTTP status."""
    request = _make_request()

    response = await value_error_handler(request, ValueError(message))

    assert response.status_code == expected_status
    body = json.loads(response.body)
    assert body["errorCode"] == expected_code
    assert body["status"] == expected_status


@pytest.mark.asyncio
async def test_integrity_error_handler_maps_conflict():
    """DB IntegrityError maps to 409 Conflict."""
    request = _make_request()
    exc = IntegrityError("INSERT ...", {"id": "1"}, Exception("duplicate key"))

    response = await integrity_error_handler(request, exc)

    assert response.status_code == 409
    body = json.loads(response.body)
    assert body["errorCode"] == ErrorCodes.SYS_DATABASE_ERROR
    assert body["error"] == "Conflict"


@pytest.mark.asyncio
async def test_sqlalchemy_error_handler_maps_internal_error():
    """SQLAlchemy error maps to 500."""
    request = _make_request()
    response = await sqlalchemy_error_handler(request, SQLAlchemyError("db offline"))

    assert response.status_code == 500
    body = json.loads(response.body)
    assert body["errorCode"] == ErrorCodes.SYS_DATABASE_ERROR
    assert body["error"] == "Internal Server Error"


@pytest.mark.asyncio
async def test_general_exception_handler_maps_internal_error():
    """Unhandled exception maps to 500."""
    request = _make_request("/api/v1/expenses")
    response = await general_exception_handler(request, RuntimeError("boom"))

    assert response.status_code == 500
    body = json.loads(response.body)
    assert body["errorCode"] == ErrorCodes.SYS_INTERNAL_ERROR
    assert body["message"] == "Internal server error"
    assert body["path"] == "/api/v1/expenses"


@pytest.mark.asyncio
async def test_http_exception_handler_maps_401_and_403():
    """HTTPException 401/403 map to proper error codes."""
    request = _make_request("/api/v1/budgets")

    response_401 = await http_exception_handler(
        request,
        HTTPException(status_code=401, detail="Not authenticated"),
    )
    body_401 = json.loads(response_401.body)
    assert response_401.status_code == 401
    assert body_401["errorCode"] == ErrorCodes.AUTH_INVALID_TOKEN
    assert body_401["message"] == "Missing or invalid token"

    response_403 = await http_exception_handler(
        request,
        HTTPException(status_code=403, detail="Forbidden"),
    )
    body_403 = json.loads(response_403.body)
    assert response_403.status_code == 403
    assert body_403["errorCode"] == ErrorCodes.AUTH_UNAUTHORIZED
    assert body_403["message"] == "Forbidden"


# ===========================================================================
# DEPENDENCY: get_current_user TOKEN VALIDATION TESTS
# ===========================================================================


def test_get_current_user_invalid_token(monkeypatch):
    """Invalid/expired token raises 401 AUTH-001."""
    monkeypatch.setattr(dependencies, "decode_access_token", lambda _: None)
    auth_service = type("AuthServiceStub", (), {"get_user_by_id": lambda *_: None})()

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_current_user(token="not-a-token", auth_service=auth_service)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing or invalid token"


def test_get_current_user_invalid_uuid_payload(monkeypatch):
    """Token payload with malformed UUID in 'sub' raises 401."""
    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _: {"sub": "not-a-uuid", "email": "tester@example.com"},
    )
    auth_service = type("AuthServiceStub", (), {"get_user_by_id": lambda *_: None})()

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_current_user(token="valid-looking", auth_service=auth_service)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token format"


def test_get_current_user_missing_payload_fields(monkeypatch):
    """Token missing 'email' field raises 401."""
    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _: {"sub": str(uuid4())},
    )
    auth_service = type("AuthServiceStub", (), {"get_user_by_id": lambda *_: None})()

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_current_user(token="valid-looking", auth_service=auth_service)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token payload"


def test_get_current_user_user_not_found(monkeypatch):
    """Valid token but user not in DB raises 401."""
    user_id = uuid4()
    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _: {"sub": str(user_id), "email": "tester@example.com"},
    )
    auth_service = type("AuthServiceStub", (), {"get_user_by_id": lambda *_: None})()

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_current_user(token="valid-looking", auth_service=auth_service)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User not found"


def test_get_current_user_success(monkeypatch):
    """Valid token and user in DB returns TokenData."""
    user_id = uuid4()
    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _: {"sub": str(user_id), "email": "tester@example.com"},
    )
    user = SimpleUser(id=user_id, email="tester@example.com")
    auth_service = type("AuthServiceStub", (), {"get_user_by_id": lambda *_: user})()

    token_data = dependencies.get_current_user(
        token="valid-looking", auth_service=auth_service
    )

    assert token_data.user_id == user_id
    assert token_data.email == "tester@example.com"


class SimpleUser:
    """Stub user object for dependency testing."""
    def __init__(self, id, email):
        self.id = id
        self.email = email


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
