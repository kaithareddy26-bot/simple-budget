from sqlalchemy import Column, String, Numeric, ForeignKey, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.models.base import Base


class Budget(Base):
    """Budget domain model."""
    
    __tablename__ = "budgets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    month = Column(String(7), nullable=False)  # Format: YYYY-MM
    amount = Column(Numeric(12, 2), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="budgets")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'month', name='uq_user_month'),
        Index('ix_budgets_user_month', 'user_id', 'month'),
        CheckConstraint("amount > 0", name="ck_budgets_amount_positive"),
        CheckConstraint("month ~ '^[0-9]{4}-[0-9]{2}$'", name="ck_budgets_month_format"),
    )
