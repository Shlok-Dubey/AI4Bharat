"""
Authentication request/response schemas.

Pydantic models for user registration, login, and token management.

Requirements: 10.3
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional


class UserRegisterRequest(BaseModel):
    """Request schema for user registration."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password (8-128 characters)")
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength.
        
        Requirements:
        - At least 8 characters
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one digit
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        
        return v


class UserLoginRequest(BaseModel):
    """Request schema for user login."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""
    
    access_token: str = Field(..., description="JWT access token (60 min expiry)")
    refresh_token: str = Field(..., description="JWT refresh token (7 days expiry)")
    token_type: str = Field(default="bearer", description="Token type")


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""
    
    refresh_token: str = Field(..., description="JWT refresh token")


class AccessTokenResponse(BaseModel):
    """Response schema for refreshed access token."""
    
    access_token: str = Field(..., description="New JWT access token (60 min expiry)")
    token_type: str = Field(default="bearer", description="Token type")


class UserResponse(BaseModel):
    """Response schema for user details (no sensitive data)."""
    
    user_id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    created_at: str = Field(..., description="Account creation timestamp (ISO format)")
    timezone: str = Field(default="UTC", description="User timezone")
    daily_campaign_quota: int = Field(default=50, description="Daily campaign generation quota")
    campaigns_generated_today: int = Field(default=0, description="Campaigns generated today")
    
    # Instagram connection status
    instagram_connected: bool = Field(default=False, description="Whether Instagram is connected")
    instagram_username: Optional[str] = Field(None, description="Instagram username if connected")
