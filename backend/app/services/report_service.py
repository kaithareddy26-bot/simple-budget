from uuid import UUID
from decimal import Decimal
from typing import Dict
from abc import ABC, abstractmethod
from app.repositories.income_repository import IncomeRepository
from app.repositories.expense_repository import ExpenseRepository
from app.utils.validators import validate_month_format, get_month_range
from app.schemas.error_schemas import ErrorCodes
from datetime import datetime, timezone


# Strategy Pattern: Report Calculation Strategy
class ReportCalculationStrategy(ABC):
    """Abstract strategy for report calculations."""
    
    @abstractmethod
    def calculate(self, data) -> Decimal:
        """Calculate metric from data."""
        pass


class TotalIncomeStrategy(ReportCalculationStrategy):
    """Strategy for calculating total income."""
    
    def calculate(self, incomes) -> Decimal:
        """Calculate total income."""
        return sum(income.amount for income in incomes) if incomes else Decimal('0')


class TotalExpensesStrategy(ReportCalculationStrategy):
    """Strategy for calculating total expenses."""
    
    def calculate(self, expenses) -> Decimal:
        """Calculate total expenses."""
        return sum(expense.amount for expense in expenses) if expenses else Decimal('0')


class ExpensesByCategoryStrategy(ReportCalculationStrategy):
    """Strategy for grouping expenses by category."""
    
    def calculate(self, expenses) -> Dict[str, Decimal]:
        """Group expenses by category."""
        category_totals = {}
        for expense in expenses:
            if expense.category in category_totals:
                category_totals[expense.category] += expense.amount
            else:
                category_totals[expense.category] = expense.amount
        return category_totals


# Factory Pattern: Report Generator Factory
class ReportGenerator:
    """Base report generator."""
    
    def __init__(
        self,
        income_repository: IncomeRepository,
        expense_repository: ExpenseRepository
    ):
        self.income_repository = income_repository
        self.expense_repository = expense_repository
        self.total_income_strategy = TotalIncomeStrategy()
        self.total_expenses_strategy = TotalExpensesStrategy()
        self.expenses_by_category_strategy = ExpensesByCategoryStrategy()
    
    def generate(self, user_id: UUID, month: str) -> Dict:
        """Generate report."""
        # Get data
        start_date, end_date = get_month_range(month)
        incomes = self.income_repository.get_by_user_and_date_range(
            user_id, start_date, end_date
        )
        expenses = self.expense_repository.get_by_user_and_date_range(
            user_id, start_date, end_date
        )
        
        # Calculate metrics using strategies
        total_income = self.total_income_strategy.calculate(incomes)
        total_expenses = self.total_expenses_strategy.calculate(expenses)
        net_balance = total_income - total_expenses
        expenses_by_category = self.expenses_by_category_strategy.calculate(expenses)
        
        return {
            "month": month,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_balance": net_balance,
            "expenses_by_category": expenses_by_category
        }


class ReportGeneratorFactory:
    """Factory for creating report generators."""
    
    @staticmethod
    def create_monthly_summary_generator(
        income_repository: IncomeRepository,
        expense_repository: ExpenseRepository
    ) -> ReportGenerator:
        """Create monthly summary report generator."""
        return ReportGenerator(income_repository, expense_repository)



# Service Layer
class ReportService:
    """Report service containing business logic."""
    
    def __init__(
        self,
        income_repository: IncomeRepository,
        expense_repository: ExpenseRepository
    ):
        self.income_repository = income_repository
        self.expense_repository = expense_repository

    @staticmethod
    def utc_now():
        return datetime.now(timezone.utc)
    
    def get_monthly_summary(self, user_id: UUID, month: str) -> Dict:
        """
        Generate monthly summary report.
        
        Business Rules:
        - Month must be in valid YYYY-MM format
        - Report includes total income, total expenses, net balance
        - Expenses grouped by category
        
        Raises:
            ValueError: If month format is invalid
        """
        # Validate month format
        is_valid, error_message = validate_month_format(month)
        if not is_valid:
            raise ValueError(f"{ErrorCodes.RPT_INVALID_MONTH}:{error_message}")
        
        # Create report generator using factory
        generator = ReportGeneratorFactory.create_monthly_summary_generator(
            self.income_repository,
            self.expense_repository
        )
        
        # Generate report
        return generator.generate(user_id, month)
