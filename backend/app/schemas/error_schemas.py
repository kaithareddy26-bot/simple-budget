from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any


class ErrorDetail(BaseModel):
    """Standard error detail schema."""
    
    code: str
    message: str
    field: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "VAL-001",
                "message": "Invalid input data",
                "field": "email"
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    
    error: Dict[str, Any]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "VAL-001",
                    "message": "Invalid input data",
                    "field": "email"
                }
            }
        }
    )


# Standard error codes by category
class ErrorCodes:
    """Standard error codes."""
    
    # Authentication errors (AUTH-xxx)
    AUTH_INVALID_CREDENTIALS = "AUTH-001"
    AUTH_USER_EXISTS = "AUTH-002"
    AUTH_INVALID_TOKEN = "AUTH-003"
    AUTH_TOKEN_EXPIRED = "AUTH-004"
    AUTH_UNAUTHORIZED = "AUTH-005"
    
    # Validation errors (VAL-xxx)
    VAL_INVALID_INPUT = "VAL-001"
    VAL_REQUIRED_FIELD = "VAL-002"
    VAL_INVALID_FORMAT = "VAL-003"
    VAL_INVALID_RANGE = "VAL-004"
    
    # Budget errors (BUD-xxx)
    BUD_NOT_FOUND = "BUD-001"
    BUD_ALREADY_EXISTS = "BUD-002"
    BUD_INVALID_AMOUNT = "BUD-003"
    BUD_UNAUTHORIZED = "BUD-004"
    
    # Income errors (INC-xxx)
    INC_NOT_FOUND = "INC-001"
    INC_INVALID_AMOUNT = "INC-002"
    INC_UNAUTHORIZED = "INC-003"
    
    # Expense errors (EXP-xxx)
    EXP_NOT_FOUND = "EXP-001"
    EXP_INVALID_AMOUNT = "EXP-002"
    EXP_UNAUTHORIZED = "EXP-003"
    
    # Report errors (RPT-xxx)
    RPT_INVALID_MONTH = "RPT-001"
    RPT_NO_DATA = "RPT-002"
    
    # System errors (SYS-xxx)
    SYS_INTERNAL_ERROR = "SYS-001"
    SYS_DATABASE_ERROR = "SYS-002"