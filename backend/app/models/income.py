from sqlalchemy import Column, String, Numeric, Date, ForeignKey, Index, CheckConstraint, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.models.base import Base


class Income(Base):
    """Income domain model."""
    
    __tablename__ = "incomes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    source = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="incomes")
    
    # Indexes
    __table_args__ = (
        Index('ix_incomes_user_date', 'user_id', 'date'),
        CheckConstraint("amount > 0", name="ck_incomes_amount_positive"),
        CheckConstraint("length(trim(source)) > 0", name="ck_incomes_source_nonempty"),
    )
