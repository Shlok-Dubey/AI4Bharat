"""
Example of protected routes using authentication dependencies.
This file demonstrates how to use the authentication system.
"""

from fastapi import APIRouter, Depends
from models.user import User
from dependencies.auth import get_current_user, get_current_active_user
from schemas.auth import UserResponse

router = APIRouter(prefix="/protected", tags=["Protected Routes"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    Requires valid JWT token in Authorization header.
    
    Example:
        Authorization: Bearer <your_jwt_token>
    """
    return UserResponse.model_validate(current_user)

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get user profile (requires active user).
    This endpoint ensures the user is both authenticated and active.
    """
    return UserResponse.model_validate(current_user)
