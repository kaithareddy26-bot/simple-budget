from fastapi import APIRouter, Depends, status
from typing import List
from app.schemas.expense_schemas import (
    ExpenseCreateRequest,
    ExpenseResponse
)
from app.schemas.error_schemas import ErrorResponse
from app.schemas.auth_schemas import TokenData
from app.services.expense_service import ExpenseService
from app.dependencies import get_expense_service, get_current_user

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Expense successfully added"},
        400: {"model": ErrorResponse, "description": "Validation error or invalid amount"},
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)
async def add_expense(
    request: ExpenseCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    expense_service: ExpenseService = Depends(get_expense_service)
):
    """
    Add a new expense record.
    
    Creates an expense record for the authenticated user with the
    specified amount, category, date, and optional note.
    """
    expense = expense_service.add_expense(
        user_id=current_user.user_id,
        amount=request.amount,
        category=request.category,
        expense_date=request.date,
        note=request.note
    )
    
    return expense

@router.get(
    "/current-month",
    response_model=List[ExpenseResponse],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Expenses retrieved successfully"},
        400: {"model": ErrorResponse, "description": "Validation error or invalid amount"},
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)
async def get_current_month_expenses(
    current_user: TokenData = Depends(get_current_user),
    expense_service: ExpenseService = Depends(get_expense_service)
):
    """
    Retrieve current month's expenses for the authenticated user.
    
    Returns a list of expense records for the current month.
    """

    expenses = expense_service.get_current_month_expenses(user_id=current_user.user_id)

    return expenses

