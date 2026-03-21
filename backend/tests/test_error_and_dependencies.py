import json
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.requests import Request

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


def _make_request(path: str = "/api/v1/test") -> Request:
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
    request = _make_request()

    response = await value_error_handler(request, ValueError(message))

    assert response.status_code == expected_status
    body = json.loads(response.body)
    assert body["errorCode"] == expected_code
    assert body["status"] == expected_status


@pytest.mark.asyncio
async def test_integrity_error_handler_maps_conflict():
    request = _make_request()
    exc = IntegrityError("INSERT ...", {"id": "1"}, Exception("duplicate key"))

    response = await integrity_error_handler(request, exc)

    assert response.status_code == 409
    body = json.loads(response.body)
    assert body["errorCode"] == ErrorCodes.SYS_DATABASE_ERROR
    assert body["error"] == "Conflict"


@pytest.mark.asyncio
async def test_sqlalchemy_error_handler_maps_internal_error():
    request = _make_request()
    response = await sqlalchemy_error_handler(request, SQLAlchemyError("db offline"))

    assert response.status_code == 500
    body = json.loads(response.body)
    assert body["errorCode"] == ErrorCodes.SYS_DATABASE_ERROR
    assert body["error"] == "Internal Server Error"


@pytest.mark.asyncio
async def test_general_exception_handler_maps_internal_error():
    request = _make_request("/api/v1/expenses")
    response = await general_exception_handler(request, RuntimeError("boom"))

    assert response.status_code == 500
    body = json.loads(response.body)
    assert body["errorCode"] == ErrorCodes.SYS_INTERNAL_ERROR
    assert body["message"] == "Internal server error"
    assert body["path"] == "/api/v1/expenses"


@pytest.mark.asyncio
async def test_http_exception_handler_maps_401_and_403():
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


def test_get_current_user_invalid_token(monkeypatch):
    monkeypatch.setattr(dependencies, "decode_access_token", lambda _: None)
    auth_service = type("AuthServiceStub", (), {"get_user_by_id": lambda *_: None})()

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_current_user(token="not-a-token", auth_service=auth_service)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing or invalid token"


def test_get_current_user_invalid_uuid_payload(monkeypatch):
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
    def __init__(self, id, email):
        self.id = id
        self.email = email