from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional
import re
from app.models.budget import Budget
from app.repositories.budget_repository import BudgetRepository
from app.schemas.error_schemas import ErrorCodes

try:
    from sqlalchemy.exc import IntegrityError as SAIntegrityError
except Exception:
    SAIntegrityError = None


class BudgetService:
    """Budget service — enforces all budget business rules.

    Responsibilities:
    - Month format and range validation (YYYY-MM, 01-12)
    - Amount validation (must be > 0)
    - User-scoped access control (users can only read/update their own budgets)
    - Duplicate-budget prevention with race-condition-safe DB fallback
    """

    _MONTH_RE = re.compile(r"^\d{4}-\d{2}$")

    def __init__(self, budget_repository: BudgetRepository):
        self.budget_repository = budget_repository

    @classmethod
    def _validate_month_strict(cls, month: str) -> None:
        """Validate that month is a string in YYYY-MM format with MM in 01-12.

        Raises:
            ValueError: BUD_INVALID_MONTH if format or range is invalid.
        """
        if not isinstance(month, str) or not cls._MONTH_RE.match(month):
            raise ValueError(
                f"{ErrorCodes.BUD_INVALID_MONTH}:Month must be in YYYY-MM format"
            )
        mm = int(month[5:7])
        if mm < 1 or mm > 12:
            raise ValueError(
                f"{ErrorCodes.BUD_INVALID_MONTH}:Month must be in YYYY-MM format"
            )

    def create_budget(self, user_id: UUID, month: str, amount: Decimal) -> Budget:
        """Create a new monthly budget for the given user.

        Business rules:
        - One budget per user per month (unique constraint)
        - Amount must be greater than 0
        - Month must be YYYY-MM with MM in 01-12

        Raises:
            ValueError: BUD_INVALID_MONTH, BUD_INVALID_AMOUNT, or BUD_ALREADY_EXISTS.
        """
        self._validate_month_strict(month)

        if amount <= 0:
            raise ValueError(
                f"{ErrorCodes.BUD_INVALID_AMOUNT}:Budget amount must be greater than 0"
            )

        existing_budget = self.budget_repository.get_by_user_and_month(user_id, month)
        if existing_budget:
            raise ValueError(
                f"{ErrorCodes.BUD_ALREADY_EXISTS}:Budget already exists for this month"
            )

        budget = Budget(user_id=user_id, month=month, amount=amount)

        try:
            return self.budget_repository.create(budget)
        except Exception as e:
            if SAIntegrityError is not None and isinstance(e, SAIntegrityError):
                db_error = str(getattr(e, "orig", e)).lower()
            elif hasattr(e, "orig"):
                db_error = str(getattr(e, "orig")).lower()
            else:
                raise

            if (
                "uq_user_month" in db_error
                or "unique constraint" in db_error
                or "duplicate key" in db_error
            ):
                raise ValueError(
                    f"{ErrorCodes.BUD_ALREADY_EXISTS}:"
                    "Budget already exists for this month"
                ) from e

            if "ck_budgets_amount_positive" in db_error or (
                "check constraint" in db_error and "amount" in db_error
            ):
                raise ValueError(
                    f"{ErrorCodes.BUD_INVALID_AMOUNT}:"
                    "Budget amount must be greater than 0"
                ) from e

            if "ck_budgets_month_format" in db_error or (
                "check constraint" in db_error and "month" in db_error
            ):
                raise ValueError(
                    f"{ErrorCodes.BUD_INVALID_MONTH}:"
                    "Month must be in YYYY-MM format"
                ) from e

            raise

    def get_budget_by_id(self, budget_id: UUID, user_id: UUID) -> Budget:
        """Return the budget identified by budget_id, enforcing user ownership.

        Raises:
            ValueError: BUD_NOT_FOUND if the budget does not exist,
                        BUD_UNAUTHORIZED if it belongs to a different user.
        """
        budget = self.budget_repository.get_by_id(budget_id)
        if not budget:
            raise ValueError(f"{ErrorCodes.BUD_NOT_FOUND}:Budget not found")
        if budget.user_id != user_id:
            raise ValueError(
                f"{ErrorCodes.BUD_UNAUTHORIZED}:Unauthorized access to budget"
            )
        return budget

    def update_budget_amount(
        self, budget_id: UUID, user_id: UUID, new_amount: Decimal
    ) -> Budget:
        """Update the amount on an existing budget owned by user_id.

        Raises:
            ValueError: BUD_INVALID_AMOUNT, BUD_NOT_FOUND, or BUD_UNAUTHORIZED.
        """
        if new_amount <= 0:
            raise ValueError(
                f"{ErrorCodes.BUD_INVALID_AMOUNT}:Budget amount must be greater than 0"
            )
        budget = self.get_budget_by_id(budget_id, user_id)
        budget.amount = new_amount
        return self.budget_repository.update(budget)

    def get_current_month_budget(self, user_id: UUID) -> Budget:
        """Return the budget for the current calendar month (UTC) for user_id.

        Raises:
            ValueError: BUD_NOT_FOUND if no budget exists for the current month.
        """
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        budget = self.budget_repository.get_by_user_and_month(user_id, current_month)
        if not budget:
            raise ValueError(f"{ErrorCodes.BUD_NOT_FOUND}:Budget not found")
        return budget