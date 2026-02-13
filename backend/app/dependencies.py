from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.base import get_db
from app.repositories import (
    UserRepository,
    BudgetRepository,
    IncomeRepository,
    ExpenseRepository
)
from app.services import (
    AuthService,
    BudgetService,
    IncomeService,
    ExpenseService,
    ReportService
)
from app.utils.security import decode_access_token
from app.schemas.auth_schemas import TokenData
from app.schemas.error_schemas import ErrorCodes, ErrorDetail, ErrorResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Repository Dependencies
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Get user repository instance."""
    return UserRepository(db)


def get_budget_repository(db: Session = Depends(get_db)) -> BudgetRepository:
    """Get budget repository instance."""
    return BudgetRepository(db)


def get_income_repository(db: Session = Depends(get_db)) -> IncomeRepository:
    """Get income repository instance."""
    return IncomeRepository(db)


def get_expense_repository(db: Session = Depends(get_db)) -> ExpenseRepository:
    """Get expense repository instance."""
    return ExpenseRepository(db)


# Service Dependencies
def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository)
) -> AuthService:
    """Get auth service instance."""
    return AuthService(user_repository)


def get_budget_service(
    budget_repository: BudgetRepository = Depends(get_budget_repository)
) -> BudgetService:
    """Get budget service instance."""
    return BudgetService(budget_repository)


def get_income_service(
    income_repository: IncomeRepository = Depends(get_income_repository)
) -> IncomeService:
    """Get income service instance."""
    return IncomeService(income_repository)


def get_expense_service(
    expense_repository: ExpenseRepository = Depends(get_expense_repository)
) -> ExpenseService:
    """Get expense service instance."""
    return ExpenseService(expense_repository)


def get_report_service(
    income_repository: IncomeRepository = Depends(get_income_repository),
    expense_repository: ExpenseRepository = Depends(get_expense_repository)
) -> ReportService:
    """Get report service instance."""
    return ReportService(income_repository, expense_repository)


# Authentication Dependency
def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenData:
    """
    Validate JWT token and return current user data.
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCodes.AUTH_INVALID_TOKEN,
                    message="Invalid or expired token"
                )
            ).model_dump(),
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        user_id = UUID(payload.get("sub"))
        email = payload.get("email")
        
        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        code=ErrorCodes.AUTH_INVALID_TOKEN,
                        message="Invalid token payload"
                    )
                ).model_dump(),
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify user still exists
        user = auth_service.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        code=ErrorCodes.AUTH_INVALID_TOKEN,
                        message="User not found"
                    )
                ).model_dump(),
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return TokenData(user_id=user_id, email=email)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCodes.AUTH_INVALID_TOKEN,
                    message="Invalid token format"
                )
            ).model_dump(),
            headers={"WWW-Authenticate": "Bearer"}
        )
