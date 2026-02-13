import pytest
from unittest.mock import Mock
from uuid import uuid4
from decimal import Decimal
from datetime import date, datetime
from app.services.report_service import ReportService
from app.models.income import Income
from app.models.expense import Expense
from app.schemas.error_schemas import ErrorCodes


class TestReportService:
    """Unit tests for ReportService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_income_repo = Mock()
        self.mock_expense_repo = Mock()
        self.service = ReportService(self.mock_income_repo, self.mock_expense_repo)
        self.user_id = uuid4()
    
    def test_get_monthly_summary_success(self):
        """Test successful monthly summary generation."""
        # Arrange
        incomes = [
            Income(
                id=uuid4(),
                user_id=self.user_id,
                amount=Decimal("3000.00"),
                source="Salary",
                date=date(2024, 3, 15)
            ),
            Income(
                id=uuid4(),
                user_id=self.user_id,
                amount=Decimal("500.00"),
                source="Freelance",
                date=date(2024, 3, 20)
            )
        ]
        
        expenses = [
            Expense(
                id=uuid4(),
                user_id=self.user_id,
                amount=Decimal("200.00"),
                category="Groceries",
                date=date(2024, 3, 5),
                note=None
            ),
            Expense(
                id=uuid4(),
                user_id=self.user_id,
                amount=Decimal("150.00"),
                category="Groceries",
                date=date(2024, 3, 12),
                note=None
            ),
            Expense(
                id=uuid4(),
                user_id=self.user_id,
                amount=Decimal("100.00"),
                category="Utilities",
                date=date(2024, 3, 1),
                note=None
            )
        ]
        
        self.mock_income_repo.get_by_user_and_date_range.return_value = incomes
        self.mock_expense_repo.get_by_user_and_date_range.return_value = expenses
        
        # Act
        summary = self.service.get_monthly_summary(self.user_id, "2024-03")
        
        # Assert
        assert summary["month"] == "2024-03"
        assert summary["total_income"] == Decimal("3500.00")
        assert summary["total_expenses"] == Decimal("450.00")
        assert summary["net_balance"] == Decimal("3050.00")
        assert summary["expenses_by_category"]["Groceries"] == Decimal("350.00")
        assert summary["expenses_by_category"]["Utilities"] == Decimal("100.00")
    
    def test_get_monthly_summary_no_data(self):
        """Test monthly summary with no income or expenses."""
        # Arrange
        self.mock_income_repo.get_by_user_and_date_range.return_value = []
        self.mock_expense_repo.get_by_user_and_date_range.return_value = []
        
        # Act
        summary = self.service.get_monthly_summary(self.user_id, "2024-03")
        
        # Assert
        assert summary["total_income"] == Decimal("0")
        assert summary["total_expenses"] == Decimal("0")
        assert summary["net_balance"] == Decimal("0")
        assert summary["expenses_by_category"] == {}
    
    def test_get_monthly_summary_invalid_month_format(self):
        """Test monthly summary with invalid month format."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.get_monthly_summary(self.user_id, "2024/03")
        
        assert ErrorCodes.RPT_INVALID_MONTH in str(exc_info.value)
    
    def test_get_monthly_summary_invalid_month_number(self):
        """Test monthly summary with invalid month number."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.get_monthly_summary(self.user_id, "2024-13")
        
        assert ErrorCodes.RPT_INVALID_MONTH in str(exc_info.value)
    
    def test_get_monthly_summary_expenses_grouped_correctly(self):
        """Test that expenses are correctly grouped by category."""
        # Arrange
        expenses = [
            Expense(
                id=uuid4(),
                user_id=self.user_id,
                amount=Decimal("100.00"),
                category="Food",
                date=date(2024, 3, 1),
                note=None
            ),
            Expense(
                id=uuid4(),
                user_id=self.user_id,
                amount=Decimal("150.00"),
                category="Food",
                date=date(2024, 3, 5),
                note=None
            ),
            Expense(
                id=uuid4(),
                user_id=self.user_id,
                amount=Decimal("50.00"),
                category="Transport",
                date=date(2024, 3, 10),
                note=None
            ),
            Expense(
                id=uuid4(),
                user_id=self.user_id,
                amount=Decimal("75.00"),
                category="Food",
                date=date(2024, 3, 15),
                note=None
            )
        ]
        
        self.mock_income_repo.get_by_user_and_date_range.return_value = []
        self.mock_expense_repo.get_by_user_and_date_range.return_value = expenses
        
        # Act
        summary = self.service.get_monthly_summary(self.user_id, "2024-03")
        
        # Assert
        assert summary["expenses_by_category"]["Food"] == Decimal("325.00")
        assert summary["expenses_by_category"]["Transport"] == Decimal("50.00")
        assert len(summary["expenses_by_category"]) == 2
