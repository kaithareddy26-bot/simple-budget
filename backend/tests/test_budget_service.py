import pytest
from unittest.mock import Mock
from uuid import uuid4
from decimal import Decimal
from app.services.budget_service import BudgetService
from app.models.budget import Budget
from app.schemas.error_schemas import ErrorCodes


class TestBudgetService:
    """Unit tests for BudgetService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repo = Mock()
        self.service = BudgetService(self.mock_repo)
        self.user_id = uuid4()
    
    def test_create_budget_success(self):
        """Test successful budget creation."""
        # Arrange
        self.mock_repo.get_by_user_and_month.return_value = None
        self.mock_repo.create.return_value = Budget(
            id=uuid4(),
            user_id=self.user_id,
            month="2024-03",
            amount=Decimal("5000.00")
        )
        
        # Act
        budget = self.service.create_budget(
            user_id=self.user_id,
            month="2024-03",
            amount=Decimal("5000.00")
        )
        
        # Assert
        assert budget.month == "2024-03"
        assert budget.amount == Decimal("5000.00")
        self.mock_repo.create.assert_called_once()
    
    def test_create_budget_duplicate_month(self):
        """Test creating budget for existing month."""
        # Arrange
        self.mock_repo.get_by_user_and_month.return_value = Budget(
            id=uuid4(),
            user_id=self.user_id,
            month="2024-03",
            amount=Decimal("5000.00")
        )
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.create_budget(
                user_id=self.user_id,
                month="2024-03",
                amount=Decimal("6000.00")
            )
        
        assert ErrorCodes.BUD_ALREADY_EXISTS in str(exc_info.value)
    
    def test_create_budget_invalid_amount(self):
        """Test creating budget with invalid amount."""
        # Arrange
        self.mock_repo.get_by_user_and_month.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.create_budget(
                user_id=self.user_id,
                month="2024-03",
                amount=Decimal("0")
            )
        
        assert ErrorCodes.BUD_INVALID_AMOUNT in str(exc_info.value)
    
    def test_get_budget_by_id_success(self):
        """Test successful budget retrieval."""
        # Arrange
        budget_id = uuid4()
        self.mock_repo.get_by_id.return_value = Budget(
            id=budget_id,
            user_id=self.user_id,
            month="2024-03",
            amount=Decimal("5000.00")
        )
        
        # Act
        budget = self.service.get_budget_by_id(budget_id, self.user_id)
        
        # Assert
        assert budget.id == budget_id
        assert budget.user_id == self.user_id
    
    def test_get_budget_by_id_not_found(self):
        """Test getting non-existent budget."""
        # Arrange
        budget_id = uuid4()
        self.mock_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.get_budget_by_id(budget_id, self.user_id)
        
        assert ErrorCodes.BUD_NOT_FOUND in str(exc_info.value)
    
    def test_get_budget_by_id_unauthorized(self):
        """Test unauthorized budget access."""
        # Arrange
        budget_id = uuid4()
        other_user_id = uuid4()
        self.mock_repo.get_by_id.return_value = Budget(
            id=budget_id,
            user_id=other_user_id,
            month="2024-03",
            amount=Decimal("5000.00")
        )
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.get_budget_by_id(budget_id, self.user_id)
        
        assert ErrorCodes.BUD_UNAUTHORIZED in str(exc_info.value)
    
    def test_update_budget_amount_success(self):
        """Test successful budget update."""
        # Arrange
        budget_id = uuid4()
        budget = Budget(
            id=budget_id,
            user_id=self.user_id,
            month="2024-03",
            amount=Decimal("5000.00")
        )
        self.mock_repo.get_by_id.return_value = budget
        self.mock_repo.update.return_value = budget
        
        # Act
        updated_budget = self.service.update_budget_amount(
            budget_id=budget_id,
            user_id=self.user_id,
            new_amount=Decimal("6000.00")
        )
        
        # Assert
        assert updated_budget.amount == Decimal("6000.00")
        self.mock_repo.update.assert_called_once()
    
    def test_update_budget_amount_invalid(self):
        """Test updating budget with invalid amount."""
        # Arrange
        budget_id = uuid4()
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.update_budget_amount(
                budget_id=budget_id,
                user_id=self.user_id,
                new_amount=Decimal("-100.00")
            )
        
        assert ErrorCodes.BUD_INVALID_AMOUNT in str(exc_info.value)

    def test_update_budget_amount_not_found(self):
        budget_id = uuid4()
        self.mock_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc_info:
            self.service.update_budget_amount(
                budget_id=budget_id,
                user_id=self.user_id,
                new_amount=Decimal("100.00")
            )

        assert ErrorCodes.BUD_NOT_FOUND in str(exc_info.value)
        self.mock_repo.update.assert_not_called()

    def test_get_current_month_budget_not_found(self):
        """Test current month budget retrieval when budget does not exist."""
        self.mock_repo.get_by_user_and_month.return_value = None

        with pytest.raises(ValueError) as exc_info:
            self.service.get_current_month_budget(self.user_id)

        assert ErrorCodes.BUD_NOT_FOUND in str(exc_info.value)
        self.mock_repo.get_by_user_and_month.assert_called_once()
        
    # -----------------------------
    # New tests: strict month validation + DB IntegrityError mapping
    # -----------------------------

    def test_create_budget_invalid_month_format(self):
        """Test creating budget with invalid month format (strict YYYY-MM)."""
        # Arrange
        self.mock_repo.get_by_user_and_month.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.create_budget(
                user_id=self.user_id,
                month="2024-3",  # invalid (must be YYYY-MM)
                amount=Decimal("100.00")
            )

        assert ErrorCodes.BUD_INVALID_MONTH in str(exc_info.value)
        self.mock_repo.get_by_user_and_month.assert_not_called()
        self.mock_repo.create.assert_not_called()

    def test_create_budget_invalid_month_out_of_range(self):
        """Test creating budget with invalid month range (e.g., 00 or 13)."""
        # Arrange
        self.mock_repo.get_by_user_and_month.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.create_budget(
                user_id=self.user_id,
                month="2024-13",  # invalid month
                amount=Decimal("100.00")
            )

        assert ErrorCodes.BUD_INVALID_MONTH in str(exc_info.value)
        self.mock_repo.get_by_user_and_month.assert_not_called()
        self.mock_repo.create.assert_not_called()

    def test_create_budget_db_unique_violation_maps_to_already_exists(self):
        """Test DB unique constraint violation maps to BUD_ALREADY_EXISTS (race condition safe)."""
        # Arrange
        self.mock_repo.get_by_user_and_month.return_value = None

        # IntegrityError stub that behaves like sqlalchemy.exc.IntegrityError enough for our mapping
        class IntegrityErrorStub(Exception):
            def __init__(self, orig):
                self.orig = orig

        # Make repo.create raise a unique constraint violation
        self.mock_repo.create.side_effect = IntegrityErrorStub(
            'duplicate key value violates unique constraint "uq_user_month"'
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.create_budget(
                user_id=self.user_id,
                month="2024-03",
                amount=Decimal("5000.00")
            )

        assert ErrorCodes.BUD_ALREADY_EXISTS in str(exc_info.value)
        self.mock_repo.get_by_user_and_month.assert_called_once_with(self.user_id, "2024-03")
        self.mock_repo.create.assert_called_once()

    def test_create_budget_db_month_check_violation_maps_to_invalid_month(self):
        """Test DB month format check constraint violation maps to BUD_INVALID_MONTH."""
        # Arrange
        self.mock_repo.get_by_user_and_month.return_value = None

        class IntegrityErrorStub(Exception):
            def __init__(self, orig):
                self.orig = orig

        self.mock_repo.create.side_effect = IntegrityErrorStub(
            'new row for relation "budgets" violates check constraint "ck_budgets_month_format"'
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.create_budget(
                user_id=self.user_id,
                month="2024-03",
                amount=Decimal("5000.00")
            )

        assert ErrorCodes.BUD_INVALID_MONTH in str(exc_info.value)
        self.mock_repo.create.assert_called_once()

    def test_create_budget_db_amount_check_violation_maps_to_invalid_amount(self):
        """Test DB amount check constraint violation maps to BUD_INVALID_AMOUNT."""
        # Arrange
        self.mock_repo.get_by_user_and_month.return_value = None

        class IntegrityErrorStub(Exception):
            def __init__(self, orig):
                self.orig = orig

        self.mock_repo.create.side_effect = IntegrityErrorStub(
            'new row for relation "budgets" violates check constraint "ck_budgets_amount_positive"'
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.create_budget(
                user_id=self.user_id,
                month="2024-03",
                amount=Decimal("5000.00")
            )

        assert ErrorCodes.BUD_INVALID_AMOUNT in str(exc_info.value)
        self.mock_repo.create.assert_called_once()

