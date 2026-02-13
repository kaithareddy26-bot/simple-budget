from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from typing import Dict


class CategoryExpense(BaseModel):
    """Category expense aggregation schema."""
    
    category: str
    total: Decimal
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "Groceries",
                "total": 450.00
            }
        }
    )


class MonthlySummaryResponse(BaseModel):
    """Monthly summary report response schema."""
    
    month: str = Field(..., description="Report month in YYYY-MM format")
    total_income: Decimal = Field(..., description="Total income for the month")
    total_expenses: Decimal = Field(..., description="Total expenses for the month")
    net_balance: Decimal = Field(..., description="Net balance (income - expenses)")
    expenses_by_category: Dict[str, Decimal] = Field(..., description="Expenses grouped by category")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "month": "2024-03",
                "total_income": 5000.00,
                "total_expenses": 3200.00,
                "net_balance": 1800.00,
                "expenses_by_category": {
                    "Groceries": 450.00,
                    "Utilities": 200.00,
                    "Transportation": 300.00,
                    "Entertainment": 150.00,
                    "Healthcare": 100.00
                }
            }
        }
    )