from fastapi import APIRouter, Depends, status
from uuid import UUID
from app.schemas.budget_schemas import (
    BudgetCreateRequest,
    BudgetUpdateRequest,
    BudgetResponse
)
from app.schemas.error_schemas import ErrorResponse
from app.schemas.auth_schemas import TokenData
from app.services.budget_service import BudgetService
from app.dependencies import get_budget_service, get_current_user

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.post(
    "",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Budget successfully created"},
        400: {"model": ErrorResponse, "description": "Validation error or invalid amount"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ErrorResponse, "description": "Budget already exists for this month"}
    }
)
async def create_budget(
    request: BudgetCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Create a new monthly budget.
    
    Creates a budget for the specified month. Only one budget
    per user per month is allowed.
    """
    budget = budget_service.create_budget(
        user_id=current_user.user_id,
        month=request.month,
        amount=request.amount
    )
    
    return budget


@router.get(
    "/current-month",
    response_model=BudgetResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Budget retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Access forbidden"},
        404: {"model": ErrorResponse, "description": "Budget not found"}
    }
)
async def get_current_month_budget(
    current_user: TokenData = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Retrieve the current month's budget for the authenticated user.
    
    
    Returns the budget details. Users can only access their own budgets.
    """
    budget = budget_service.get_current_month_budget(
        user_id=current_user.user_id
    )
    
    return budget


@router.get(
    "/{budgetId}",
    response_model=BudgetResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Budget retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Access forbidden"},
        404: {"model": ErrorResponse, "description": "Budget not found"}
    }
)
async def get_budget(
    budgetId: UUID,
    current_user: TokenData = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Retrieve a budget by ID.
    
    Returns the budget details. Users can only access their own budgets.
    """
    budget = budget_service.get_budget_by_id(
        budget_id=budgetId,
        user_id=current_user.user_id
    )
    
    return budget


@router.put(
    "/{budgetId}",
    response_model=BudgetResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Budget updated successfully"},
        400: {"model": ErrorResponse, "description": "Validation error or invalid amount"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Access forbidden"},
        404: {"model": ErrorResponse, "description": "Budget not found"}
    }
)
async def update_budget(
    budgetId: UUID,
    request: BudgetUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Update a budget amount.
    
    Updates the amount for an existing budget. Users can only
    update their own budgets.
    """
    budget = budget_service.update_budget_amount(
        budget_id=budgetId,
        user_id=current_user.user_id,
        new_amount=request.amount
    )
    
    return budget
