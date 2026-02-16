import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from app.services.auth_service import AuthService
from app.models.user import User
from app.schemas.error_schemas import ErrorCodes


class TestAuthService:
    """Unit tests for AuthService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repo = Mock()
        self.service = AuthService(self.mock_repo)
    
    def test_register_user_success(self):
        """Test successful user registration."""
        # Arrange
        self.mock_repo.get_by_email.return_value = None
        self.mock_repo.create.return_value = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed",
            full_name="Kaitha Reddy"
        )
        
        # Act
        user = self.service.register_user(
            email="test@example.com",
            password="password123",
            full_name="Kaitha Reddy"
        )
        
        # Assert
        assert user.email == "test@example.com"
        assert user.full_name == "Kaitha Reddy"
        self.mock_repo.get_by_email.assert_called_once_with("test@example.com")
        self.mock_repo.create.assert_called_once()
    
    def test_register_user_duplicate_email(self):
        """Test registration with existing email."""
        # Arrange
        self.mock_repo.get_by_email.return_value = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed",
            full_name="Existing User"
        )
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.register_user(
                email="test@example.com",
                password="password123",
                full_name="Kaitha Reddy"
            )
        
        assert ErrorCodes.USER_EXISTS in str(exc_info.value)
    
    def test_login_user_success(self):
        user_id = uuid4()
        self.mock_repo.get_by_email.return_value = User(
            id=user_id,
            email="test@example.com",
            hashed_password="does-not-matter",
            full_name="Kaitha Reddy"
        )

        with patch("app.services.auth_service.verify_password", return_value=True), \
            patch("app.services.auth_service.create_access_token", return_value="fake.jwt.token"):
            token = self.service.login_user(email="test@example.com", password="password123")

        assert token == "fake.jwt.token"
        self.mock_repo.get_by_email.assert_called_once_with("test@example.com")

    def test_login_user_invalid_password(self):
        self.mock_repo.get_by_email.return_value = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed",
            full_name="Kaitha Reddy"
        )

        with patch("app.services.auth_service.verify_password", return_value=False):
            with pytest.raises(ValueError) as exc_info:
                self.service.login_user(email="test@example.com", password="wrong")

        assert ErrorCodes.AUTH_INVALID_CREDENTIALS in str(exc_info.value)
    
    def test_login_user_invalid_email(self):
        """Test login with non-existent email."""
        # Arrange
        self.mock_repo.get_by_email.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.login_user(
                email="nonexistent@example.com",
                password="password123"
            )
        
        assert ErrorCodes.AUTH_INVALID_CREDENTIALS in str(exc_info.value)
    
    def test_get_user_by_id(self):
        """Test getting user by ID."""
        # Arrange
        user_id = uuid4()
        expected_user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Kaitha Reddy"
        )
        self.mock_repo.get_by_id.return_value = expected_user
        
        # Act
        user = self.service.get_user_by_id(user_id)
        
        # Assert
        assert user == expected_user
        self.mock_repo.get_by_id.assert_called_once_with(user_id)
