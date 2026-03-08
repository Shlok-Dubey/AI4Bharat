"""
OAuth authentication routes for social media platforms.

This module handles OAuth flows for Meta (Facebook/Instagram).
For production deployment:
1. Set up Meta App at https://developers.facebook.com/apps/
2. Configure OAuth redirect URIs
3. Set META_APP_ID and META_APP_SECRET environment variables
4. Enable required permissions in Meta App settings
"""

import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database_sqlite import get_db
from models.user import OAuthAccount
from dependencies.auth import get_current_user
from services.meta_oauth import MetaOAuthService
from schemas.oauth import OAuthCallbackResponse, OAuthAccountResponse
from config import settings

router = APIRouter(prefix="/auth/meta", tags=["OAuth - Meta"])

# In-memory state storage for CSRF protection
# For production, use Redis or database with expiration
oauth_states = {}

@router.get("/login")
async def meta_oauth_login(
    token: str = Query(..., description="JWT token for authentication"),
    db: Session = Depends(get_db)
):
    """
    Initiate Meta OAuth flow for Instagram integration.
    
    This endpoint redirects the user to Meta's OAuth authorization page.
    User must be authenticated with JWT token passed as query parameter.
    
    Flow:
    1. Verify JWT token from query parameter
    2. Generate random state for CSRF protection
    3. Store state with user_id
    4. Redirect to Meta OAuth URL
    5. User authorizes app on Meta
    6. Meta redirects back to /auth/meta/callback
    
    Required Permissions:
    - instagram_basic: Access to Instagram account info
    - instagram_content_publish: Publish content to Instagram
    - pages_show_list: List Facebook Pages
    - pages_read_engagement: Read Page engagement data
    
    Note:
        For production, ensure META_APP_ID is configured.
        The state parameter prevents CSRF attacks.
    """
    # Verify JWT token
    from utils.security import decode_access_token
    
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state with user_id (expires in 10 minutes)
    # For production, use Redis with TTL
    oauth_states[state] = {
        "user_id": user_id,
        "provider": "meta"
    }
    
    # Get authorization URL
    auth_url = MetaOAuthService.get_authorization_url(state)
    
    # Redirect user to Meta OAuth page
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def meta_oauth_callback(
    code: str = Query(..., description="Authorization code from Meta"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback from Meta.
    
    This endpoint is called by Meta after user authorizes the app.
    It exchanges the authorization code for access tokens and stores them.
    
    Args:
        code: Authorization code from Meta
        state: State parameter to verify request authenticity
        db: Database session
        
    Returns:
        Redirect to frontend with success/error message
        
    Note:
        For production:
        - Implement proper error handling
        - Add logging for debugging
        - Handle token refresh logic
        - Validate all responses from Meta API
    """
    # Verify state parameter (CSRF protection)
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter. Please try again."
        )
    
    state_data = oauth_states.pop(state)
    user_id = state_data["user_id"]
    
    try:
        # Step 1: Exchange code for short-lived token
        token_data = await MetaOAuthService.exchange_code_for_token(code)
        if not token_data:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/oauth/error?message=Failed to exchange code for token"
            )
        
        short_lived_token = token_data["access_token"]
        
        # Step 2: Exchange for long-lived token (60 days)
        long_lived_data = await MetaOAuthService.get_long_lived_token(short_lived_token)
        if not long_lived_data:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/oauth/error?message=Failed to get long-lived token"
            )
        
        access_token = long_lived_data["access_token"]
        expires_in = long_lived_data.get("expires_in", 5184000)  # Default 60 days
        
        # Step 3: Get user info from Meta
        user_info = await MetaOAuthService.get_user_info(access_token)
        if not user_info:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/oauth/error?message=Failed to get user info"
            )
        
        provider_account_id = user_info["id"]
        
        # Step 4: Calculate token expiry
        token_expiry = MetaOAuthService.calculate_token_expiry(expires_in)
        
        # Step 5: Check if OAuth account already exists
        existing_account = db.query(OAuthAccount).filter(
            OAuthAccount.user_id == user_id,
            OAuthAccount.provider == "meta",
            OAuthAccount.provider_account_id == provider_account_id
        ).first()
        
        if existing_account:
            # Update existing account
            existing_account.access_token = access_token
            existing_account.token_expires_at = token_expiry
        else:
            # Create new OAuth account
            oauth_account = OAuthAccount(
                user_id=user_id,
                provider="meta",
                provider_account_id=provider_account_id,
                access_token=access_token,
                refresh_token=None,  # Meta uses long-lived tokens instead
                token_expires_at=token_expiry,
                scope=settings.META_SCOPES
            )
            db.add(oauth_account)
        
        db.commit()
        
        # Step 6: Get Instagram accounts (optional, for display)
        instagram_accounts = await MetaOAuthService.get_instagram_accounts(access_token)
        
        # Redirect to frontend dashboard with success parameter
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/dashboard?oauth_success=true"
        )
        
    except Exception as e:
        print(f"Error in OAuth callback: {e}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/oauth/error?message=An error occurred during authentication"
        )

@router.get("/accounts", response_model=list[OAuthAccountResponse])
async def get_user_oauth_accounts(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all OAuth accounts connected to the current user.
    
    Returns:
        List of OAuth accounts with provider information
    """
    accounts = db.query(OAuthAccount).filter(
        OAuthAccount.user_id == current_user.id
    ).all()
    
    return [OAuthAccountResponse.model_validate(acc) for acc in accounts]

@router.delete("/disconnect/{provider}")
async def disconnect_oauth_account(
    provider: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect an OAuth account.
    
    Args:
        provider: OAuth provider name (e.g., 'meta')
        
    Returns:
        Success message
    """
    account = db.query(OAuthAccount).filter(
        OAuthAccount.user_id == current_user.id,
        OAuthAccount.provider == provider
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {provider} account connected"
        )
    
    db.delete(account)
    db.commit()
    
    return {"message": f"{provider.capitalize()} account disconnected successfully"}
