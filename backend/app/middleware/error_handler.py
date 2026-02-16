from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timezone
from app.schemas.error_schemas import ErrorCodes
import logging

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    # Week 4 wants an ISO-8601 UTC timestamp (commonly shown with Z)
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
    return "Internal Server Error"


def _week4_payload(
    request: Request,
    status_code: int,
    error_code: str,
    message: str,
    details: list[dict] | None = None,
) -> dict:
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
    if ":" in error_message:
        code, message = error_message.split(":", 1)
        return code.strip(), message.strip()
    return ErrorCodes.SYS_INTERNAL_ERROR, error_message


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors in Week 4 error shape."""
    details = []
    for e in exc.errors():
        loc = e.get("loc", [])
        # loc often looks like ("body", "month") / ("query","month") / ("path","budgetId")
        field = ".".join(str(x) for x in loc if x not in ("body", "query", "path")) or None
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
    """Handle ValueError exceptions from business logic (Week 4 error shape)."""
    code, message = _split_code_and_message(str(exc))

    # Determine HTTP status code based on error code prefix
    if code.startswith("AUTH-"):
        if code == ErrorCodes.AUTH_INVALID_CREDENTIALS:
            status_code = status.HTTP_401_UNAUTHORIZED
        elif code == getattr(ErrorCodes, "AUTH_UNAUTHORIZED", None) or code == getattr(ErrorCodes, "AUTH_FORBIDDEN", None):
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_401_UNAUTHORIZED

    # Determine HTTP status code based on error code prefix
    elif code.startswith("USR-"):
        if code == ErrorCodes.USER_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif code == ErrorCodes.USER_EXISTS:
            status_code = status.HTTP_409_CONFLICT
        else:
            status_code = status.HTTP_400_BAD_REQUEST

    elif code.startswith("VAL-"):
        status_code = status.HTTP_400_BAD_REQUEST

    elif code.startswith("BUD-"):
        if code == ErrorCodes.BUD_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif code == ErrorCodes.BUD_ALREADY_EXISTS:
            status_code = status.HTTP_409_CONFLICT
        elif code == ErrorCodes.BUD_UNAUTHORIZED:
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_400_BAD_REQUEST

    elif code.startswith("INC-"):
        # Minimal improvement (keeps logic style, aligns with Week 4 expectations)
        if code == ErrorCodes.INC_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif code == ErrorCodes.INC_UNAUTHORIZED:
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_400_BAD_REQUEST

    elif code.startswith("EXP-"):
        if code == ErrorCodes.EXP_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif code == ErrorCodes.EXP_UNAUTHORIZED:
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_400_BAD_REQUEST

    elif code.startswith("RPT-"):
        status_code = status.HTTP_400_BAD_REQUEST

    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        code = ErrorCodes.SYS_INTERNAL_ERROR

    payload = _week4_payload(
        request=request,
        status_code=status_code,
        error_code=code,
        message=message,
    )

    logger.warning(f"Business logic error: {code} - {message}")
    return JSONResponse(status_code=status_code, content=payload)


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors (Week 4 error shape)."""
    payload = _week4_payload(
        request=request,
        status_code=status.HTTP_409_CONFLICT,
        error_code=ErrorCodes.SYS_DATABASE_ERROR,
        message="Database constraint violation",
    )
    logger.error(f"Database integrity error: {str(exc)}")
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=payload)


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """Handle general SQLAlchemy errors (Week 4 error shape)."""
    payload = _week4_payload(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code=ErrorCodes.SYS_DATABASE_ERROR,
        message="Database error occurred",
    )
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions (Week 4 error shape)."""
    payload = _week4_payload(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code=ErrorCodes.SYS_INTERNAL_ERROR,
        message="Internal server error",
    )
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Convert FastAPI HTTPException (e.g., OAuth2 'Not authenticated')
    into Week 4 error response shape.
    """
    status_code = exc.status_code

    # Normalize 401s coming from auth to AUTH-001 by default
    if status_code == status.HTTP_401_UNAUTHORIZED:
        error_code = ErrorCodes.AUTH_INVALID_TOKEN  # AUTH-001 after your remap
        message = "Missing or invalid token"
    elif status_code == status.HTTP_403_FORBIDDEN:
        error_code = getattr(ErrorCodes, "AUTH_UNAUTHORIZED", ErrorCodes.AUTH_INVALID_TOKEN)
        message = str(exc.detail)
    else:
        error_code = ErrorCodes.SYS_INTERNAL_ERROR
        message = str(exc.detail)

    payload = _week4_payload(
        request=request,
        status_code=status_code,
        error_code=error_code,
        message=message,
    )
    return JSONResponse(status_code=status_code, content=payload)
