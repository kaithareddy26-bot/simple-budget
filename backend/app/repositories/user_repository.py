from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository implementation."""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def create(self, entity: User) -> User:
        """Create a new user."""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def get_by_id(self, entity_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == entity_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def update(self, entity: User) -> User:
        """Update a user."""
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, entity_id: UUID) -> bool:
        """Delete a user."""
        user = self.get_by_id(entity_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False
