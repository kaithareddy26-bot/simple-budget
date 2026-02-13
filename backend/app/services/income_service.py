from uuid import UUID
from decimal import Decimal
from datetime import date
from app.models.income import Income
from app.repositories.income_repository import IncomeRepository
from app.schemas.error_schemas import ErrorCodes


class IncomeService:
    """Income service containing business logic."""
    
    def __init__(self, income_repository: IncomeRepository):
        self.income_repository = income_repository
    
    def add_income(
        self,
        user_id: UUID,
        amount: Decimal,
        source: str,
        income_date: date
    ) -> Income:
        """
        Add a new income record.
        
        Business Rules:
        - Amount must be greater than 0
        - Income is user-scoped
        
        Raises:
            ValueError: If amount <= 0
        """
        # Validate amount
        if amount <= 0:
            raise ValueError(f"{ErrorCodes.INC_INVALID_AMOUNT}:Income amount must be greater than 0")
        
        # Create income entity
        income = Income(
            user_id=user_id,
            amount=amount,
            source=source,
            date=income_date
        )
        
        # Persist income
        return self.income_repository.create(income)
