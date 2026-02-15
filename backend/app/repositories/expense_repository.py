from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.expense import Expense
from app.repositories.base_repository import BaseRepository


class ExpenseRepository(BaseRepository[Expense]):
    """Expense repository implementation."""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def create(self, entity: Expense) -> Expense:
        """Create a new expense record."""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def get_by_id(self, entity_id: UUID) -> Optional[Expense]:
        """Get expense by ID."""
        return self.db.query(Expense).filter(Expense.id == entity_id).first()
    
    def get_by_user_and_date_range(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> List[Expense]:
        """Get expenses by user ID and date range."""
        return self.db.query(Expense).filter(
            and_(
                Expense.user_id == user_id,
                Expense.date >= start_date,
                Expense.date < end_date
            )
        ).all()
    
    def update(self, entity: Expense) -> Expense:
        """Update an expense record."""
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, entity_id: UUID) -> bool:
        """Delete an expense record."""
        expense = self.get_by_id(entity_id)
        if expense:
            self.db.delete(expense)
            self.db.commit()
            return True
        return False
