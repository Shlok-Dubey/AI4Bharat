"""
Authentication dependencies for FastAPI routes.
"""

from typing import Optional, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import dynamodb_client as db
from utils.security import decode_access_token

# HTTP Bearer token scheme
security = HTTPBearer()


class UserDict(dict):
    """
    Dictionary that also supports attribute access for backward compatibility.
    Allows both user['user_id'] and user.id syntax.
    """
    def __getattr__(self, key):
        # Map 'id' to 'user_id' for backward compatibility
        if key == 'id':
            return self.get('user_id')
        return self.get(key)
    
    def __setattr__(self, key, value):
        self[key] = value


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserDict:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        Current authenticated user dict with attribute access support
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode token
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    # Extract user ID from token
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Get user from DynamoDB
    user = db.get_user(user_id)
    
    if user is None:
        raise credentials_exception
    
    if not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Return UserDict for backward compatibility
    return UserDict(user)


async def get_current_active_user(
    current_user: UserDict = Depends(get_current_user)
) -> UserDict:
    """
    Dependency to ensure the current user is active.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

