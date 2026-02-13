from uuid import UUID
from decimal import Decimal
from datetime import date
from typing import Optional
from app.models.expense import Expense
from app.repositories.expense_repository import ExpenseRepository
from app.schemas.error_schemas import ErrorCodes


class ExpenseService:
    """Expense service containing business logic."""
    
    def __init__(self, expense_repository: ExpenseRepository):
        self.expense_repository = expense_repository
    
    def add_expense(
        self,
        user_id: UUID,
        amount: Decimal,
        category: str,
        expense_date: date,
        note: Optional[str] = None
    ) -> Expense:
        """
        Add a new expense record.
        
        Business Rules:
        - Amount must be greater than 0
        - Expense is user-scoped
        
        Raises:
            ValueError: If amount <= 0
        """
        # Validate amount
        if amount <= 0:
            raise ValueError(f"{ErrorCodes.EXP_INVALID_AMOUNT}:Expense amount must be greater than 0")
        
        # Create expense entity
        expense = Expense(
            user_id=user_id,
            amount=amount,
            category=category,
            date=expense_date,
            note=note
        )
        
        # Persist expense
        return self.expense_repository.create(expense)
