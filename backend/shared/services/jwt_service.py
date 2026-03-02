"""
JWT token service for authentication.

This module provides JWT token generation, verification, and decoding functionality
using HS256 algorithm as specified in requirements 1.2, 1.3, and 1.4.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt


# Token expiry durations
ACCESS_TOKEN_EXPIRY_MINUTES = 60
REFRESH_TOKEN_EXPIRY_DAYS = 7


def _get_jwt_secret() -> str:
    """
    Get JWT secret from environment variable.
    
    Returns:
        JWT secret key
        
    Raises:
        ValueError: If JWT_SECRET environment variable is not set
    """
    secret = os.getenv('JWT_SECRET')
    if not secret:
        raise ValueError("JWT_SECRET environment variable is required")
    return secret


def generate_access_token(user_id: str) -> str:
    """
    Generate an access token with 60 minute expiry.
    
    Args:
        user_id: User ID to encode in the token
        
    Returns:
        JWT access token as a string
        
    Requirements: 1.2
    """
    secret = _get_jwt_secret()
    
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES)
    
    payload = {
        'user_id': user_id,
        'type': 'access',
        'iat': now,
        'exp': expiry
    }
    
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token


def generate_refresh_token(user_id: str) -> str:
    """
    Generate a refresh token with 7 days expiry.
    
    Args:
        user_id: User ID to encode in the token
        
    Returns:
        JWT refresh token as a string
        
    Requirements: 1.2
    """
    secret = _get_jwt_secret()
    
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)
    
    payload = {
        'user_id': user_id,
        'type': 'refresh',
        'iat': now,
        'exp': expiry
    }
    
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token


def verify_token(token: str, token_type: str = 'access') -> bool:
    """
    Verify a JWT token and check expiry.
    
    Args:
        token: JWT token to verify
        token_type: Expected token type ('access' or 'refresh')
        
    Returns:
        True if token is valid and not expired, False otherwise
        
    Requirements: 1.3, 1.4
    """
    try:
        secret = _get_jwt_secret()
        
        # Decode and verify token
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        
        # Check token type matches
        if payload.get('type') != token_type:
            return False
            
        return True
        
    except jwt.ExpiredSignatureError:
        # Token has expired
        return False
    except jwt.InvalidTokenError:
        # Token is invalid
        return False
    except Exception:
        # Any other error
        return False


def decode_token(token: str) -> Optional[str]:
    """
    Decode a JWT token and extract user_id.
    
    Args:
        token: JWT token to decode
        
    Returns:
        User ID if token is valid, None otherwise
        
    Requirements: 1.3, 1.4
    """
    try:
        secret = _get_jwt_secret()
        
        # Decode token
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        
        # Extract user_id
        user_id = payload.get('user_id')
        return user_id
        
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except jwt.InvalidTokenError:
        # Token is invalid
        return None
    except Exception:
        # Any other error
        return None
