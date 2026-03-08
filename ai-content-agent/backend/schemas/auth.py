"""
Pydantic schemas for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid

class UserSignupRequest(BaseModel):
    """User signup request schema"""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    business_name: Optional[str] = Field(None, max_length=255)
    business_type: Optional[str] = Field(None, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "password": "SecurePass123!",
                "business_name": "Acme Corp",
                "business_type": "Technology"
            }
        }

class UserLoginRequest(BaseModel):
    """User login request schema"""
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "SecurePass123!"
            }
        }

class TokenResponse(BaseModel):
    """JWT token response schema"""
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    """User response schema"""
    id: uuid.UUID
    name: str
    email: str
    business_name: Optional[str]
    business_type: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    """Authentication response with token and user data"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
