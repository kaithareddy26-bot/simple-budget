from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from decimal import Decimal
from datetime import date as date_type
from datetime import datetime


class IncomeCreateRequest(BaseModel):
    """Income creation request schema."""
    
    amount: Decimal = Field(..., gt=0, description="Income amount (must be > 0)")
    source: str = Field(..., min_length=1, max_length=255, description="Income source")
    date: date_type = Field(..., description="Income date")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 3500.00,
                "source": "Monthly Salary",
                "date": "2024-03-15"
            }
        }
    )


class IncomeResponse(BaseModel):
    """Income response schema."""
    
    id: UUID = Field(serialization_alias="incomeId")
    user_id: UUID = Field(serialization_alias="userId")
    amount: Decimal
    source: str
    date: date_type
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "incomeId": "550e8400-e29b-41d4-a716-446655440000",
                "userId": "660e8400-e29b-41d4-a716-446655440000",
                "amount": 3500.00,
                "source": "Monthly Salary",
                "date": "2024-03-15",
                "createdAt": "2024-03-15T12:00:00Z"
            }
        }
    )