import pytest
from unittest.mock import Mock
from uuid import uuid4
from decimal import Decimal
from datetime import date
from app.services.income_service import IncomeService
from app.models.income import Income
from app.schemas.error_schemas import ErrorCodes


class TestIncomeService:
    """Unit tests for IncomeService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repo = Mock()
        self.service = IncomeService(self.mock_repo)
        self.user_id = uuid4()
    
    def test_add_income_success(self):
        """Test successful income addition."""
        # Arrange
        self.mock_repo.create.return_value = Income(
            id=uuid4(),
            user_id=self.user_id,
            amount=Decimal("3500.00"),
            source="Salary",
            date=date(2024, 3, 15)
        )
        
        # Act
        income = self.service.add_income(
            user_id=self.user_id,
            amount=Decimal("3500.00"),
            source="Salary",
            income_date=date(2024, 3, 15)
        )
        
        # Assert
        assert income.amount == Decimal("3500.00")
        assert income.source == "Salary"
        assert income.date == date(2024, 3, 15)
        self.mock_repo.create.assert_called_once()
    
    def test_add_income_invalid_amount_zero(self):
        """Test adding income with zero amount."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.add_income(
                user_id=self.user_id,
                amount=Decimal("0"),
                source="Salary",
                income_date=date(2024, 3, 15)
            )
        
        assert ErrorCodes.INC_INVALID_AMOUNT in str(exc_info.value)
    
    def test_add_income_invalid_amount_negative(self):
        """Test adding income with negative amount."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.add_income(
                user_id=self.user_id,
                amount=Decimal("-100.00"),
                source="Salary",
                income_date=date(2024, 3, 15)
            )
        
        assert ErrorCodes.INC_INVALID_AMOUNT in str(exc_info.value)
    
    def test_add_income_various_sources(self):
        """Test adding income from various sources."""
        # Arrange
        sources = ["Salary", "Freelance", "Investment", "Gift"]
        
        for source in sources:
            self.mock_repo.create.return_value = Income(
                id=uuid4(),
                user_id=self.user_id,
                amount=Decimal("1000.00"),
                source=source,
                date=date(2024, 3, 15)
            )
            
            # Act
            income = self.service.add_income(
                user_id=self.user_id,
                amount=Decimal("1000.00"),
                source=source,
                income_date=date(2024, 3, 15)
            )
            
            # Assert
            assert income.source == source
