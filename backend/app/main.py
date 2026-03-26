from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.models import init_db
from app.controllers import (
    auth_router,
    budget_router,
    income_router,
    expense_router,
    report_router,
)
from app.middleware.error_handler import (
    validation_exception_handler,
    value_error_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
    general_exception_handler,
    http_exception_handler,
)

settings = get_settings()

# ---------------------------------------------------------------------------
# Rate limiter — uses client IP by default.
# default_limits applies to every route that doesn't have its own @limiter.limit
# Production upgrade: swap memory:// for redis://localhost:6379 in .env
# ---------------------------------------------------------------------------
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.GLOBAL_RATE_LIMIT],
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Cross-Platform Budgeting Application API",
)

# Attach limiter to app state so route decorators can reach it
app.state.limiter = limiter

# SlowAPI middleware must be added BEFORE other middleware
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],       # only what the API uses
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=[],
)

# Exception handlers
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(budget_router, prefix=settings.API_V1_PREFIX)
app.include_router(income_router, prefix=settings.API_V1_PREFIX)
app.include_router(expense_router, prefix=settings.API_V1_PREFIX)
app.include_router(report_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    init_db()


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Budgeting Application API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }