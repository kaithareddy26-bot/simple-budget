from fastapi import APIRouter, Depends, status, Query
from app.schemas.report_schemas import MonthlySummaryResponse
from app.schemas.error_schemas import ErrorResponse
from app.schemas.auth_schemas import TokenData
from app.services.report_service import ReportService
from app.dependencies import get_report_service, get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "/summary",
    response_model=MonthlySummaryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Monthly summary generated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid month format"},
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)
async def get_monthly_summary(
    month: str = Query(..., description="Month in YYYY-MM format", regex=r"^\d{4}-\d{2}$"),
    current_user: TokenData = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Generate monthly summary report.
    
    Returns aggregated financial data for the specified month including:
    - Total income
    - Total expenses
    - Net balance
    - Expenses grouped by category
    """
    summary = report_service.get_monthly_summary(
        user_id=current_user.user_id,
        month=month
    )
    
    return MonthlySummaryResponse(
        month=summary["month"],
        total_income=summary["total_income"],
        total_expenses=summary["total_expenses"],
        net_balance=summary["net_balance"],
        expenses_by_category=summary["expenses_by_category"]
    )
