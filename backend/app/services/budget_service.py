from uuid import UUID
from decimal import Decimal
from typing import Optional
import re
from app.models.budget import Budget
from app.repositories.budget_repository import BudgetRepository
from app.schemas.error_schemas import ErrorCodes

# Compatibility: allow tests to run even if SQLAlchemy isn't installed/resolved by the editor
try:
    from sqlalchemy.exc import IntegrityError as SAIntegrityError
except Exception:
    SAIntegrityError = None

class BudgetService:
    """Budget service containing business logic."""
    
    # Strict YYYY-MM (e.g., 2026-02). Note: does not validate month range 01-12.
    _MONTH_RE = re.compile(r"^\d{4}-\d{2}$")

    def __init__(self, budget_repository: BudgetRepository):
        self.budget_repository = budget_repository
    
    @classmethod
    def _validate_month_strict(cls, month: str) -> None:
        """
        Strictly validate month in YYYY-MM format.
        Raises ValueError with ErrorCodes on failure.
        """
        if not isinstance(month, str) or not cls._MONTH_RE.match(month):
            raise ValueError(f"{ErrorCodes.BUD_INVALID_MONTH}:Month must be in YYYY-MM format")

        # Enforce month range 01-12 (stricter than the DB regex, but matches domain expectations)
        mm = int(month[5:7])
        if mm < 1 or mm > 12:
            raise ValueError(f"{ErrorCodes.BUD_INVALID_MONTH}:Month must be in YYYY-MM format")

    def create_budget(self, user_id: UUID, month: str, amount: Decimal) -> Budget:
        """
        Create a new monthly budget.
        
        Business Rules:
        - One budget per user per month
        - Amount must be greater than 0
        - Month must be in YYYY-MM format (strict)
        
        Raises:
            ValueError: If budget already exists for user and month, invalid month, or amount <= 0
        """
        # Validate month strictly (service-layer)
        self._validate_month_strict(month)

        # Validate amount
        if amount <= 0:
            raise ValueError(f"{ErrorCodes.BUD_INVALID_AMOUNT}:Budget amount must be greater than 0")
        
        # Pre-check (still useful for friendly errors, but DB enforces uniqueness)
        existing_budget = self.budget_repository.get_by_user_and_month(user_id, month)
        if existing_budget:
            raise ValueError(f"{ErrorCodes.BUD_ALREADY_EXISTS}:Budget already exists for this month")
        
        # Create budget entity
        budget = Budget(
            user_id=user_id,
            month=month,
            amount=amount
        )
        
        # Persist budget (catch DB enforcement for concurrency/race conditions)
        try:
            return self.budget_repository.create(budget)
        except Exception as e:
            # Compatibility: handle both real SQLAlchemy IntegrityError and test IntegrityErrorStub (.orig)
            if SAIntegrityError is not None and isinstance(e, SAIntegrityError):
                db_error = str(getattr(e, "orig", e)).lower()
            elif hasattr(e, "orig"):
                db_error = str(getattr(e, "orig")).lower()
            else:
                raise  # Not a DB integrity error we know how to map

            # Map DB enforcement back to consistent domain errors (race-condition safe)
            if "uq_user_month" in db_error or "unique constraint" in db_error or "duplicate key" in db_error:
                raise ValueError(f"{ErrorCodes.BUD_ALREADY_EXISTS}:Budget already exists for this month") from e

            if "ck_budgets_amount_positive" in db_error or ("check constraint" in db_error and "amount" in db_error):
                raise ValueError(f"{ErrorCodes.BUD_INVALID_AMOUNT}:Budget amount must be greater than 0") from e

            if "ck_budgets_month_format" in db_error or ("check constraint" in db_error and "month" in db_error):
                raise ValueError(f"{ErrorCodes.BUD_INVALID_MONTH}:Month must be in YYYY-MM format") from e

            # Unknown integrity error: re-raise for middleware/logging
            raise
    
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
    
    def get_current_month_budget(self, user_id: UUID) -> Optional[Budget]:
        """
        Get current month's budget for a user.
        
        """
        from datetime import datetime
        current_month = datetime.now().strftime("%Y-%m")
        print("DEBUG: Fetching current month budget for user_id:", user_id, "current_month:", current_month)
        budget = self.budget_repository.get_by_user_and_month(user_id, current_month)

        if not budget:
            raise ValueError(f"{ErrorCodes.BUD_NOT_FOUND}:Budget not found")

        return budget