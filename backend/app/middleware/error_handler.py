from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.schemas.error_schemas import ErrorResponse, ErrorDetail, ErrorCodes
import logging

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    
    field = ".".join(str(x) for x in first_error.get("loc", [])[1:])
    message = first_error.get("msg", "Validation error")
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCodes.VAL_INVALID_INPUT,
            message=message,
            field=field if field else None
        )
    )
    
    logger.warning(f"Validation error: {message}, field: {field}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump()
    )


async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions from business logic."""
    error_message = str(exc)
    
    # Parse error code and message
    if ":" in error_message:
        code, message = error_message.split(":", 1)
    else:
        code = ErrorCodes.SYS_INTERNAL_ERROR
        message = error_message
    
    # Determine HTTP status code based on error code prefix
    if code.startswith("AUTH-"):
        if code == ErrorCodes.AUTH_INVALID_CREDENTIALS:
            status_code = status.HTTP_401_UNAUTHORIZED
        elif code == ErrorCodes.AUTH_USER_EXISTS:
            status_code = status.HTTP_409_CONFLICT
        else:
            status_code = status.HTTP_401_UNAUTHORIZED
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
        status_code = status.HTTP_400_BAD_REQUEST
    elif code.startswith("EXP-"):
        status_code = status.HTTP_400_BAD_REQUEST
    elif code.startswith("RPT-"):
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message
        )
    )
    
    logger.warning(f"Business logic error: {code} - {message}")
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump()
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors."""
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCodes.SYS_DATABASE_ERROR,
            message="Database constraint violation"
        )
    )
    
    logger.error(f"Database integrity error: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=error_response.model_dump()
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """Handle general SQLAlchemy errors."""
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCodes.SYS_DATABASE_ERROR,
            message="Database error occurred"
        )
    )
    
    logger.error(f"Database error: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    error_response = ErrorResponse(
        error={
            "code": ErrorCodes.SYS_INTERNAL_ERROR,
            "message": "Internal server error"
        }
    )
    
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )
