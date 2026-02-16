from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID
from decimal import Decimal
from datetime import datetime
import re


class BudgetCreateRequest(BaseModel):
    """Budget creation request schema."""
    
    month: str = Field(..., description="Budget month in YYYY-MM format")
    amount: Decimal = Field(..., gt=0, description="Budget amount (must be > 0)")
    
    @field_validator('month')
    @classmethod
    def validate_month_format(cls, v: str) -> str:
        if not re.match(r'^\d{4}-\d{2}$', v):
            raise ValueError("Month must be in YYYY-MM format")
        year, month = v.split('-')
        if not (1 <= int(month) <= 12):
            raise ValueError("Month must be between 01 and 12")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "month": "2024-03",
                "amount": 5000.00
            }
        }
    )


class BudgetUpdateRequest(BaseModel):
    """Budget update request schema."""
    
    amount: Decimal = Field(..., gt=0, description="New budget amount (must be > 0)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 5500.00
            }
        }
    )


class BudgetResponse(BaseModel):
    """Budget response schema."""
    
    id: UUID = Field(serialization_alias="budgetId")
    user_id: UUID = Field(serialization_alias="userId")
    month: str
    amount: Decimal = Field(serialization_alias="totalAmount")
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")
    updated_at: datetime | None = Field(default=None, serialization_alias="updatedAt")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "budgetId": "550e8400-e29b-41d4-a716-446655440000",
                "userId": "660e8400-e29b-41d4-a716-446655440000",
                "month": "2024-03",
                "totalAmount": 5000.00,
                "createdAt": "2024-03-01T00:00:00Z",
                "updatedAt": "2024-03-02T00:00:00Z"
            }
        }
    )