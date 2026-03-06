"""
Instagram OAuth routes for local development API.

Implements Instagram OAuth flow: authorization redirect and callback handling.

Requirements: 2.1, 2.2, 2.3, 2.6
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime

from shared.schemas.instagram import (
    InstagramAuthUrlResponse,
    InstagramConnectionResponse,
)
from shared.services.instagram_service import InstagramService
from shared.services.encryption_service import encrypt_token
from shared.services.auth_middleware import get_current_user
from repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/instagram", tags=["Instagram OAuth"])


@router.get("/authorize", response_model=InstagramAuthUrlResponse)
async def get_authorization_url(current_user: str = Depends(get_current_user)):
    """
    Get Instagram OAuth authorization URL.
    
    Redirects user to Instagram to authorize the application.
    
    Steps:
    1. Validate user is authenticated
    2. Generate Instagram OAuth URL with client_id and redirect_uri
    3. Return URL for frontend to redirect user
    
    Requirements: 2.1
    """
    try:
        instagram_service = InstagramService()
        
        # Generate authorization URL with user_id as state for CSRF protection
        state = current_user
        authorization_url = instagram_service.get_authorization_url(state=state)
        
        logger.info(f"Generated Instagram authorization URL for user: {current_user}")
        
        return InstagramAuthUrlResponse(authorization_url=authorization_url)
        
    except Exception as e:
        logger.error(f"Error generating Instagram authorization URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Instagram authorization URL"
        )


@router.get("/callback", response_model=InstagramConnectionResponse)
async def handle_oauth_callback(
    code: str = Query(..., description="Authorization code from Instagram"),
    state: str = Query(None, description="State parameter for CSRF protection"),
    current_user: str = Depends(get_current_user),
):
    """
    Handle Instagram OAuth callback.
    
    Steps:
    1. Validate authorization code
    2. Exchange code for short-lived access token
    3. Exchange short-lived token for long-lived token (60 days)
    4. Fetch Instagram user profile
    5. Encrypt tokens before storing
    6. Store encrypted tokens and user metadata in database
    7. Return success response
    
    Requirements: 2.2, 2.3, 2.6
    """
    user_repo = UserRepository()
    instagram_service = InstagramService()
    
    try:
        # Validate state parameter (CSRF protection)
        if state and state != current_user:
            logger.warning(f"State mismatch in Instagram callback: expected {current_user}, got {state}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter"
            )
        
        # Step 1: Exchange authorization code for short-lived token
        logger.info(f"Exchanging Instagram authorization code for user: {current_user}")
        short_lived_token_response = await instagram_service.exchange_code_for_token(code)
        
        # Step 2: Exchange short-lived token for long-lived token (60 days)
        logger.info(f"Exchanging for long-lived Instagram token for user: {current_user}")
        long_lived_token_response = await instagram_service.exchange_for_long_lived_token(
            short_lived_token_response.access_token
        )
        
        # Step 3: Fetch Instagram user profile
        logger.info(f"Fetching Instagram user profile for user: {current_user}")
        user_profile = await instagram_service.get_user_profile(
            long_lived_token_response.access_token
        )
        
        # Step 4: Encrypt tokens before storing (Requirement 2.3)
        logger.info(f"Encrypting Instagram tokens for user: {current_user}")
        encrypted_access_token = await encrypt_token(long_lived_token_response.access_token)
        
        # Step 5: Calculate token expiry
        token_expires_at = instagram_service.calculate_token_expiry(
            long_lived_token_response.expires_in
        )
        
        # Step 6: Update user with Instagram connection data
        user = await user_repo.get_by_id(current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user with encrypted tokens and metadata (Requirement 2.6)
        user.instagram_access_token = encrypted_access_token
        user.instagram_token_expires_at = token_expires_at
        user.instagram_user_id = user_profile.id
        user.instagram_username = user_profile.username
        user.updated_at = datetime.utcnow()
        
        # Save to database
        await user_repo.update(user)
        
        logger.info(
            f"Successfully connected Instagram account for user: {current_user}, "
            f"Instagram username: {user_profile.username}"
        )
        
        return InstagramConnectionResponse(
            success=True,
            instagram_username=user_profile.username,
            instagram_user_id=user_profile.id,
            message=f"Successfully connected Instagram account @{user_profile.username}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling Instagram OAuth callback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect Instagram account: {str(e)}"
        )
