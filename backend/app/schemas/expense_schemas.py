from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from decimal import Decimal
from datetime import date as date_type
from typing import Optional


class ExpenseCreateRequest(BaseModel):
    """Expense creation request schema."""
    
    amount: Decimal = Field(..., gt=0, description="Expense amount (must be > 0)")
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
    
    id: UUID
    user_id: UUID
    amount: Decimal
    category: str
    date: date_type
    note: Optional[str]
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "660e8400-e29b-41d4-a716-446655440000",
                "amount": 150.00,
                "category": "Groceries",
                "date": "2024-03-10",
                "note": "Weekly shopping at supermarket"
            }
        }
    )