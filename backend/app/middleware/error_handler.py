from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timezone
from slowapi.errors import RateLimitExceeded
from app.schemas.error_schemas import ErrorCodes
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Status-code lookup table — maps domain error codes to HTTP status codes.
# Replaces the previous verbose if/elif chain in value_error_handler.
# Prefix keys (e.g. "AUTH-") act as fallbacks when no exact code matches.
# ---------------------------------------------------------------------------
_CODE_TO_STATUS: dict[str, int] = {
    # Auth
    ErrorCodes.AUTH_INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
    ErrorCodes.AUTH_INVALID_TOKEN:        status.HTTP_401_UNAUTHORIZED,
    # User
    ErrorCodes.USER_NOT_FOUND:  status.HTTP_404_NOT_FOUND,
    ErrorCodes.USER_EXISTS:     status.HTTP_409_CONFLICT,
    # Budget
    ErrorCodes.BUD_NOT_FOUND:      status.HTTP_404_NOT_FOUND,
    ErrorCodes.BUD_ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    ErrorCodes.BUD_UNAUTHORIZED:   status.HTTP_403_FORBIDDEN,
    # Income
    ErrorCodes.INC_NOT_FOUND:    status.HTTP_404_NOT_FOUND,
    ErrorCodes.INC_UNAUTHORIZED: status.HTTP_403_FORBIDDEN,
    # Expense
    ErrorCodes.EXP_NOT_FOUND:    status.HTTP_404_NOT_FOUND,
    ErrorCodes.EXP_UNAUTHORIZED: status.HTTP_403_FORBIDDEN,
}

# Prefix fallbacks — used when the exact code is not in _CODE_TO_STATUS
_PREFIX_TO_STATUS: dict[str, int] = {
    "AUTH-": status.HTTP_401_UNAUTHORIZED,
    "USR-":  status.HTTP_400_BAD_REQUEST,
    "VAL-":  status.HTTP_400_BAD_REQUEST,
    "BUD-":  status.HTTP_400_BAD_REQUEST,
    "INC-":  status.HTTP_400_BAD_REQUEST,
    "EXP-":  status.HTTP_400_BAD_REQUEST,
    "RPT-":  status.HTTP_400_BAD_REQUEST,
}


def _resolve_status(code: str) -> int:
    """Return the HTTP status code for a domain error code.

    Checks the exact-match table first, then falls back to prefix matching,
    then defaults to 500 Internal Server Error.
    """
    if code in _CODE_TO_STATUS:
        return _CODE_TO_STATUS[code]
    for prefix, http_status in _PREFIX_TO_STATUS.items():
        if code.startswith(prefix):
            return http_status
    return status.HTTP_500_INTERNAL_SERVER_ERROR


def _utc_now_iso() -> str:
    """Return current UTC time as an ISO-8601 string with Z suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _http_reason(status_code: int) -> str:
    if status_code == 400:
        return "Bad Request"
    if status_code == 401:
        return "Unauthorized"
    if status_code == 403:
        return "Forbidden"
    if status_code == 404:
        return "Not Found"
    if status_code == 409:
        return "Conflict"
    if status_code == 429:
        return "Too Many Requests"
    return "Internal Server Error"


def _week4_payload(
    request: Request,
    status_code: int,
    error_code: str,
    message: str,
    details: list[dict] | None = None,
) -> dict:
    """Build the standard Week-4 error envelope."""
    payload = {
        "timestamp": _utc_now_iso(),
        "status": status_code,
        "error": _http_reason(status_code),
        "errorCode": error_code,
        "message": message,
        "path": str(request.url.path),
    }
    if details:
        payload["details"] = details
    return payload


def _split_code_and_message(error_message: str) -> tuple[str, str]:
    """Split a "CODE:message" string raised by services into its two parts.

    If no colon separator is present the entire string is treated as a
    message and SYS_INTERNAL_ERROR is used as the code.
    """
    if ":" in error_message:
        code, message = error_message.split(":", 1)
        return code.strip(), message.strip()
    return ErrorCodes.SYS_INTERNAL_ERROR, error_message


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic/FastAPI validation errors using the standard error envelope."""
    details = []
    for e in exc.errors():
        loc = e.get("loc", [])
        field = (
            ".".join(str(x) for x in loc if x not in ("body", "query", "path")) or None
        )
        details.append({"field": field, "issue": e.get("msg", "Invalid value")})

    payload = _week4_payload(
        request=request,
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code=ErrorCodes.VAL_INVALID_INPUT,
        message="Invalid input data",
        details=details or None,
    )
    logger.warning(f"Validation error on {request.url.path}: {details}")
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=payload)


async def value_error_handler(request: Request, exc: ValueError):
    """Map service-layer ValueErrors to HTTP responses using the error code lookup table."""
    code, message = _split_code_and_message(str(exc))
    http_status = _resolve_status(code)

    # Codes that fall through to 500 are unrecognised domain errors; normalise them.
    if http_status == status.HTTP_500_INTERNAL_SERVER_ERROR:
        code = ErrorCodes.SYS_INTERNAL_ERROR

    payload = _week4_payload(
        request=request,
        status_code=http_status,
        error_code=code,
        message=message,
    )
    logger.warning(f"Business logic error: {code} - {message}")
    return JSONResponse(status_code=http_status, content=payload)


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors using the standard error envelope."""
    payload = _week4_payload(
        request=request,
        status_code=status.HTTP_409_CONFLICT,
        error_code=ErrorCodes.SYS_DATABASE_ERROR,
        message="Database constraint violation",
    )
    logger.error(f"Database integrity error: {str(exc)}")
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=payload)


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """Handle general SQLAlchemy errors using the standard error envelope."""
    payload = _week4_payload(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code=ErrorCodes.SYS_DATABASE_ERROR,
        message="Database error occurred",
    )
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected exceptions."""
    payload = _week4_payload(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code=ErrorCodes.SYS_INTERNAL_ERROR,
        message="Internal server error",
    )
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Convert FastAPI HTTPExceptions into the standard Week-4 error envelope.

    Normalises OAuth2 401s ('Not authenticated') and 403s into the
    project's AUTH error code scheme.
    """
    http_status = exc.status_code

    if http_status == status.HTTP_401_UNAUTHORIZED:
        error_code = ErrorCodes.AUTH_INVALID_TOKEN
        message = "Missing or invalid token"
    elif http_status == status.HTTP_403_FORBIDDEN:
        error_code = getattr(ErrorCodes, "AUTH_UNAUTHORIZED", ErrorCodes.AUTH_INVALID_TOKEN)
        message = str(exc.detail)
    else:
        error_code = ErrorCodes.SYS_INTERNAL_ERROR
        message = str(exc.detail)

    payload = _week4_payload(
        request=request,
        status_code=http_status,
        error_code=error_code,
        message=message,
    )
    return JSONResponse(status_code=status_code, content=payload)


async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """Handle SlowAPI 429 responses using the standard error envelope."""
    message = str(getattr(exc, "detail", "Rate limit exceeded"))
    payload = _week4_payload(
        request=request,
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        error_code=ErrorCodes.SYS_RATE_LIMIT,
        message=message,
    )
    return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=payload)
