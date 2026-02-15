import pytest
from unittest.mock import Mock
from uuid import uuid4
from decimal import Decimal
from datetime import date
from app.services.expense_service import ExpenseService
from app.models.expense import Expense
from app.schemas.error_schemas import ErrorCodes


class TestExpenseService:
    """Unit tests for ExpenseService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repo = Mock()
        self.service = ExpenseService(self.mock_repo)
        self.user_id = uuid4()
    
    def test_add_expense_success(self):
        """Test successful expense addition."""
        # Arrange
        self.mock_repo.create.return_value = Expense(
            id=uuid4(),
            user_id=self.user_id,
            amount=Decimal("150.00"),
            category="Groceries",
            date=date(2024, 3, 10),
            note="Weekly shopping"
        )
        
        # Act
        expense = self.service.add_expense(
            user_id=self.user_id,
            amount=Decimal("150.00"),
            category="Groceries",
            expense_date=date(2024, 3, 10),
            note="Weekly shopping"
        )
        
        # Assert
        assert expense.amount == Decimal("150.00")
        assert expense.category == "Groceries"
        assert expense.date == date(2024, 3, 10)
        assert expense.note == "Weekly shopping"
        self.mock_repo.create.assert_called_once()
    
    def test_add_expense_without_note(self):
        """Test adding expense without note."""
        # Arrange
        self.mock_repo.create.return_value = Expense(
            id=uuid4(),
            user_id=self.user_id,
            amount=Decimal("50.00"),
            category="Transportation",
            date=date(2024, 3, 12),
            note=None
        )
        
        # Act
        expense = self.service.add_expense(
            user_id=self.user_id,
            amount=Decimal("50.00"),
            category="Transportation",
            expense_date=date(2024, 3, 12),
            note=None
        )
        
        # Assert
        assert expense.note is None
    
    def test_add_expense_invalid_amount_zero(self):
        """Test adding expense with zero amount."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.add_expense(
                user_id=self.user_id,
                amount=Decimal("0"),
                category="Food",
                expense_date=date(2024, 3, 10)
            )
        
        assert ErrorCodes.EXP_INVALID_AMOUNT in str(exc_info.value)
    
    def test_add_expense_invalid_amount_negative(self):
        """Test adding expense with negative amount."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.add_expense(
                user_id=self.user_id,
                amount=Decimal("-50.00"),
                category="Food",
                expense_date=date(2024, 3, 10)
            )
        
        assert ErrorCodes.EXP_INVALID_AMOUNT in str(exc_info.value)
    
    def test_add_expense_various_categories(self):
        """Test adding expenses from various categories."""
        # Arrange
        categories = ["Groceries", "Utilities", "Transportation", "Entertainment", "Healthcare"]
        
        for category in categories:
            self.mock_repo.create.return_value = Expense(
                id=uuid4(),
                user_id=self.user_id,
                amount=Decimal("100.00"),
                category=category,
                date=date(2024, 3, 15),
                note=None
            )
            
            # Act
            expense = self.service.add_expense(
                user_id=self.user_id,
                amount=Decimal("100.00"),
                category=category,
                expense_date=date(2024, 3, 15)
            )
            
            # Assert
            assert expense.category == category

    def test_add_expense_invalid_category_empty(self):
        with pytest.raises(ValueError) as exc_info:
            self.service.add_expense(
                user_id=self.user_id,
                amount=Decimal("10.00"),
                category="",
                expense_date=date(2024, 3, 10)
            )
        assert ErrorCodes.EXP_INVALID_CATEGORY in str(exc_info.value)

    def test_add_expense_invalid_category_whitespace(self):
        with pytest.raises(ValueError) as exc_info:
            self.service.add_expense(
                user_id=self.user_id,
                amount=Decimal("10.00"),
                category="   ",
                expense_date=date(2024, 3, 10)
            )
        assert ErrorCodes.EXP_INVALID_CATEGORY in str(exc_info.value)

