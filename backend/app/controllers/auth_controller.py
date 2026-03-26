from fastapi import APIRouter, Depends, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.auth_schemas import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse,
)
from app.schemas.error_schemas import ErrorResponse
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service
from app.config import get_settings

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User successfully registered"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "User already exists"},
        429: {"description": "Too many registration attempts"},
    },
)
@limiter.limit(settings.REGISTER_RATE_LIMIT)
async def register(
    request: Request,
    body: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Register a new user.

    Rate limited to 3 requests per minute per IP to prevent
    registration spam and account enumeration.
    """
    user = auth_service.register_user(
        email=body.email, password=body.password, full_name=body.full_name
    )
    return UserRegisterResponse(id=user.id, email=user.email, full_name=user.full_name)


@router.post(
    "/login",
    response_model=UserLoginResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Login successful, returns JWT token"},
        401: {"model": ErrorResponse, "description": "Invalid credentials or locked out"},
        429: {"description": "Too many login attempts — back off and retry"},
    },
)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login(
    request: Request,
    body: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate user and return JWT token.

    Rate limited to 5 requests per minute per IP (network-level).
    Additionally, the service layer enforces a per-email lockout after
    5 consecutive failures within a 15-minute window (application-level).
    Both controls must be bypassed for a brute-force attack to succeed.
    """
    access_token = auth_service.login_user(
        email=body.email, password=body.password
    )
    return UserLoginResponse(access_token=access_token, token_type="bearer")