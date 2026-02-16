from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from typing import Dict
from datetime import datetime


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
    total_income: Decimal = Field(..., serialization_alias="totalIncome", description="Total income for the month")
    total_expenses: Decimal = Field(..., serialization_alias="totalExpenses", description="Total expenses for the month")
    net_balance: Decimal = Field(..., serialization_alias="net", description="Net balance (income - expenses)")
    expenses_by_category: Dict[str, Decimal] = Field(..., serialization_alias="byCategory", description="Expenses grouped by category")
    generated_at: datetime = Field(..., serialization_alias="generatedAt")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "month": "2024-03",
                "totalIncome": 5000.00,
                "totalExpenses": 3200.00,
                "net": 1800.00,
                "byCategory": {
                    "Groceries": 450.00,
                    "Utilities": 200.00,
                    "Transportation": 300.00,
                    "Entertainment": 150.00,
                    "Healthcare": 100.00
                },
                "generatedAt": "2024-03-31T23:59:59Z"
            }
        }
    )