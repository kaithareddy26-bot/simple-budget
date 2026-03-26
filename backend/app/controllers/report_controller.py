from fastapi import APIRouter, Depends, Request, status, Query
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.report_schemas import MonthlySummaryResponse
from app.schemas.error_schemas import ErrorResponse
from app.schemas.auth_schemas import TokenData
from app.services.report_service import ReportService
from app.dependencies import get_report_service, get_current_user
from app.config import get_settings

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "/summary",
    response_model=MonthlySummaryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Monthly summary generated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid month format"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"description": "Too many report requests"},
    },
)
@limiter.limit(settings.REPORT_RATE_LIMIT)
async def get_monthly_summary(
    request: Request,
    month: str = Query(
        ..., description="Month in YYYY-MM format", pattern=r"^\d{4}-\d{2}$"
    ),
    current_user: TokenData = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
):
    """
    Generate monthly summary report.

    Rate limited to 10 requests per minute — tighter than the global
    60/min default because this endpoint aggregates all financial data
    for a month and is the highest-value scraping target.
    """
    summary = report_service.get_monthly_summary(
        user_id=current_user.user_id, month=month
    )

    return MonthlySummaryResponse(
        month=summary["month"],
        total_income=summary["total_income"],
        total_expenses=summary["total_expenses"],
        net_balance=summary["net_balance"],
        expenses_by_category=summary["expenses_by_category"],
        generated_at=report_service.utc_now(),
    )