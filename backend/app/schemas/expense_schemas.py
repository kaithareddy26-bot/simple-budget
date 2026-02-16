from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from decimal import Decimal
from datetime import date as date_type
from datetime import datetime
from typing import Optional


class ExpenseCreateRequest(BaseModel):
    """Expense creation request schema."""
    
    amount: Decimal = Field(..., description="Expense amount")
    category: str = Field(..., min_length=1, max_length=100, description="Expense category")
    date: date_type = Field(..., description="Expense date")
    note: Optional[str] = Field(None, description="Optional note")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 150.00,
                "category": "Groceries",
                "date": "2024-03-10",
                "note": "Weekly shopping at supermarket"
            }
        }
    )


class ExpenseResponse(BaseModel):
    """Expense response schema."""
    
    id: UUID = Field(serialization_alias="expenseId")
    user_id: UUID = Field(serialization_alias="userId")
    amount: Decimal
    category: str
    date: date_type
    note: Optional[str]
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "expenseId": "550e8400-e29b-41d4-a716-446655440000",
                "userId": "660e8400-e29b-41d4-a716-446655440000",
                "amount": 150.00,
                "category": "Groceries",
                "date": "2024-03-10",
                "note": "Weekly shopping at supermarket",
                "createdAt": "2024-03-10T12:00:00Z"
            }
        }
    )