"""
Instagram OAuth request/response schemas.

Pydantic models for Instagram OAuth flow and token management.

Requirements: 2.1, 2.2, 2.3, 2.6
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


class InstagramAuthUrlResponse(BaseModel):
    """Response schema for Instagram authorization URL."""
    
    authorization_url: str = Field(..., description="Instagram OAuth authorization URL")


class InstagramCallbackRequest(BaseModel):
    """Request schema for Instagram OAuth callback."""
    
    code: str = Field(..., description="Authorization code from Instagram")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")


class InstagramTokenResponse(BaseModel):
    """Response schema for Instagram token exchange."""
    
    access_token: str = Field(..., description="Instagram access token")
    user_id: int = Field(..., description="Instagram user ID")


class InstagramLongLivedTokenResponse(BaseModel):
    """Response schema for Instagram long-lived token exchange."""
    
    access_token: str = Field(..., description="Long-lived Instagram access token")
    token_type: str = Field(..., description="Token type (bearer)")
    expires_in: int = Field(..., description="Token expiry in seconds (60 days)")


class InstagramRefreshTokenResponse(BaseModel):
    """Response schema for Instagram token refresh."""
    
    access_token: str = Field(..., description="Refreshed Instagram access token")
    token_type: str = Field(..., description="Token type (bearer)")
    expires_in: int = Field(..., description="Token expiry in seconds (60 days)")


class InstagramUserProfile(BaseModel):
    """Instagram user profile data."""
    
    id: str = Field(..., description="Instagram user ID")
    username: str = Field(..., description="Instagram username")
    account_type: Optional[str] = Field(None, description="Account type (BUSINESS, CREATOR, PERSONAL)")
    media_count: Optional[int] = Field(None, description="Number of media items")


class InstagramConnectionResponse(BaseModel):
    """Response schema for successful Instagram connection."""
    
    success: bool = Field(..., description="Whether connection was successful")
    instagram_username: str = Field(..., description="Connected Instagram username")
    instagram_user_id: str = Field(..., description="Connected Instagram user ID")
    message: str = Field(..., description="Success message")


class InstagramInsights(BaseModel):
    """Instagram post insights data."""
    
    likes: int = Field(..., description="Number of likes")
    comments: int = Field(..., description="Number of comments")
    reach: int = Field(..., description="Number of unique accounts reached")
    impressions: int = Field(..., description="Total number of times the post was seen")
    engagement_rate: float = Field(..., description="Engagement rate: (likes + comments) / reach")
