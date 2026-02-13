from uuid import UUID
from typing import Optional
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.security import hash_password, verify_password, create_access_token
from app.schemas.error_schemas import ErrorCodes


class AuthService:
    """Authentication service containing business logic."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def register_user(self, email: str, password: str, full_name: str) -> User:
        """
        Register a new user.
        
        Business Rules:
        - Email must be unique
        - Password must be hashed before storage
        
        Raises:
            ValueError: If user with email already exists
        """
        # Check if user already exists
        existing_user = self.user_repository.get_by_email(email)
        if existing_user:
            raise ValueError(f"{ErrorCodes.AUTH_USER_EXISTS}:User with this email already exists")
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Create user entity
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name
        )
        
        # Persist user
        return self.user_repository.create(user)
    
    def login_user(self, email: str, password: str) -> str:
        """
        Authenticate user and return JWT token.
        
        Business Rules:
        - Email and password must match
        - Return JWT token on success
        
        Raises:
            ValueError: If credentials are invalid
        """
        # Get user by email
        user = self.user_repository.get_by_email(email)
        if not user:
            raise ValueError(f"{ErrorCodes.AUTH_INVALID_CREDENTIALS}:Invalid email or password")
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise ValueError(f"{ErrorCodes.AUTH_INVALID_CREDENTIALS}:Invalid email or password")
        
        # Create access token
        access_token = create_access_token(user.id, user.email)
        
        return access_token
    
    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return self.user_repository.get_by_id(user_id)
