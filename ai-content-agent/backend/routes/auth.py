"""
Authentication routes for user signup and login.
"""

from fastapi import APIRouter, HTTPException, status
import dynamodb_client as db
from schemas.auth import (
    UserSignupRequest,
    UserLoginRequest,
    AuthResponse,
    UserResponse
)
from utils.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserSignupRequest):
    """
    Register a new user account.
    
    Args:
        user_data: User signup information
        
    Returns:
        JWT token and user information
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if user already exists
    existing_user = db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = db.create_user(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        business_name=user_data.business_name,
        business_type=user_data.business_type
    )
    
    # Create access token
    access_token = create_access_token(data={"sub": new_user['user_id']})
    
    # Map DynamoDB fields to UserResponse schema
    user_response = UserResponse(
        id=new_user['user_id'],
        name=new_user['name'],
        email=new_user['email'],
        business_name=new_user.get('business_name'),
        business_type=new_user.get('business_type'),
        is_active=new_user.get('is_active', True),
        is_verified=new_user.get('is_verified', False),
        created_at=new_user['created_at']
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.post("/login", response_model=AuthResponse)
def login(credentials: UserLoginRequest):
    """
    Authenticate user and return JWT token.
    
    Args:
        credentials: User login credentials
        
    Returns:
        JWT token and user information
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    user = db.get_user_by_email(credentials.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(credentials.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user['user_id']})
    
    # Map DynamoDB fields to UserResponse schema
    user_response = UserResponse(
        id=user['user_id'],
        name=user['name'],
        email=user['email'],
        business_name=user.get('business_name'),
        business_type=user.get('business_type'),
        is_active=user.get('is_active', True),
        is_verified=user.get('is_verified', False),
        created_at=user['created_at']
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

