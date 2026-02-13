from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository interface."""
    
    def __init__(self, db: Session):
        self.db = db
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an entity."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: UUID) -> bool:
        """Delete an entity."""
        pass
