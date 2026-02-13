from fastapi import APIRouter, Depends, status
from app.schemas.auth_schemas import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse
)
from app.schemas.error_schemas import ErrorResponse
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User successfully registered"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "User already exists"}
    }
)
async def register(
    request: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user.
    
    Creates a new user account with the provided credentials.
    Password will be securely hashed before storage.
    """
    user = auth_service.register_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )
    
    return UserRegisterResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name
    )


@router.post(
    "/login",
    response_model=UserLoginResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Login successful, returns JWT token"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"}
    }
)
async def login(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and return JWT token.
    
    Validates credentials and returns a JWT access token
    that must be included in subsequent requests.
    """
    access_token = auth_service.login_user(
        email=request.email,
        password=request.password
    )
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer"
    )
