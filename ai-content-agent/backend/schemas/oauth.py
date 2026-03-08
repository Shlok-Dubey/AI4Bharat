"""
Pydantic schemas for OAuth operations.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class OAuthAccountResponse(BaseModel):
    """OAuth account response schema"""
    id: uuid.UUID
    user_id: uuid.UUID
    provider: str
    provider_account_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class OAuthCallbackResponse(BaseModel):
    """OAuth callback response schema"""
    success: bool
    message: str
    redirect_url: str
    oauth_account: Optional[OAuthAccountResponse] = None

class InstagramAccountInfo(BaseModel):
    """Instagram account information"""
    instagram_business_account_id: str
    username: str
    name: Optional[str] = None
    profile_picture_url: Optional[str] = None
