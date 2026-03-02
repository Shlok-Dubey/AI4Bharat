"""
Authentication routes for local development API.

Implements user registration, login, and token refresh endpoints.

Requirements: 1.1, 1.2
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime

from shared.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    AccessTokenResponse,
    UserResponse,
)
from shared.models.domain import User
from shared.services.password_service import hash_password, verify_password
from shared.services.jwt_service import (
    generate_access_token,
    generate_refresh_token,
    verify_token,
    decode_token,
)
from repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def _user_to_response(user: User) -> UserResponse:
    """Convert User domain model to UserResponse schema."""
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        created_at=user.created_at.isoformat(),
        timezone=user.timezone,
        daily_campaign_quota=user.daily_campaign_quota,
        campaigns_generated_today=user.campaigns_generated_today,
        instagram_connected=user.instagram_access_token is not None,
        instagram_username=user.instagram_username,
    )


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest):
    """
    Register a new user.
    
    Steps:
    1. Validate input with Pydantic
    2. Check if email already exists
    3. Hash password and create user in database
    4. Generate JWT tokens
    5. Return tokens and user data
    
    Requirements: 1.1, 1.2
    """
    user_repo = UserRepository()
    
    # Check if email already exists
    existing_user = await user_repo.get_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        # Hash password
        password_hash = hash_password(request.password)
        
        # Create user
        user = User(
            email=request.email,
            password_hash=password_hash,
        )
        
        # Save to database
        created_user = await user_repo.create(user)
        
        # Generate tokens
        access_token = generate_access_token(created_user.user_id)
        refresh_token = generate_refresh_token(created_user.user_id)
        
        logger.info(f"User registered successfully: {created_user.user_id}")
        
        return {
            "tokens": TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
            ).model_dump(),
            "user": _user_to_response(created_user).model_dump(),
        }
        
    except ValueError as e:
        # Validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=dict)
async def login(request: UserLoginRequest):
    """
    Login user with email and password.
    
    Steps:
    1. Validate credentials
    2. Verify password with bcrypt
    3. Generate JWT tokens
    4. Return tokens and user data
    
    Requirements: 1.2
    """
    user_repo = UserRepository()
    
    try:
        # Get user by email
        user = await user_repo.get_by_email(request.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate tokens
        access_token = generate_access_token(user.user_id)
        refresh_token = generate_refresh_token(user.user_id)
        
        logger.info(f"User logged in successfully: {user.user_id}")
        
        return {
            "tokens": TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
            ).model_dump(),
            "user": _user_to_response(user).model_dump(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    
    Steps:
    1. Validate refresh token
    2. Generate new access token
    3. Return new access token
    
    Requirements: 1.2
    """
    try:
        # Verify refresh token
        if not verify_token(request.refresh_token, token_type='refresh'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Decode token to get user_id
        user_id = decode_token(request.refresh_token)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload"
            )
        
        # Generate new access token
        access_token = generate_access_token(user_id)
        
        logger.info(f"Access token refreshed for user: {user_id}")
        
        return AccessTokenResponse(access_token=access_token)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )
