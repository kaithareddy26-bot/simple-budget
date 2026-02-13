from uuid import UUID
from decimal import Decimal
from typing import Optional
from app.models.budget import Budget
from app.repositories.budget_repository import BudgetRepository
from app.schemas.error_schemas import ErrorCodes


class BudgetService:
    """Budget service containing business logic."""
    
    def __init__(self, budget_repository: BudgetRepository):
        self.budget_repository = budget_repository
    
    def create_budget(self, user_id: UUID, month: str, amount: Decimal) -> Budget:
        """
        Create a new monthly budget.
        
        Business Rules:
        - One budget per user per month
        - Amount must be greater than 0
        
        Raises:
            ValueError: If budget already exists for user and month, or if amount <= 0
        """
        # Validate amount
        if amount <= 0:
            raise ValueError(f"{ErrorCodes.BUD_INVALID_AMOUNT}:Budget amount must be greater than 0")
        
        # Check if budget already exists for user and month
        existing_budget = self.budget_repository.get_by_user_and_month(user_id, month)
        if existing_budget:
            raise ValueError(f"{ErrorCodes.BUD_ALREADY_EXISTS}:Budget already exists for this month")
        
        # Create budget entity
        budget = Budget(
            user_id=user_id,
            month=month,
            amount=amount
        )
        
        # Persist budget
        return self.budget_repository.create(budget)
    
    def get_budget_by_id(self, budget_id: UUID, user_id: UUID) -> Optional[Budget]:
        """
        Get budget by ID.
        
        Business Rules:
        - User can only access their own budgets
        
        Raises:
            ValueError: If budget not found or unauthorized access
        """
        budget = self.budget_repository.get_by_id(budget_id)
        
        if not budget:
            raise ValueError(f"{ErrorCodes.BUD_NOT_FOUND}:Budget not found")
        
        # Enforce user-scoped access
        if budget.user_id != user_id:
            raise ValueError(f"{ErrorCodes.BUD_UNAUTHORIZED}:Unauthorized access to budget")
        
        return budget
    
    def update_budget_amount(self, budget_id: UUID, user_id: UUID, new_amount: Decimal) -> Budget:
        """
        Update budget amount.
        
        Business Rules:
        - User can only update their own budgets
        - Amount must be greater than 0
        
        Raises:
            ValueError: If budget not found, unauthorized, or invalid amount
        """
        # Validate amount
        if new_amount <= 0:
            raise ValueError(f"{ErrorCodes.BUD_INVALID_AMOUNT}:Budget amount must be greater than 0")
        
        # Get budget
        budget = self.get_budget_by_id(budget_id, user_id)
        
        # Update amount
        budget.amount = new_amount
        
        # Persist changes
        return self.budget_repository.update(budget)
