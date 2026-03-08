"""
Meta (Facebook/Instagram) OAuth service.

This service handles OAuth authentication flow with Meta Graph API.
For production deployment, you need to:
1. Create a Meta App at https://developers.facebook.com/apps/
2. Add Instagram Basic Display and Instagram Graph API products
3. Configure OAuth redirect URIs in the app settings
4. Set META_APP_ID and META_APP_SECRET in environment variables
"""

import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from config import settings

class MetaOAuthService:
    """Service for Meta OAuth operations"""
    
    @staticmethod
    def get_authorization_url(state: str) -> str:
        """
        Generate Meta OAuth authorization URL.
        
        Args:
            state: Random state string for CSRF protection
            
        Returns:
            Authorization URL to redirect user to
            
        Note:
            For production, ensure META_APP_ID is set in environment variables.
            The state parameter should be stored in session/cache to verify callback.
        """
        params = {
            "client_id": settings.META_APP_ID,
            "redirect_uri": settings.META_REDIRECT_URI,
            "scope": settings.META_SCOPES,
            "response_type": "code",
            "state": state
        }
        
        # Build query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{settings.META_OAUTH_URL}?{query_string}"
    
    @staticmethod
    async def exchange_code_for_token(code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Dictionary containing access_token, token_type, expires_in
            
        Note:
            Requires META_APP_ID and META_APP_SECRET to be set.
            In production, this makes a real API call to Meta.
        """
        # For local testing without real credentials, return mock data
        if settings.META_APP_ID == "test-app-id":
            return {
                "access_token": f"mock_access_token_{code}",
                "token_type": "bearer",
                "expires_in": 5184000  # 60 days
            }
        
        # Production: Make real API call to Meta
        params = {
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "redirect_uri": settings.META_REDIRECT_URI,
            "code": code
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(settings.META_TOKEN_URL, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"Error exchanging code for token: {e}")
            return None
    
    @staticmethod
    async def get_long_lived_token(short_lived_token: str) -> Optional[Dict[str, Any]]:
        """
        Exchange short-lived token for long-lived token (60 days).
        
        Args:
            short_lived_token: Short-lived access token
            
        Returns:
            Dictionary containing access_token, token_type, expires_in
            
        Note:
            Long-lived tokens are valid for 60 days and can be refreshed.
        """
        # For local testing, return mock data
        if settings.META_APP_ID == "test-app-id":
            return {
                "access_token": f"long_lived_{short_lived_token}",
                "token_type": "bearer",
                "expires_in": 5184000  # 60 days
            }
        
        # Production: Exchange for long-lived token
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "fb_exchange_token": short_lived_token
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(settings.META_TOKEN_URL, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"Error getting long-lived token: {e}")
            return None
    
    @staticmethod
    async def get_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from Meta Graph API.
        
        Args:
            access_token: User's access token
            
        Returns:
            Dictionary containing user id, name, email
            
        Note:
            Requires valid access token from Meta OAuth flow.
        """
        # For local testing, return mock data
        if access_token.startswith("mock_") or access_token.startswith("long_lived_mock_"):
            return {
                "id": "mock_meta_user_id_12345",
                "name": "Test User",
                "email": "test@example.com"
            }
        
        # Production: Get real user info
        params = {
            "fields": "id,name,email",
            "access_token": access_token
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{settings.META_GRAPH_API_URL}/me", params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"Error getting user info: {e}")
            return None
    
    @staticmethod
    async def get_instagram_accounts(access_token: str) -> Optional[list]:
        """
        Get user's Instagram Business accounts.
        
        Args:
            access_token: User's access token
            
        Returns:
            List of Instagram Business account IDs
            
        Note:
            User must have a Facebook Page connected to an Instagram Business account.
            This requires pages_show_list and instagram_basic permissions.
        """
        # For local testing, return mock data
        if access_token.startswith("mock_") or access_token.startswith("long_lived_mock_"):
            return [{
                "id": "mock_instagram_account_id",
                "username": "test_instagram_user",
                "name": "Test Instagram Account"
            }]
        
        # Production: Get real Instagram accounts
        # First, get user's Facebook pages
        params = {
            "fields": "instagram_business_account{id,username,name}",
            "access_token": access_token
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.META_GRAPH_API_URL}/me/accounts",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract Instagram accounts from pages
                instagram_accounts = []
                for page in data.get("data", []):
                    if "instagram_business_account" in page:
                        instagram_accounts.append(page["instagram_business_account"])
                
                return instagram_accounts
        except httpx.HTTPError as e:
            print(f"Error getting Instagram accounts: {e}")
            return None
    
    @staticmethod
    def calculate_token_expiry(expires_in: int) -> datetime:
        """
        Calculate token expiry datetime.
        
        Args:
            expires_in: Seconds until token expires
            
        Returns:
            Datetime when token expires
        """
        return datetime.utcnow() + timedelta(seconds=expires_in)
