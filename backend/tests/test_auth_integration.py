"""
Integration tests for authentication endpoints.

Tests user registration, login, token refresh, and error cases.

Requirements: 1.1, 1.2, 1.3, 1.4
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from shared.models.domain import User
from shared.services.jwt_service import generate_refresh_token


@pytest.mark.integration
class TestUserRegistration:
    """Test user registration endpoint."""
    
    @patch('dev_api.routes.auth.UserRepository')
    async def test_register_success(self, mock_repo_class, client: AsyncClient, test_user_data):
        """Test successful user registration."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        # Mock get_by_email to return None (email doesn't exist)
        mock_repo.get_by_email.return_value = None
        
        # Mock create to return a user
        created_user = User(
            user_id="test-user-id",
            email=test_user_data["email"],
            password_hash="hashed_password",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_repo.create.return_value = created_user
        
        # Make request
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Assertions
        assert response.status_code == 201
        data = response.json()
        
        assert "tokens" in data
        assert "user" in data
        
        # Check tokens
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert data["tokens"]["token_type"] == "bearer"
        
        # Check user data
        assert data["user"]["user_id"] == "test-user-id"
        assert data["user"]["email"] == test_user_data["email"]
        assert "password" not in data["user"]
        assert "password_hash" not in data["user"]
    
    @patch('dev_api.routes.auth.UserRepository')
    async def test_register_duplicate_email(self, mock_repo_class, client: AsyncClient, test_user_data):
        """Test registration with existing email."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        # Mock get_by_email to return existing user
        existing_user = User(
            user_id="existing-user-id",
            email=test_user_data["email"],
            password_hash="hashed_password",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_repo.get_by_email.return_value = existing_user
        
        # Make request
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Assertions
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "invalid-email",
            "password": "TestPass123"
        })
        
        assert response.status_code == 422  # Pydantic validation error
    
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        # Too short
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "short"
        })
        assert response.status_code == 422
        
        # No uppercase
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 422
        
        # No lowercase
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "TESTPASS123"
        })
        assert response.status_code == 422
        
        # No digit
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "TestPassword"
        })
        assert response.status_code == 422


@pytest.mark.integration
class TestUserLogin:
    """Test user login endpoint."""
    
    @patch('dev_api.routes.auth.UserRepository')
    @patch('dev_api.routes.auth.verify_password')
    async def test_login_success(self, mock_verify, mock_repo_class, client: AsyncClient, test_user_data):
        """Test successful user login."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        # Mock get_by_email to return user
        user = User(
            user_id="test-user-id",
            email=test_user_data["email"],
            password_hash="hashed_password",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_repo.get_by_email.return_value = user
        
        # Mock password verification
        mock_verify.return_value = True
        
        # Make request
        response = await client.post("/api/v1/auth/login", json=test_user_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert "tokens" in data
        assert "user" in data
        
        # Check tokens
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        
        # Check user data
        assert data["user"]["user_id"] == "test-user-id"
        assert data["user"]["email"] == test_user_data["email"]
    
    @patch('dev_api.routes.auth.UserRepository')
    async def test_login_user_not_found(self, mock_repo_class, client: AsyncClient, test_user_data):
        """Test login with non-existent email."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        # Mock get_by_email to return None
        mock_repo.get_by_email.return_value = None
        
        # Make request
        response = await client.post("/api/v1/auth/login", json=test_user_data)
        
        # Assertions
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    @patch('dev_api.routes.auth.UserRepository')
    @patch('dev_api.routes.auth.verify_password')
    async def test_login_wrong_password(self, mock_verify, mock_repo_class, client: AsyncClient, test_user_data):
        """Test login with incorrect password."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        # Mock get_by_email to return user
        user = User(
            user_id="test-user-id",
            email=test_user_data["email"],
            password_hash="hashed_password",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_repo.get_by_email.return_value = user
        
        # Mock password verification to fail
        mock_verify.return_value = False
        
        # Make request
        response = await client.post("/api/v1/auth/login", json=test_user_data)
        
        # Assertions
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()


@pytest.mark.integration
class TestTokenRefresh:
    """Test token refresh endpoint."""
    
    async def test_refresh_success(self, client: AsyncClient):
        """Test successful token refresh."""
        # Generate a valid refresh token
        user_id = "test-user-id"
        refresh_token = generate_refresh_token(user_id)
        
        # Make request
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test token refresh with invalid token."""
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid-token"
        })
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    async def test_refresh_expired_token(self, client: AsyncClient):
        """Test token refresh with expired token."""
        # Create an expired token (this would require mocking datetime)
        # For now, we'll use an invalid token format
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired.token"
        })
        
        assert response.status_code == 401


@pytest.mark.integration
class TestAuthenticationFlow:
    """Test complete authentication flow."""
    
    @patch('dev_api.routes.auth.UserRepository')
    @patch('dev_api.routes.auth.verify_password')
    async def test_complete_auth_flow(self, mock_verify, mock_repo_class, client: AsyncClient):
        """Test register -> login -> refresh flow."""
        # Setup mocks
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        # 1. Register
        mock_repo.get_by_email.return_value = None
        created_user = User(
            user_id="test-user-id",
            email="flow@example.com",
            password_hash="hashed_password",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_repo.create.return_value = created_user
        
        register_response = await client.post("/api/v1/auth/register", json={
            "email": "flow@example.com",
            "password": "FlowTest123"
        })
        assert register_response.status_code == 201
        register_data = register_response.json()
        
        # 2. Login
        mock_repo.get_by_email.return_value = created_user
        mock_verify.return_value = True
        
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "flow@example.com",
            "password": "FlowTest123"
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        
        # 3. Refresh token
        refresh_token = login_data["tokens"]["refresh_token"]
        refresh_response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        
        # Verify new access token exists (may be same if generated in same second)
        assert "access_token" in refresh_data
        assert refresh_data["access_token"]  # Not empty
