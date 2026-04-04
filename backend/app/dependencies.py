from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.base import get_db
from app.repositories import (
    UserRepository,
    BudgetRepository,
    IncomeRepository,
    ExpenseRepository,
    LoginAttemptRepository,
)
from app.services import (
    BudgetService,
    IncomeService,
    ExpenseService,
    ReportService,
)
from app.services.auth_service import AuthService
from app.utils.security import decode_access_token
from app.schemas.auth_schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Repository dependencies ──────────────────────────────────────────────────

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_budget_repository(db: Session = Depends(get_db)) -> BudgetRepository:
    return BudgetRepository(db)

def get_income_repository(db: Session = Depends(get_db)) -> IncomeRepository:
    return IncomeRepository(db)

def get_expense_repository(db: Session = Depends(get_db)) -> ExpenseRepository:
    return ExpenseRepository(db)

def get_login_attempt_repository(
    db: Session = Depends(get_db),
) -> LoginAttemptRepository:
    """Provides the DB-backed lockout repository (Sprint 3)."""
    return LoginAttemptRepository(db)


# ── Service dependencies ─────────────────────────────────────────────────────

def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
    login_attempt_repository: LoginAttemptRepository = Depends(
        get_login_attempt_repository
    ),
) -> AuthService:
    """AuthService now receives LoginAttemptRepository for DB-backed lockout."""
    return AuthService(user_repository, login_attempt_repository)

def get_budget_service(
    budget_repository: BudgetRepository = Depends(get_budget_repository),
) -> BudgetService:
    return BudgetService(budget_repository)

def get_income_service(
    income_repository: IncomeRepository = Depends(get_income_repository),
) -> IncomeService:
    return IncomeService(income_repository)

def get_expense_service(
    expense_repository: ExpenseRepository = Depends(get_expense_repository),
) -> ExpenseService:
    return ExpenseService(expense_repository)

def get_report_service(
    income_repository: IncomeRepository = Depends(get_income_repository),
    expense_repository: ExpenseRepository = Depends(get_expense_repository),
) -> ReportService:
    return ReportService(income_repository, expense_repository)


# ── Auth dependency ──────────────────────────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenData:
    """
    Validate JWT token and return current user data.

    Raises:
        HTTPException: If token is invalid or expired.
    """
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(payload.get("sub"))
        email = payload.get("email")

        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = auth_service.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(user_id=user_id, email=email)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )