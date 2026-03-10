"""
Posting Agent - Production Grade

Handles automated posting to Instagram with comprehensive error handling.
Integrates with DynamoDB for status tracking and retry support.
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
import time
import requests
from requests.exceptions import Timeout, RequestException


class InstagramPostingError(Exception):
    """Base exception for Instagram posting errors"""
    pass


class TokenExpiredError(InstagramPostingError):
    """Raised when access token is expired or invalid"""
    pass


class InvalidMediaError(InstagramPostingError):
    """Raised when media URL is invalid or inaccessible"""
    pass


class RateLimitError(InstagramPostingError):
    """Raised when API rate limit is exceeded"""
    pass


class PublishingError(InstagramPostingError):
    """Raised when publishing fails"""
    pass


class PostingAgent:
    """
    Production-grade posting agent for Instagram.
    
    Features:
    - Comprehensive error handling
    - Token validation and refresh
    - DynamoDB status tracking
    - Retry support
    - Rate limit handling
    """
    
    def __init__(self):
        """Initialize the posting agent."""
        self.api_version = 'v19.0'
        self.base_url = f'https://graph.facebook.com/{self.api_version}'
        self.timeout = 30
        self.container_check_retries = 10
        self.container_check_delay = 2
    
    def post_to_instagram(
        self,
        access_token: str,
        instagram_account_id: str,
        caption: str,
        image_url: str,
        hashtags: Optional[str] = None,
        user_id: Optional[str] = None,
        post_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Post content to Instagram using Meta Graph API.
        
        Flow: media_url → create container → publish container → return post_id
        
        Args:
            access_token: Instagram access token
            instagram_account_id: Instagram Business Account ID
            caption: Post caption
            image_url: Public S3 URL of image
            hashtags: Optional hashtags
            user_id: User ID for token refresh
            post_id: Scheduled post ID for status updates
            
        Returns:
            Tuple of (success, instagram_post_id, error_message)
        """
        print(f"🚀 Starting Instagram post flow...")
        
        # Validate inputs
        if not access_token or not instagram_account_id:
            error = "Missing access token or account ID"
            self._update_post_status(post_id, 'failed', error_message=error)
            return False, None, error
        
        if not image_url:
            error = "Image URL is required"
            self._update_post_status(post_id, 'failed', error_message=error)
            return False, None, error
        
        # Check and refresh token if needed
        if user_id:
            token_valid, token_error = self._validate_and_refresh_token(user_id)
            if not token_valid:
                self._update_post_status(post_id, 'failed', error_message=token_error)
                return False, None, token_error
            
            # Get refreshed token
            access_token = self._get_refreshed_token(user_id) or access_token
        
        try:
            # Step 1: Create media container
            container_id = self._create_media_container(
                access_token,
                instagram_account_id,
                image_url,
                caption,
                hashtags
            )
            
            # Step 2: Wait for container to be ready
            self._wait_for_container(access_token, container_id)
            
            # Step 3: Publish container
            instagram_post_id = self._publish_container(
                access_token,
                instagram_account_id,
                container_id
            )
            
            # Step 4: Update status to posted
            self._update_post_status(
                post_id,
                'posted',
                instagram_post_id=instagram_post_id,
                posted_at=datetime.utcnow().isoformat()
            )
            
            print(f"✅ Successfully posted! Instagram ID: {instagram_post_id}")
            return True, instagram_post_id, None
            
        except TokenExpiredError as e:
            error = str(e)
            print(f"❌ Token error: {error}")
            self._update_post_status(post_id, 'failed', error_message=error)
            self._mark_token_for_reauth(user_id)
            return False, None, error
            
        except InvalidMediaError as e:
            error = str(e)
            print(f"❌ Media error: {error}")
            self._update_post_status(post_id, 'failed', error_message=error)
            return False, None, error
            
        except RateLimitError as e:
            error = str(e)
            print(f"❌ Rate limit error: {error}")
            self._update_post_status(post_id, 'failed', error_message=error)
            return False, None, error
            
        except PublishingError as e:
            error = str(e)
            print(f"❌ Publishing error: {error}")
            self._update_post_status(post_id, 'failed', error_message=error)
            return False, None, error
            
        except Timeout:
            error = "Request timeout - Instagram API took too long"
            print(f"❌ {error}")
            self._update_post_status(post_id, 'failed', error_message=error)
            return False, None, error
            
        except RequestException as e:
            error = f"Network error: {str(e)}"
            print(f"❌ {error}")
            self._update_post_status(post_id, 'failed', error_message=error)
            return False, None, error
            
        except Exception as e:
            error = f"Unexpected error: {str(e)}"
            print(f"❌ {error}")
            import traceback
            traceback.print_exc()
            self._update_post_status(post_id, 'failed', error_message=error)
            return False, None, error
    
    def _create_media_container(
        self,
        access_token: str,
        instagram_account_id: str,
        image_url: str,
        caption: str,
        hashtags: Optional[str]
    ) -> str:
        """
        Create Instagram media container.
        
        Returns:
            Container ID
            
        Raises:
            TokenExpiredError: If token is invalid
            InvalidMediaError: If media URL is invalid
            RateLimitError: If rate limit exceeded
            PublishingError: If creation fails
        """
        print(f"📸 Creating media container...")
        
        # Prepare caption
        full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption
        
        url = f"{self.base_url}/{instagram_account_id}/media"
        params = {
            "image_url": image_url,
            "caption": full_caption,
            "access_token": access_token
        }
        
        try:
            response = requests.post(url, params=params, timeout=self.timeout)
            
            # Handle errors
            if response.status_code == 400:
                error_data = response.json().get('error', {})
                error_msg = error_data.get('message', response.text)
                
                # Check for specific errors
                if 'token' in error_msg.lower() or 'oauth' in error_msg.lower():
                    raise TokenExpiredError(f"Invalid access token: {error_msg}")
                elif 'url' in error_msg.lower() or 'media' in error_msg.lower():
                    raise InvalidMediaError(f"Invalid media URL: {error_msg}")
                else:
                    raise PublishingError(f"Container creation failed: {error_msg}")
            
            elif response.status_code == 429:
                raise RateLimitError("Instagram API rate limit exceeded")
            
            elif response.status_code != 200:
                raise PublishingError(f"Container creation failed: {response.text}")
            
            # Extract container ID
            container_id = response.json().get("id")
            if not container_id:
                raise PublishingError("No container ID in response")
            
            print(f"✅ Container created: {container_id}")
            return container_id
            
        except (TokenExpiredError, InvalidMediaError, RateLimitError, PublishingError):
            raise
        except RequestException as e:
            raise PublishingError(f"Network error creating container: {str(e)}")
    
    def _wait_for_container(self, access_token: str, container_id: str):
        """
        Wait for container to be ready for publishing.
        
        Raises:
            PublishingError: If container fails or times out
        """
        print(f"⏳ Waiting for container to be ready...")
        
        url = f"{self.base_url}/{container_id}"
        params = {
            "fields": "status_code",
            "access_token": access_token
        }
        
        for attempt in range(self.container_check_retries):
            try:
                response = requests.get(url, params=params, timeout=self.timeout)
                
                if response.status_code != 200:
                    raise PublishingError(f"Failed to check container status: {response.text}")
                
                status_code = response.json().get("status_code")
                
                if status_code == "FINISHED":
                    print(f"✅ Container ready")
                    return
                elif status_code == "ERROR":
                    raise PublishingError("Container processing failed")
                elif status_code == "IN_PROGRESS":
                    print(f"⏳ Processing... ({attempt + 1}/{self.container_check_retries})")
                    time.sleep(self.container_check_delay)
                else:
                    print(f"⚠️  Unknown status: {status_code}")
                    time.sleep(self.container_check_delay)
                    
            except RequestException as e:
                if attempt == self.container_check_retries - 1:
                    raise PublishingError(f"Failed to check container status: {str(e)}")
                time.sleep(self.container_check_delay)
        
        raise PublishingError("Container processing timeout")
    
    def _publish_container(
        self,
        access_token: str,
        instagram_account_id: str,
        container_id: str
    ) -> str:
        """
        Publish media container to Instagram.
        
        Returns:
            Instagram post ID
            
        Raises:
            PublishingError: If publishing fails
        """
        print(f"🚀 Publishing container...")
        
        url = f"{self.base_url}/{instagram_account_id}/media_publish"
        params = {
            "creation_id": container_id,
            "access_token": access_token
        }
        
        try:
            response = requests.post(url, params=params, timeout=self.timeout)
            
            if response.status_code != 200:
                raise PublishingError(f"Publishing failed: {response.text}")
            
            instagram_post_id = response.json().get("id")
            if not instagram_post_id:
                raise PublishingError("No post ID in response")
            
            print(f"✅ Published! Post ID: {instagram_post_id}")
            return instagram_post_id
            
        except RequestException as e:
            raise PublishingError(f"Network error publishing: {str(e)}")
    
    def _validate_and_refresh_token(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """Validate token and refresh if needed"""
        try:
            from utils.instagram_token_refresh import refresh_instagram_token, check_token_validity
            import dynamodb_client as db
            
            oauth_account = db.get_oauth_account_by_provider(user_id, 'meta')
            if not oauth_account:
                return False, "Instagram account not connected"
            
            # Check validity
            is_valid, error_msg = check_token_validity(oauth_account)
            if not is_valid:
                return False, error_msg
            
            # Try to refresh
            refresh_success, refresh_error = refresh_instagram_token(user_id)
            if not refresh_success:
                return False, f"Token refresh failed: {refresh_error}"
            
            return True, None
            
        except Exception as e:
            return False, f"Token validation error: {str(e)}"
    
    def _get_refreshed_token(self, user_id: str) -> Optional[str]:
        """Get refreshed access token"""
        try:
            import dynamodb_client as db
            oauth_account = db.get_oauth_account_by_provider(user_id, 'meta')
            return oauth_account.get('access_token') if oauth_account else None
        except:
            return None
    
    def _mark_token_for_reauth(self, user_id: str):
        """Mark token as needing re-authentication"""
        if not user_id:
            return
        
        try:
            import dynamodb_client as db
            oauth_account = db.get_oauth_account_by_provider(user_id, 'meta')
            if oauth_account:
                db.update_oauth_account(
                    oauth_account['oauth_id'],
                    scope='needs_reauth'
                )
        except Exception as e:
            print(f"⚠️  Failed to mark token for reauth: {e}")
    
    def _update_post_status(
        self,
        post_id: Optional[str],
        status: str,
        instagram_post_id: Optional[str] = None,
        posted_at: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Update post status in DynamoDB"""
        if not post_id:
            return
        
        try:
            import dynamodb_client as db
            
            update_data = {'status': status}
            
            if instagram_post_id:
                update_data['platform_post_id'] = instagram_post_id
            
            if posted_at:
                update_data['published_at'] = posted_at
            
            if error_message:
                update_data['error_message'] = error_message
                # Increment retry count
                post = db.get_scheduled_post(post_id)
                if post:
                    update_data['retry_count'] = post.get('retry_count', 0) + 1
            
            db.update_scheduled_post(post_id, **update_data)
            print(f"✅ Updated post status: {status}")
            
        except Exception as e:
            print(f"⚠️  Failed to update post status: {e}")


# Singleton instance
_posting_agent = None


def get_posting_agent() -> PostingAgent:
    """Get or create the posting agent instance"""
    global _posting_agent
    if _posting_agent is None:
        _posting_agent = PostingAgent()
    return _posting_agent

    """
    AI agent for posting content to social media platforms.
    
    This agent:
    - Posts content to Instagram, Facebook, Twitter, LinkedIn
    - Handles media uploads
    - Tracks posting status
    - Manages rate limits
    - Implements retry logic
    
    For production:
    - Use platform-specific APIs
    - Implement OAuth token refresh
    - Handle rate limiting
    - Add webhook handlers
    - Implement queue system for bulk posting
    """
    
    def __init__(self):
        """Initialize the posting agent."""
        self.max_retries = 3
        self.retry_delay = 60  # seconds
    
    def post_to_instagram(
        self,
        access_token: str,
        instagram_account_id: str,
        caption: str,
        image_url: Optional[str] = None,
        hashtags: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Post content to Instagram using Meta Graph API.
        
        Automatically checks token validity and refreshes if needed.
        
        Args:
            access_token: User's Instagram access token
            instagram_account_id: Instagram Business Account ID
            caption: Post caption text
            image_url: URL of image to post (must be publicly accessible)
            hashtags: Hashtags to include
            user_id: User ID (for token refresh)
            
        Returns:
            Tuple of (success, platform_post_id, error_message)
        """
        import requests
        from utils.instagram_token_refresh import refresh_instagram_token, check_token_validity
        import dynamodb_client as db
        
        if not access_token or not instagram_account_id:
            return False, None, "Missing access token or account ID"
        
        if not image_url:
            return False, None, "Image URL is required for Instagram posts"
        
        # Check token validity and refresh if needed
        if user_id:
            oauth_account = db.get_oauth_account_by_provider(user_id, 'meta')
            
            if oauth_account:
                # Check if token is valid
                is_valid, error_msg = check_token_validity(oauth_account)
                
                if not is_valid:
                    print(f"⚠️  Token invalid: {error_msg}")
                    return False, None, error_msg
                
                # Try to refresh token if expiring soon
                print(f"🔄 Checking if token needs refresh...")
                refresh_success, refresh_error = refresh_instagram_token(user_id)
                
                if not refresh_success:
                    print(f"⚠️  Token refresh failed: {refresh_error}")
                    return False, None, f"Token refresh failed: {refresh_error}"
                
                # Get updated token after refresh
                oauth_account = db.get_oauth_account_by_provider(user_id, 'meta')
                if oauth_account:
                    access_token = oauth_account['access_token']
                    print(f"✅ Using refreshed token")
        
        try:
            # Combine caption and hashtags
            full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption
            
            # Step 1: Create media container
            print(f"📸 Creating Instagram media container...")
            container_url = f"https://graph.facebook.com/v19.0/{instagram_account_id}/media"
            container_params = {
                "image_url": image_url,
                "caption": full_caption,
                "access_token": access_token
            }
            
            container_response = requests.post(container_url, params=container_params, timeout=30)
            
            if container_response.status_code != 200:
                error_msg = f"Failed to create container: {container_response.text}"
                print(f"❌ {error_msg}")
                
                # Check if it's a token error
                if 'OAuthException' in error_msg or 'access token' in error_msg.lower():
                    # Mark token as needing re-auth
                    if user_id:
                        oauth_account = db.get_oauth_account_by_provider(user_id, 'meta')
                        if oauth_account:
                            db.update_oauth_account(
                                oauth_account['oauth_id'],
                                scope='needs_reauth'
                            )
                    return False, None, "Instagram access token is invalid. Please reconnect your account."
                
                return False, None, error_msg
            
            container_id = container_response.json().get("id")
            print(f"✅ Container created: {container_id}")
            
            # Step 2: Check container status (optional but recommended)
            import time
            max_retries = 10
            for attempt in range(max_retries):
                status_url = f"https://graph.facebook.com/v19.0/{container_id}"
                status_params = {
                    "fields": "status_code",
                    "access_token": access_token
                }
                
                status_response = requests.get(status_url, params=status_params, timeout=30)
                status_code = status_response.json().get("status_code")
                
                if status_code == "FINISHED":
                    print(f"✅ Container ready for publishing")
                    break
                elif status_code == "ERROR":
                    return False, None, "Container creation failed with error status"
                elif status_code == "IN_PROGRESS":
                    print(f"⏳ Container processing... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(2)
                else:
                    print(f"⚠️  Unknown status: {status_code}")
                    time.sleep(2)
            
            # Step 3: Publish media container
            print(f"🚀 Publishing to Instagram...")
            publish_url = f"https://graph.facebook.com/v19.0/{instagram_account_id}/media_publish"
            publish_params = {
                "creation_id": container_id,
                "access_token": access_token
            }
            
            publish_response = requests.post(publish_url, params=publish_params, timeout=30)
            
            if publish_response.status_code != 200:
                error_msg = f"Failed to publish: {publish_response.text}"
                print(f"❌ {error_msg}")
                return False, None, error_msg
            
            media_id = publish_response.json().get("id")
            print(f"✅ Published to Instagram! Media ID: {media_id}")
            
            return True, media_id, None
            
        except requests.exceptions.Timeout:
            return False, None, "Request timeout - Instagram API took too long to respond"
        except requests.exceptions.RequestException as e:
            return False, None, f"Network error: {str(e)}"
        except Exception as e:
            return False, None, f"Unexpected error: {str(e)}"


# Singleton instance
_posting_agent = None


def get_posting_agent() -> PostingAgent:
    """Get or create the posting agent instance"""
    global _posting_agent
    if _posting_agent is None:
        _posting_agent = PostingAgent()
    return _posting_agent
