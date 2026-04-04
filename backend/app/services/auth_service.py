from uuid import UUID
from typing import Optional
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.login_attempt_repository import LoginAttemptRepository
from app.utils.security import hash_password, verify_password, create_access_token
from app.schemas.error_schemas import ErrorCodes
from app.config import get_settings

settings = get_settings()


class AuthService:
    """
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=settings.LOGIN_LOCKOUT_WINDOW_MINUTES)

    # Prune attempts outside the current window
    _failed_attempts[email] = [
        t for t in _failed_attempts[email] if t > window_start
    ]

    if len(_failed_attempts[email]) >= settings.LOGIN_LOCKOUT_MAX_ATTEMPTS:
        raise ValueError(
            f"{ErrorCodes.AUTH_INVALID_CREDENTIALS}:Too many failed login attempts. "
            f"Try again in {settings.LOGIN_LOCKOUT_WINDOW_MINUTES} minutes."
        )


def _record_failure(email: str) -> None:
    """Record a failed login attempt for this email."""
    _failed_attempts[email].append(datetime.now(timezone.utc))

    The public interface is identical to Sprint 2 — callers do not need
    to change.  Only __init__ gains a second argument.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        login_attempt_repository: LoginAttemptRepository,
    ):
        self.user_repository = user_repository
        self.login_attempt_repo = login_attempt_repository

    def register_user(self, email: str, password: str, full_name: str) -> User:
        """
        Register a new user.

        Raises:
            ValueError: If a user with this email already exists.
        """
        existing_user = self.user_repository.get_by_email(email)
        if existing_user:
            raise ValueError(
                f"{ErrorCodes.USER_EXISTS}:User with this email already exists"
            )
        hashed_password = hash_password(password)
        user = User(email=email, hashed_password=hashed_password, full_name=full_name)
        return self.user_repository.create(user)

    def login_user(self, email: str, password: str) -> str:
        """
        Authenticate user and return JWT token.

        Security flow (unchanged from Sprint 2):
        1. DB lockout check — rejects before any credential work
        2. Fetch user — records failure and raises if not found
        3. Verify password — records failure and raises if wrong
        4. Success — clears lockout record, issues JWT

        After recording each failure the service checks whether the
        threshold has been crossed and sets locked_until if so.

        Raises:
            ValueError: AUTH_INVALID_CREDENTIALS on lockout or bad creds.
        """
        # Step 1 — DB-backed lockout check
        if self.login_attempt_repo.is_locked(email):
            raise ValueError(
                f"{ErrorCodes.AUTH_INVALID_CREDENTIALS}:"
                f"Too many failed login attempts. "
                f"Try again in {settings.LOGIN_LOCKOUT_WINDOW_MINUTES} minutes."
            )

        # Step 2 — Fetch user
        user = self.user_repository.get_by_email(email)
        if not user:
            self._record_and_maybe_lock(email)
            raise ValueError(
                f"{ErrorCodes.AUTH_INVALID_CREDENTIALS}:Invalid email or password"
            )

        # Step 3 — Verify password (bcrypt constant-time compare)
        if not verify_password(password, user.hashed_password):
            self._record_and_maybe_lock(email)
            raise ValueError(
                f"{ErrorCodes.AUTH_INVALID_CREDENTIALS}:Invalid email or password"
            )

        # Step 4 — Success
        self.login_attempt_repo.clear(email)
        return create_access_token(user.id, user.email)

    def _record_and_maybe_lock(self, email: str) -> None:
        """Record a failure; set locked_until if the threshold is now met."""
        attempt = self.login_attempt_repo.record_failure(
            email, settings.LOGIN_LOCKOUT_WINDOW_MINUTES
        )
        if attempt and attempt.attempt_count >= settings.LOGIN_LOCKOUT_MAX_ATTEMPTS:
            locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=settings.LOGIN_LOCKOUT_WINDOW_MINUTES
            )
            self.login_attempt_repo.set_locked(email, locked_until)

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return self.user_repository.get_by_id(user_id)