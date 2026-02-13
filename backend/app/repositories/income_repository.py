from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.income import Income
from app.repositories.base_repository import BaseRepository


class IncomeRepository(BaseRepository[Income]):
    """Income repository implementation."""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def create(self, entity: Income) -> Income:
        """Create a new income record."""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def get_by_id(self, entity_id: UUID) -> Optional[Income]:
        """Get income by ID."""
        return self.db.query(Income).filter(Income.id == entity_id).first()
    
    def get_by_user_and_date_range(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> List[Income]:
        """Get incomes by user ID and date range."""
        return self.db.query(Income).filter(
            and_(
                Income.user_id == user_id,
                Income.date >= start_date,
                Income.date < end_date
            )
        ).all()
    
    def update(self, entity: Income) -> Income:
        """Update an income record."""
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, entity_id: UUID) -> bool:
        """Delete an income record."""
        income = self.get_by_id(entity_id)
        if income:
            self.db.delete(income)
            self.db.commit()
            return True
        return False
