from app.controllers.auth_controller import router as auth_router
from app.controllers.budget_controller import router as budget_router
from app.controllers.income_controller import router as income_router
from app.controllers.expense_controller import router as expense_router
from app.controllers.report_controller import router as report_router

__all__ = [
    "auth_router",
    "budget_router",
    "income_router",
    "expense_router",
    "report_router"
]
