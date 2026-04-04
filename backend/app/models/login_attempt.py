from sqlalchemy import Column, String, Integer, DateTime, Index, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class LoginAttempt(Base):
    """
    Tracks failed login attempts per email for DB-backed lockout.

    One row per email address. Updated atomically via upsert so it is
    safe under concurrent requests and survives application restarts.

    Upgrade from Sprint 2: replaces the module-level _failed_attempts dict
    in auth_service.py with this persistent table.

    Production note: a scheduled job or pg_cron can periodically DELETE
    rows where last_attempt_at < NOW() - INTERVAL '1 hour' to keep the
    table small. The service also handles window expiry inline at read time.
    """

    __tablename__ = "login_attempts"

    email = Column(String(255), primary_key=True, nullable=False)
    attempt_count = Column(Integer, nullable=False, default=0)
    first_attempt_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_attempt_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    locked_until = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_login_attempts_locked_until", "locked_until"),
    )