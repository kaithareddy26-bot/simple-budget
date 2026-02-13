from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.budget import Budget
from app.repositories.base_repository import BaseRepository


class BudgetRepository(BaseRepository[Budget]):
    """Budget repository implementation."""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def create(self, entity: Budget) -> Budget:
        """Create a new budget."""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def get_by_id(self, entity_id: UUID) -> Optional[Budget]:
        """Get budget by ID."""
        return self.db.query(Budget).filter(Budget.id == entity_id).first()
    
    def get_by_user_and_month(self, user_id: UUID, month: str) -> Optional[Budget]:
        """Get budget by user ID and month."""
        return self.db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.month == month
        ).first()
    
    def update(self, entity: Budget) -> Budget:
        """Update a budget."""
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, entity_id: UUID) -> bool:
        """Delete a budget."""
        budget = self.get_by_id(entity_id)
        if budget:
            self.db.delete(budget)
            self.db.commit()
            return True
        return False
