from sqlalchemy import Column, String, Numeric, Date, ForeignKey, Index, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.models.base import Base


class Expense(Base):
    """Expense domain model."""
    
    __tablename__ = "expenses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    category = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    note = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="expenses")
    
    # Indexes
    __table_args__ = (
        Index('ix_expenses_user_date', 'user_id', 'date'),
        CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
        CheckConstraint("length(trim(category)) > 0", name="ck_expenses_category_nonempty"),
    )
