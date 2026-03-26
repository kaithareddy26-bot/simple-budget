from uuid import UUID
from typing import Optional
from collections import defaultdict
from datetime import datetime, timedelta
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.security import hash_password, verify_password, create_access_token
from app.schemas.error_schemas import ErrorCodes
from app.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# In-memory login attempt tracker
# Tracks failed login attempts per email address within a sliding window.
# Production upgrade path: replace _failed_attempts with a Redis client
# using INCR + EXPIRE for atomic, distributed, persistent tracking.
# ---------------------------------------------------------------------------
_failed_attempts: dict[str, list[datetime]] = defaultdict(list)


def _check_lockout(email: str) -> None:
    """
    Raise ValueError with AUTH_INVALID_CREDENTIALS if this email has exceeded
    the maximum failed login attempts within the lockout window.

    Uses a sliding window: only attempts within the last
    LOGIN_LOCKOUT_WINDOW_MINUTES minutes count.
    """
    now = datetime.utcnow()
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
    _failed_attempts[email].append(datetime.utcnow())


def _clear_failures(email: str) -> None:
    """Clear failed attempts on successful login."""
    _failed_attempts.pop(email, None)


def reset_attempts_for_testing(email: str) -> None:
    """
    Test-only helper to reset failed attempt state between tests.
    Do not call in production code.
    """
    _failed_attempts.pop(email, None)


class AuthService:
    """Authentication service containing business logic."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def register_user(self, email: str, password: str, full_name: str) -> User:
        """
        Register a new user.

        Business Rules:
        - Email must be unique
        - Password must be hashed before storage

        Raises:
            ValueError: If user with email already exists
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

        Security controls applied:
        1. Lockout check — raises before any DB query if email is locked
        2. Constant-time comparison via passlib (prevents timing attacks)
        3. Failed attempt recorded on any credential failure
        4. Attempt counter cleared on success

        Raises:
            ValueError: If locked out or credentials are invalid
        """
        # Step 1: Check lockout BEFORE hitting the DB
        _check_lockout(email)

        # Step 2: Fetch user
        user = self.user_repository.get_by_email(email)
        if not user:
            _record_failure(email)
            raise ValueError(
                f"{ErrorCodes.AUTH_INVALID_CREDENTIALS}:Invalid email or password"
            )

        # Step 3: Verify password (bcrypt constant-time compare)
        if not verify_password(password, user.hashed_password):
            _record_failure(email)
            raise ValueError(
                f"{ErrorCodes.AUTH_INVALID_CREDENTIALS}:Invalid email or password"
            )

        # Step 4: Success — reset counter and issue token
        _clear_failures(email)
        return create_access_token(user.id, user.email)

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return self.user_repository.get_by_id(user_id)