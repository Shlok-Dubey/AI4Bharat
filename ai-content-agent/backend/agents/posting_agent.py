"""
Posting Agent

This module handles automated posting to social media platforms.
Currently uses placeholder logic for local development.

For production deployment:
- Integrate with Meta Graph API for Instagram/Facebook
- Use Twitter API v2 for Twitter/X
- Use LinkedIn API for LinkedIn
- Implement retry logic and error handling
- Add webhook handlers for post status updates
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
import uuid

class PostingAgent:
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
        hashtags: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Post content to Instagram using Meta Graph API.
        
        Args:
            access_token: User's Instagram access token
            instagram_account_id: Instagram Business Account ID
            caption: Post caption text
            image_url: URL of image to post (must be publicly accessible)
            hashtags: Hashtags to include
            
        Returns:
            Tuple of (success, platform_post_id, error_message)
        """
        import requests
        
        if not access_token or not instagram_account_id:
            return False, None, "Missing access token or account ID"
        
        if not image_url:
            return False, None, "Image URL is required for Instagram posts"
        
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
    
    def post_to_facebook(
        self,
        access_token: str,
        page_id: str,
        message: str,
        image_url: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Post content to Facebook Page.
        
        Args:
            access_token: Page access token
            page_id: Facebook Page ID
            message: Post message
            image_url: Optional image URL
            
        Returns:
            Tuple of (success, post_id, error_message)
            
        For production with Meta Graph API:
        
        # Post with photo
        url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        params = {
            "url": image_url,
            "caption": message,
            "access_token": access_token
        }
        
        # Or post text only
        url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
        params = {
            "message": message,
            "access_token": access_token
        }
        
        response = requests.post(url, params=params)
        
        if response.status_code == 200:
            post_id = response.json().get("id")
            return True, post_id, None
        else:
            return False, None, response.text
        """
        # Placeholder
        mock_post_id = f"facebook_{uuid.uuid4().hex[:12]}"
        return True, mock_post_id, None
    
    def post_to_twitter(
        self,
        access_token: str,
        access_token_secret: str,
        tweet_text: str,
        media_ids: Optional[list] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Post tweet to Twitter/X.
        
        Args:
            access_token: OAuth access token
            access_token_secret: OAuth access token secret
            tweet_text: Tweet text (max 280 characters)
            media_ids: List of uploaded media IDs
            
        Returns:
            Tuple of (success, tweet_id, error_message)
            
        For production with Twitter API v2:
        
        import requests
        from requests_oauthlib import OAuth1
        
        # Create OAuth1 session
        auth = OAuth1(
            client_key=TWITTER_API_KEY,
            client_secret=TWITTER_API_SECRET,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )
        
        # Upload media first (if any)
        if media_ids is None and image_url:
            media_upload_url = "https://upload.twitter.com/1.1/media/upload.json"
            # Download image and upload
            # ... media upload logic ...
            media_ids = [uploaded_media_id]
        
        # Create tweet
        url = "https://api.twitter.com/2/tweets"
        payload = {
            "text": tweet_text
        }
        
        if media_ids:
            payload["media"] = {"media_ids": media_ids}
        
        response = requests.post(url, json=payload, auth=auth)
        
        if response.status_code == 201:
            tweet_id = response.json()["data"]["id"]
            return True, tweet_id, None
        else:
            return False, None, response.text
        
        Rate Limits:
        - 300 tweets per 3 hours
        - 50 tweets per hour (recommended)
        """
        # Placeholder
        mock_tweet_id = f"twitter_{uuid.uuid4().hex[:12]}"
        return True, mock_tweet_id, None
    
    def post_to_linkedin(
        self,
        access_token: str,
        person_urn: str,
        text: str,
        image_url: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Post content to LinkedIn.
        
        Args:
            access_token: LinkedIn access token
            person_urn: LinkedIn person URN
            text: Post text
            image_url: Optional image URL
            
        Returns:
            Tuple of (success, post_id, error_message)
            
        For production with LinkedIn API:
        
        import requests
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        # Upload image first (if any)
        if image_url:
            # Register upload
            register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
            register_payload = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": person_urn,
                    "serviceRelationships": [{
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }]
                }
            }
            
            register_response = requests.post(
                register_url,
                json=register_payload,
                headers=headers
            )
            
            asset_urn = register_response.json()["value"]["asset"]
            upload_url = register_response.json()["value"]["uploadMechanism"]["..."]["uploadUrl"]
            
            # Upload image
            # ... upload logic ...
        
        # Create post
        url = "https://api.linkedin.com/v2/ugcPosts"
        payload = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"  # or "IMAGE" if image
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        if image_url and asset_urn:
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                "status": "READY",
                "media": asset_urn
            }]
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            post_id = response.headers.get("X-RestLi-Id")
            return True, post_id, None
        else:
            return False, None, response.text
        """
        # Placeholder
        mock_post_id = f"linkedin_{uuid.uuid4().hex[:12]}"
        return True, mock_post_id, None
    
    def update_post_status(
        self,
        db_session,
        scheduled_post_id: uuid.UUID,
        status: str,
        platform_post_id: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """
        Update scheduled post status in database.
        
        Args:
            db_session: SQLAlchemy database session
            scheduled_post_id: UUID of scheduled post
            status: New status (published, failed, cancelled)
            platform_post_id: ID from social media platform
            error_message: Error message if failed
            
        Status values:
        - pending: Waiting to be posted
        - published: Successfully posted
        - failed: Posting failed
        - cancelled: Manually cancelled
        
        For production:
        - Add to scheduled_posts table
        - Track retry attempts
        - Store platform response
        - Update published_at timestamp
        """
        from models.content import ScheduledPost
        
        scheduled_post = db_session.query(ScheduledPost).filter(
            ScheduledPost.id == scheduled_post_id
        ).first()
        
        if scheduled_post:
            scheduled_post.status = status
            
            if platform_post_id:
                scheduled_post.platform_post_id = platform_post_id
                scheduled_post.published_at = datetime.utcnow()
            
            if error_message:
                scheduled_post.error_message = error_message
                scheduled_post.retry_count += 1
            
            db_session.commit()
    
    def post_scheduled_content(
        self,
        db_session,
        scheduled_post_id: uuid.UUID,
        access_token: str,
        account_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Post a scheduled content piece.
        
        This is the main function called by the scheduler to post content.
        
        Args:
            db_session: Database session
            scheduled_post_id: UUID of scheduled post
            access_token: Platform access token
            account_id: Platform account ID
            
        Returns:
            Tuple of (success, error_message)
            
        Workflow:
        1. Fetch scheduled post from database
        2. Get content details
        3. Determine platform
        4. Call appropriate posting function
        5. Update post status in database
        6. Return result
        
        For production:
        - Implement as background task (Celery, RQ)
        - Add to posting queue
        - Handle rate limits
        - Implement retry logic
        - Send notifications on success/failure
        """
        from models.content import ScheduledPost, GeneratedContent
        
        # Fetch scheduled post
        scheduled_post = db_session.query(ScheduledPost).filter(
            ScheduledPost.id == scheduled_post_id
        ).first()
        
        if not scheduled_post:
            return False, "Scheduled post not found"
        
        # Get content
        content = scheduled_post.content
        
        if not content:
            return False, "Content not found"
        
        # Determine platform and post
        platform = content.platform
        caption = content.content_text
        hashtags = content.hashtags
        
        try:
            if platform == "instagram":
                success, post_id, error = self.post_to_instagram(
                    access_token=access_token,
                    instagram_account_id=account_id,
                    caption=caption,
                    hashtags=hashtags
                )
            elif platform == "facebook":
                success, post_id, error = self.post_to_facebook(
                    access_token=access_token,
                    page_id=account_id,
                    message=f"{caption}\n\n{hashtags}" if hashtags else caption
                )
            elif platform == "twitter":
                success, post_id, error = self.post_to_twitter(
                    access_token=access_token,
                    access_token_secret="",  # Would need to store this
                    tweet_text=f"{caption}\n\n{hashtags}" if hashtags else caption
                )
            elif platform == "linkedin":
                success, post_id, error = self.post_to_linkedin(
                    access_token=access_token,
                    person_urn=account_id,
                    text=f"{caption}\n\n{hashtags}" if hashtags else caption
                )
            else:
                return False, f"Unsupported platform: {platform}"
            
            # Update status
            if success:
                self.update_post_status(
                    db_session=db_session,
                    scheduled_post_id=scheduled_post_id,
                    status="published",
                    platform_post_id=post_id
                )
                return True, None
            else:
                self.update_post_status(
                    db_session=db_session,
                    scheduled_post_id=scheduled_post_id,
                    status="failed",
                    error_message=error
                )
                return False, error
                
        except Exception as e:
            self.update_post_status(
                db_session=db_session,
                scheduled_post_id=scheduled_post_id,
                status="failed",
                error_message=str(e)
            )
            return False, str(e)


# Singleton instance
_posting_agent = None

def get_posting_agent() -> PostingAgent:
    """
    Get or create the posting agent instance.
    
    Returns:
        PostingAgent instance
    """
    global _posting_agent
    if _posting_agent is None:
        _posting_agent = PostingAgent()
    return _posting_agent
