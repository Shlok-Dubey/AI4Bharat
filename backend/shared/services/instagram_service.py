"""
Instagram OAuth and API service.

Handles Instagram Graph API v18.0 OAuth flow, token management, and content publishing.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.6, 7.1, 7.2, 7.3, 7.4, 18.1, 18.3, 19.1, 19.2, 30.1
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from urllib.parse import urlencode
import asyncio

from shared.schemas.instagram import (
    InstagramTokenResponse,
    InstagramLongLivedTokenResponse,
    InstagramRefreshTokenResponse,
    InstagramUserProfile,
    InstagramInsights,
)

logger = logging.getLogger(__name__)


class InstagramService:
    """Service for Instagram OAuth and API operations."""
    
    # Instagram Graph API endpoints
    OAUTH_AUTHORIZE_URL = "https://api.instagram.com/oauth/authorize"
    OAUTH_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
    GRAPH_API_BASE = "https://graph.instagram.com"
    
    def __init__(self):
        """Initialize Instagram service with OAuth credentials from environment."""
        self.client_id = os.getenv('INSTAGRAM_CLIENT_ID')
        self.client_secret = os.getenv('INSTAGRAM_CLIENT_SECRET')
        self.redirect_uri = os.getenv('INSTAGRAM_REDIRECT_URI')
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.warning(
                "Instagram OAuth credentials not fully configured. "
                "Set INSTAGRAM_CLIENT_ID, INSTAGRAM_CLIENT_SECRET, and INSTAGRAM_REDIRECT_URI."
            )
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate Instagram OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            str: Authorization URL to redirect user to
            
        Requirements: 2.1
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'user_profile,user_media',
            'response_type': 'code',
        }
        
        if state:
            params['state'] = state
        
        url = f"{self.OAUTH_AUTHORIZE_URL}?{urlencode(params)}"
        logger.info(f"Generated Instagram authorization URL")
        return url
    
    async def exchange_code_for_token(self, code: str) -> InstagramTokenResponse:
        """
        Exchange authorization code for short-lived access token.
        
        Args:
            code: Authorization code from Instagram callback
            
        Returns:
            InstagramTokenResponse with access_token and user_id
            
        Raises:
            httpx.HTTPError: If token exchange fails
            
        Requirements: 2.2
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.OAUTH_TOKEN_URL,
                    data={
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                        'grant_type': 'authorization_code',
                        'redirect_uri': self.redirect_uri,
                        'code': code,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Successfully exchanged code for Instagram token")
                
                return InstagramTokenResponse(
                    access_token=data['access_token'],
                    user_id=data['user_id'],
                )
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to exchange Instagram code for token: {e}")
                raise
    
    async def exchange_for_long_lived_token(
        self, 
        short_lived_token: str
    ) -> InstagramLongLivedTokenResponse:
        """
        Exchange short-lived token for long-lived token (60 days).
        
        Args:
            short_lived_token: Short-lived access token from code exchange
            
        Returns:
            InstagramLongLivedTokenResponse with long-lived token
            
        Raises:
            httpx.HTTPError: If token exchange fails
            
        Requirements: 2.2
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.GRAPH_API_BASE}/access_token",
                    params={
                        'grant_type': 'ig_exchange_token',
                        'client_secret': self.client_secret,
                        'access_token': short_lived_token,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Successfully exchanged for long-lived Instagram token")
                
                return InstagramLongLivedTokenResponse(
                    access_token=data['access_token'],
                    token_type=data['token_type'],
                    expires_in=data['expires_in'],
                )
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to exchange for long-lived Instagram token: {e}")
                raise
    
    async def refresh_access_token(
        self, 
        access_token: str
    ) -> InstagramRefreshTokenResponse:
        """
        Refresh a long-lived access token (extends expiry by 60 days).
        
        Args:
            access_token: Current long-lived access token
            
        Returns:
            InstagramRefreshTokenResponse with refreshed token
            
        Raises:
            httpx.HTTPError: If token refresh fails
            
        Requirements: 2.4
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.GRAPH_API_BASE}/refresh_access_token",
                    params={
                        'grant_type': 'ig_refresh_token',
                        'access_token': access_token,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Successfully refreshed Instagram access token")
                
                return InstagramRefreshTokenResponse(
                    access_token=data['access_token'],
                    token_type=data['token_type'],
                    expires_in=data['expires_in'],
                )
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to refresh Instagram access token: {e}")
                raise
    
    async def get_user_profile(self, access_token: str) -> InstagramUserProfile:
        """
        Fetch Instagram user profile information.
        
        Args:
            access_token: Instagram access token
            
        Returns:
            InstagramUserProfile with user data
            
        Raises:
            httpx.HTTPError: If profile fetch fails
            
        Requirements: 2.6
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.GRAPH_API_BASE}/me",
                    params={
                        'fields': 'id,username,account_type,media_count',
                        'access_token': access_token,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Successfully fetched Instagram user profile: {data.get('username')}")
                
                return InstagramUserProfile(
                    id=str(data['id']),
                    username=data['username'],
                    account_type=data.get('account_type'),
                    media_count=data.get('media_count'),
                )
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch Instagram user profile: {e}")
                raise
    
    def calculate_token_expiry(self, expires_in_seconds: int) -> datetime:
        """
        Calculate token expiry datetime from expires_in seconds.
        
        Args:
            expires_in_seconds: Token lifetime in seconds
            
        Returns:
            datetime: Token expiry timestamp
        """
        return datetime.utcnow() + timedelta(seconds=expires_in_seconds)
    
    def is_token_expired(self, expires_at: datetime) -> bool:
        """
        Check if token is expired or will expire soon (within 7 days).
        
        Args:
            expires_at: Token expiry datetime
            
        Returns:
            bool: True if token is expired or expiring soon
        """
        # Refresh if token expires within 7 days
        buffer = timedelta(days=7)
        return datetime.utcnow() >= (expires_at - buffer)
    
    async def publish_post(
        self,
        access_token: str,
        instagram_user_id: str,
        image_url: str,
        caption: str
    ) -> str:
        """
        Publish a post to Instagram feed.
        
        This method implements the Instagram Container Publishing flow:
        1. Create media container with image and caption
        2. Poll container status until ready
        3. Publish container to feed
        
        Implements retry logic for transient failures:
        - 5xx errors: Exponential backoff (1s, 2s, 4s)
        - 429 rate limit: Respect retry-after header
        
        Args:
            access_token: Instagram access token
            instagram_user_id: Instagram user ID
            image_url: Publicly accessible image URL (S3 presigned URL)
            caption: Post caption with hashtags
            
        Returns:
            Instagram post ID
            
        Raises:
            httpx.HTTPError: If publishing fails after retries
            
        Requirements: 7.1, 7.2, 7.3, 7.4, 19.1, 19.2, 30.1
        """
        # Step 1: Create media container
        container_id = await self._create_media_container(
            access_token, instagram_user_id, image_url, caption
        )
        
        logger.info(f"Created Instagram media container: {container_id}")
        
        # Step 2: Poll container status
        await self._poll_container_status(access_token, container_id)
        
        logger.info(f"Instagram container ready: {container_id}")
        
        # Step 3: Publish container
        post_id = await self._publish_container(
            access_token, instagram_user_id, container_id
        )
        
        logger.info(f"Published Instagram post: {post_id}")
        
        return post_id
    
    async def _create_media_container(
        self,
        access_token: str,
        instagram_user_id: str,
        image_url: str,
        caption: str
    ) -> str:
        """
        Create Instagram media container.
        
        Args:
            access_token: Instagram access token
            instagram_user_id: Instagram user ID
            image_url: Publicly accessible image URL
            caption: Post caption
            
        Returns:
            Container ID
            
        Raises:
            httpx.HTTPError: If container creation fails
        """
        url = f"{self.GRAPH_API_BASE}/{instagram_user_id}/media"
        
        params = {
            'image_url': image_url,
            'caption': caption,
            'access_token': access_token,
        }
        
        # Retry with exponential backoff for 5xx errors
        backoff_delays = [1, 2, 4]  # seconds
        last_exception = None
        
        for attempt, delay in enumerate(backoff_delays + [None], start=1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, data=params)
                    
                    # Handle rate limiting (429)
                    if response.status_code == 429:
                        retry_after = int(response.headers.get('retry-after', 60))
                        logger.warning(
                            f"Instagram rate limit hit, waiting {retry_after}s "
                            f"(attempt {attempt})"
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    
                    # Handle 5xx errors with exponential backoff
                    if 500 <= response.status_code < 600:
                        if delay is not None:
                            logger.warning(
                                f"Instagram API 5xx error ({response.status_code}), "
                                f"retrying in {delay}s (attempt {attempt})"
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            # Last attempt, raise error
                            response.raise_for_status()
                    
                    # Raise for other 4xx errors (no retry)
                    response.raise_for_status()
                    
                    data = response.json()
                    return data['id']
                    
            except httpx.HTTPError as e:
                last_exception = e
                if delay is None:
                    # Last attempt failed
                    logger.error(f"Failed to create Instagram media container: {e}")
                    raise
        
        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in _create_media_container")
    
    async def _poll_container_status(
        self,
        access_token: str,
        container_id: str,
        max_wait_seconds: int = 30,
        poll_interval: int = 5
    ) -> None:
        """
        Poll Instagram container status until ready.
        
        Args:
            access_token: Instagram access token
            container_id: Container ID to poll
            max_wait_seconds: Maximum time to wait (default: 30s)
            poll_interval: Seconds between polls (default: 5s)
            
        Raises:
            TimeoutError: If container not ready within max_wait_seconds
            httpx.HTTPError: If status check fails
        """
        url = f"{self.GRAPH_API_BASE}/{container_id}"
        params = {
            'fields': 'status_code',
            'access_token': access_token,
        }
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= max_wait_seconds:
                raise TimeoutError(
                    f"Instagram container {container_id} not ready after {max_wait_seconds}s"
                )
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    
                    data = response.json()
                    status_code = data.get('status_code')
                    
                    if status_code == 'FINISHED':
                        return
                    elif status_code == 'ERROR':
                        raise RuntimeError(
                            f"Instagram container {container_id} processing failed"
                        )
                    
                    # Status is IN_PROGRESS or other, wait and retry
                    logger.debug(
                        f"Instagram container {container_id} status: {status_code}, "
                        f"waiting {poll_interval}s"
                    )
                    await asyncio.sleep(poll_interval)
                    
            except httpx.HTTPError as e:
                logger.error(f"Failed to check Instagram container status: {e}")
                raise
    
    async def _publish_container(
        self,
        access_token: str,
        instagram_user_id: str,
        container_id: str
    ) -> str:
        """
        Publish Instagram media container to feed.
        
        Args:
            access_token: Instagram access token
            instagram_user_id: Instagram user ID
            container_id: Container ID to publish
            
        Returns:
            Instagram post ID
            
        Raises:
            httpx.HTTPError: If publishing fails
        """
        url = f"{self.GRAPH_API_BASE}/{instagram_user_id}/media_publish"
        
        params = {
            'creation_id': container_id,
            'access_token': access_token,
        }
        
        # Retry with exponential backoff for 5xx errors
        backoff_delays = [1, 2, 4]  # seconds
        last_exception = None
        
        for attempt, delay in enumerate(backoff_delays + [None], start=1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, data=params)
                    
                    # Handle rate limiting (429)
                    if response.status_code == 429:
                        retry_after = int(response.headers.get('retry-after', 60))
                        logger.warning(
                            f"Instagram rate limit hit, waiting {retry_after}s "
                            f"(attempt {attempt})"
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    
                    # Handle 5xx errors with exponential backoff
                    if 500 <= response.status_code < 600:
                        if delay is not None:
                            logger.warning(
                                f"Instagram API 5xx error ({response.status_code}), "
                                f"retrying in {delay}s (attempt {attempt})"
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            # Last attempt, raise error
                            response.raise_for_status()
                    
                    # Raise for other 4xx errors (no retry)
                    response.raise_for_status()
                    
                    data = response.json()
                    return data['id']
                    
            except httpx.HTTPError as e:
                last_exception = e
                if delay is None:
                    # Last attempt failed
                    logger.error(f"Failed to publish Instagram container: {e}")
                    raise
        
        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in _publish_container")
    
    async def verify_post_exists(self, access_token: str, post_id: str) -> bool:
        """
        Verify if an Instagram post exists.
        
        Used for idempotency checking to determine if a post was already published.
        
        Args:
            access_token: Instagram access token
            post_id: Instagram post ID to verify
            
        Returns:
            True if post exists, False otherwise
            
        Requirements: 18.1, 18.3
        """
        url = f"{self.GRAPH_API_BASE}/{post_id}"
        params = {
            'fields': 'id',
            'access_token': access_token,
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    return True
                elif response.status_code == 404:
                    return False
                else:
                    # Unexpected status, raise for investigation
                    response.raise_for_status()
                    return False
                    
        except httpx.HTTPError as e:
            logger.error(f"Failed to verify Instagram post {post_id}: {e}")
            # On error, assume post doesn't exist to allow retry
            return False
    
    async def fetch_insights(
        self,
        access_token: str,
        post_id: str
    ) -> InstagramInsights:
        """
        Fetch Instagram insights for a published post.
        
        Calls Instagram Graph API /{post_id}/insights to retrieve:
        - likes
        - comments
        - reach
        - impressions
        
        Calculates engagement_rate as: (likes + comments) / reach
        
        Args:
            access_token: Instagram access token
            post_id: Instagram post ID
            
        Returns:
            InstagramInsights object with metrics
            
        Raises:
            httpx.HTTPError: If insights fetch fails
            
        Requirements: 8.1
        """
        url = f"{self.GRAPH_API_BASE}/{post_id}/insights"
        
        # Request specific metrics
        params = {
            'metric': 'likes,comments,reach,impressions',
            'access_token': access_token,
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Parse metrics from response
                metrics = {}
                for metric_data in data.get('data', []):
                    metric_name = metric_data.get('name')
                    metric_value = metric_data.get('values', [{}])[0].get('value', 0)
                    metrics[metric_name] = metric_value
                
                # Extract values with defaults
                likes = metrics.get('likes', 0)
                comments = metrics.get('comments', 0)
                reach = metrics.get('reach', 0)
                impressions = metrics.get('impressions', 0)
                
                # Calculate engagement rate
                engagement_rate = 0.0
                if reach > 0:
                    engagement_rate = ((likes + comments) / reach) * 100
                
                logger.info(
                    f"Fetched Instagram insights for post {post_id}: "
                    f"likes={likes}, comments={comments}, reach={reach}, "
                    f"impressions={impressions}, engagement_rate={engagement_rate:.2f}%"
                )
                
                return InstagramInsights(
                    likes=likes,
                    comments=comments,
                    reach=reach,
                    impressions=impressions,
                    engagement_rate=engagement_rate,
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch Instagram insights for post {post_id}: {e}")
            raise
    
    async def publish_with_idempotency_check(
        self,
        campaign_id: str,
        existing_post_id: Optional[str],
        access_token: str,
        instagram_user_id: str,
        image_url: str,
        caption: str
    ) -> str:
        """
        Publish post with idempotency checking.
        
        This method ensures campaigns are never published twice:
        1. If campaign already has instagram_post_id, verify post exists
        2. If post exists, return existing post_id
        3. If post doesn't exist, proceed with publishing
        
        Args:
            campaign_id: Campaign ID for logging
            existing_post_id: Existing Instagram post ID (if any)
            access_token: Instagram access token
            instagram_user_id: Instagram user ID
            image_url: Publicly accessible image URL
            caption: Post caption
            
        Returns:
            Instagram post ID (existing or newly created)
            
        Requirements: 18.1, 18.3
        """
        # Check if campaign already has a post ID
        if existing_post_id:
            logger.info(
                f"Campaign {campaign_id} already has post ID {existing_post_id}, "
                "verifying existence"
            )
            
            # Verify post exists on Instagram
            post_exists = await self.verify_post_exists(access_token, existing_post_id)
            
            if post_exists:
                logger.info(
                    f"Instagram post {existing_post_id} exists, "
                    f"skipping publish for campaign {campaign_id}"
                )
                return existing_post_id
            else:
                logger.warning(
                    f"Instagram post {existing_post_id} not found, "
                    f"proceeding with new publish for campaign {campaign_id}"
                )
        
        # No existing post or post doesn't exist, proceed with publishing
        post_id = await self.publish_post(
            access_token, instagram_user_id, image_url, caption
        )
        
        return post_id


async def refresh_instagram_token(user_id: str, user_repo: 'UserRepository') -> bool:
    """
    Refresh Instagram access token for a user.
    
    This function:
    1. Retrieves user from database
    2. Decrypts current access token
    3. Calls Instagram API to refresh token
    4. Encrypts new token
    5. Updates user in database
    
    Args:
        user_id: User ID to refresh token for
        user_repo: UserRepository instance
        
    Returns:
        bool: True if refresh successful, False otherwise
        
    Requirements: 2.4
    """
    from shared.services.encryption_service import decrypt_token, encrypt_token
    
    logger.info(f"Refreshing Instagram token for user: {user_id}")
    
    try:
        # Get user from database
        user = await user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            return False
        
        if not user.instagram_access_token:
            logger.error(f"User has no Instagram token: {user_id}")
            return False
        
        # Decrypt current token
        current_token = await decrypt_token(user.instagram_access_token)
        
        # Call Instagram API to refresh token
        instagram_service = InstagramService()
        refresh_response = await instagram_service.refresh_access_token(current_token)
        
        # Encrypt new token
        encrypted_token = await encrypt_token(refresh_response.access_token)
        
        # Calculate new expiry
        new_expires_at = instagram_service.calculate_token_expiry(
            refresh_response.expires_in
        )
        
        # Update user
        user.instagram_access_token = encrypted_token
        user.instagram_token_expires_at = new_expires_at
        user.updated_at = datetime.utcnow()
        
        await user_repo.update(user)
        
        logger.info(f"Successfully refreshed Instagram token for user: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to refresh Instagram token for user {user_id}: {e}", exc_info=True)
        return False
