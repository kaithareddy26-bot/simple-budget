from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.login_attempt import LoginAttempt


class LoginAttemptRepository:
    """
    All DB operations for login attempt / lockout tracking.

    The core write operation uses PostgreSQL's INSERT ... ON CONFLICT
    (upsert) so it is atomic — no race condition between check and
    increment even under concurrent requests from the same email.
    """

    def __init__(self, db: Session):
        self.db = db

    def get(self, email: str) -> LoginAttempt | None:
        """Fetch the attempt row for this email, or None if no failures yet."""
        return (
            self.db.query(LoginAttempt)
            .filter(LoginAttempt.email == email)
            .first()
        )

    def record_failure(self, email: str, window_minutes: int) -> LoginAttempt:
        """
        Atomically increment the failure counter for this email.

        If the existing row's first_attempt_at is outside the current window,
        the counter is reset to 1 (sliding window behaviour matches Sprint 2).
        Returns the updated row so the caller can decide whether to lock.
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)

        self.db.execute(
            text("""
                INSERT INTO login_attempts
                    (email, attempt_count, first_attempt_at, last_attempt_at)
                VALUES
                    (:email, 1, :now, :now)
                ON CONFLICT (email) DO UPDATE SET
                    attempt_count = CASE
                        WHEN login_attempts.first_attempt_at < :window_start
                            THEN 1
                        ELSE login_attempts.attempt_count + 1
                    END,
                    first_attempt_at = CASE
                        WHEN login_attempts.first_attempt_at < :window_start
                            THEN :now
                        ELSE login_attempts.first_attempt_at
                    END,
                    last_attempt_at = :now
            """),
            {"email": email, "now": now, "window_start": window_start},
        )
        self.db.commit()
        return self.get(email)

    def set_locked(self, email: str, until: datetime) -> None:
        """Set locked_until on the row — called once threshold is crossed."""
        attempt = self.get(email)
        if attempt:
            attempt.locked_until = until
            self.db.commit()

    def clear(self, email: str) -> None:
        """Delete the row on successful login — resets all counters."""
        self.db.query(LoginAttempt).filter(
            LoginAttempt.email == email
        ).delete()
        self.db.commit()

    def is_locked(self, email: str) -> bool:
        """
        Return True if this email is currently within a lockout window.
        Compares locked_until (stored in UTC) against UTC now.
        """
        attempt = self.get(email)
        if not attempt or not attempt.locked_until:
            return False
        locked_until_utc = attempt.locked_until
        if locked_until_utc.tzinfo is None:
            locked_until_utc = locked_until_utc.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < locked_until_utc