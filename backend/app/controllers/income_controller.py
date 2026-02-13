from fastapi import APIRouter, Depends, status
from app.schemas.income_schemas import (
    IncomeCreateRequest,
    IncomeResponse
)
from app.schemas.error_schemas import ErrorResponse
from app.schemas.auth_schemas import TokenData
from app.services.income_service import IncomeService
from app.dependencies import get_income_service, get_current_user

router = APIRouter(prefix="/incomes", tags=["Income"])


@router.post(
    "",
    response_model=IncomeResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Income successfully added"},
        400: {"model": ErrorResponse, "description": "Validation error or invalid amount"},
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)
async def add_income(
    request: IncomeCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    income_service: IncomeService = Depends(get_income_service)
):
    """
    Add a new income record.
    
    Creates an income record for the authenticated user with the
    specified amount, source, and date.
    """
    income = income_service.add_income(
        user_id=current_user.user_id,
        amount=request.amount,
        source=request.source,
        income_date=request.date
    )
    
    return IncomeResponse(
        id=income.id,
        user_id=income.user_id,
        amount=income.amount,
        source=income.source,
        date=income.date
    )
