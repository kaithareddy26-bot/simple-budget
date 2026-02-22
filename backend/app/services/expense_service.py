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
        - Category must be non-empty (strict)
        - Expense is user-scoped
        
        Raises:
            ValueError: If amount <= 0 or category invalid
        """
        # Validate amount
        if amount <= 0:
            raise ValueError(f"{ErrorCodes.EXP_INVALID_AMOUNT}:Expense amount must be greater than 0")
        
        if not isinstance(category, str) or not category.strip():
            raise ValueError(f"{ErrorCodes.EXP_INVALID_CATEGORY}:Expense category must be provided")
        
        # Create expense entity
        expense = Expense(
            user_id=user_id,
            amount=amount,
            category=category.strip(),
            date=expense_date,
            note=note
        )
        
        # Persist expense
        return self.expense_repository.create(expense)
    
    def get_current_month_expenses(self, user_id: UUID) -> list[Expense]:
        """
        Get current month's expenses for a user.
        
        """
        from datetime import datetime
        current_month = datetime.now().strftime("%Y-%m")
        print("DEBUG: Fetching current month expenses for user_id:", user_id, "current_month:", current_month)
        return self.expense_repository.get_by_user_and_month(user_id, current_month)