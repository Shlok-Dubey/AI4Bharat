"""
Authentication middleware for FastAPI.

This module provides authentication dependency for FastAPI endpoints
to extract and validate JWT tokens from Authorization headers.

Requirements: 1.3, 1.4
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt_service import decode_token, verify_token


# HTTP Bearer security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    FastAPI dependency to extract and validate JWT token from Authorization header.
    
    This dependency:
    1. Extracts JWT from Authorization header (Bearer token)
    2. Validates the token
    3. Returns the user_id
    4. Raises 401 error for invalid/expired tokens
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        User ID extracted from valid token
        
    Raises:
        HTTPException: 401 Unauthorized if token is invalid or expired
        
    Requirements: 1.3, 1.4
    
    Usage:
        @app.get("/api/v1/protected")
        async def protected_route(user_id: str = Depends(get_current_user)):
            return {"user_id": user_id}
    """
    token = credentials.credentials
    
    # Verify token is valid and not expired
    if not verify_token(token, token_type='access'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token to extract user_id
    user_id = decode_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    """
    Optional authentication dependency that doesn't raise error if no token provided.
    
    Args:
        credentials: Optional HTTP Bearer credentials
        
    Returns:
        User ID if valid token provided, None otherwise
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # Verify and decode token
    if verify_token(token, token_type='access'):
        return decode_token(token)
    
    return None
