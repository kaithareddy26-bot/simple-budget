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
    
    # Authentication errors (AUTH-xxx) — aligned with Week 4 document
    AUTH_INVALID_TOKEN = "AUTH-001"        # Missing or invalid token
    AUTH_TOKEN_EXPIRED = "AUTH-002"        # Token expired
    AUTH_UNAUTHORIZED = "AUTH-003"         # Insufficient permissions (403)
    AUTH_INVALID_CREDENTIALS = "AUTH-004"  # Invalid login credentials
    
    # User errors (USR-xxx) — aligned with Week 4 document
    USER_EXISTS = "USR-001"           # User with given email already exists    
    USER_NOT_FOUND = "USR-002"        # User with given email not found

    
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
    BUD_INVALID_MONTH = "BUD-005"  # Added: strict YYYY-MM validation support
    
    # Income errors (INC-xxx)
    INC_NOT_FOUND = "INC-001"
    INC_INVALID_AMOUNT = "INC-002"
    INC_UNAUTHORIZED = "INC-003"
    INC_INVALID_SOURCE = "INC-004"  # Added: strict non-empty source validation
    
    # Expense errors (EXP-xxx)
    EXP_NOT_FOUND = "EXP-001"
    EXP_INVALID_AMOUNT = "EXP-002"
    EXP_UNAUTHORIZED = "EXP-003"
    EXP_INVALID_CATEGORY = "EXP-004"  # Added: strict non-empty category validation
    
    # Report errors (RPT-xxx)
    RPT_INVALID_MONTH = "RPT-001"
    RPT_NO_DATA = "RPT-002"
    
    # System errors (SYS-xxx)
    SYS_INTERNAL_ERROR = "SYS-001"
    SYS_DATABASE_ERROR = "SYS-002"