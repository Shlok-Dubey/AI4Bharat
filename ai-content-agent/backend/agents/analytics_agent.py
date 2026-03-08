"""
Analytics Agent Module

Purpose: Fetch engagement metrics for published posts
Metrics: views, likes, comments, shares, engagement_rate

For local development: Uses mock data
For production: Integrates with Meta Graph API
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
import random


class AnalyticsAgent:
    """
    Agent responsible for fetching and analyzing post engagement metrics
    """
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize Analytics Agent
        
        Args:
            access_token: Meta Graph API access token (for production)
        """
        self.access_token = access_token
    
    def fetch_post_analytics(self, post_id: str, platform: str = "instagram") -> Dict:
        """
        Fetch analytics for a specific post from Instagram API.
        
        Args:
            post_id: ID of the published post
            platform: Social media platform (instagram, youtube, etc.)
        
        Returns:
            Dictionary containing engagement metrics
        """
        
        if platform.lower() == "instagram":
            # Try to fetch real Instagram analytics
            if self.access_token:
                try:
                    return self._fetch_instagram_analytics(post_id)
                except Exception as e:
                    print(f"⚠️  Failed to fetch Instagram analytics: {e}")
                    print(f"📊 Using mock data as fallback")
            
        # Fallback to mock data
        return self._generate_mock_analytics(post_id, platform)
    
    def fetch_campaign_analytics(self, campaign_id: str, post_ids: List[str]) -> Dict:
        """
        Fetch aggregated analytics for an entire campaign
        
        Args:
            campaign_id: Campaign identifier
            post_ids: List of post IDs in the campaign
        
        Returns:
            Aggregated metrics for the campaign
        """
        
        total_views = 0
        total_likes = 0
        total_comments = 0
        total_shares = 0
        post_analytics = []
        
        for post_id in post_ids:
            analytics = self.fetch_post_analytics(post_id)
            post_analytics.append(analytics)
            
            total_views += analytics.get("views", 0)
            total_likes += analytics.get("likes", 0)
            total_comments += analytics.get("comments", 0)
            total_shares += analytics.get("shares", 0)
        
        # Calculate overall engagement rate
        total_engagements = total_likes + total_comments + total_shares
        engagement_rate = (total_engagements / total_views * 100) if total_views > 0 else 0
        
        return {
            "campaign_id": campaign_id,
            "total_posts": len(post_ids),
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "total_engagements": total_engagements,
            "engagement_rate": round(engagement_rate, 2),
            "average_views_per_post": round(total_views / len(post_ids), 2) if post_ids else 0,
            "post_analytics": post_analytics,
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _generate_mock_analytics(self, post_id: str, platform: str) -> Dict:
        """
        Generate mock analytics data for local development
        
        Args:
            post_id: Post identifier
            platform: Social media platform
        
        Returns:
            Mock analytics data
        """
        
        # Generate realistic random metrics
        views = random.randint(500, 10000)
        likes = random.randint(50, int(views * 0.15))
        comments = random.randint(5, int(likes * 0.2))
        shares = random.randint(2, int(likes * 0.1))
        
        # Calculate engagement rate
        total_engagements = likes + comments + shares
        engagement_rate = (total_engagements / views * 100) if views > 0 else 0
        
        return {
            "post_id": post_id,
            "platform": platform,
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": random.randint(10, int(likes * 0.3)),
            "reach": random.randint(int(views * 0.8), int(views * 1.2)),
            "impressions": random.randint(views, int(views * 1.5)),
            "engagement_rate": round(engagement_rate, 2),
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _fetch_instagram_analytics(self, post_id: str) -> Dict:
        """
        Fetch analytics from Instagram using Meta Graph API.
        
        Args:
            post_id: Instagram media ID
        
        Returns:
            Analytics data from Instagram
        """
        import requests
        
        if not self.access_token:
            raise ValueError("Access token required for Instagram analytics")
        
        try:
            # Step 1: Get media insights
            print(f"📊 Fetching Instagram insights for post {post_id}...")
            insights_url = f"https://graph.facebook.com/v19.0/{post_id}/insights"
            
            params = {
                "metric": "engagement,impressions,reach,saved",
                "access_token": self.access_token
            }
            
            response = requests.get(insights_url, params=params, timeout=30)
            response.raise_for_status()
            insights_data = response.json()
            
            # Parse insights data
            metrics = {}
            for insight in insights_data.get("data", []):
                metric_name = insight.get("name")
                metric_value = insight.get("values", [{}])[0].get("value", 0)
                metrics[metric_name] = metric_value
            
            # Step 2: Get additional media details
            media_url = f"https://graph.facebook.com/v19.0/{post_id}"
            media_params = {
                "fields": "like_count,comments_count,timestamp,media_type,media_url,caption",
                "access_token": self.access_token
            }
            
            media_response = requests.get(media_url, params=media_params, timeout=30)
            media_response.raise_for_status()
            media_data = media_response.json()
            
            # Combine data
            impressions = metrics.get("impressions", 0)
            likes = media_data.get("like_count", 0)
            comments = media_data.get("comments_count", 0)
            saved = metrics.get("saved", 0)
            reach = metrics.get("reach", impressions)
            
            # Calculate engagement
            total_engagements = likes + comments + saved
            engagement_rate = (total_engagements / impressions * 100) if impressions > 0 else 0
            
            print(f"✅ Fetched real Instagram analytics: {likes} likes, {comments} comments")
            
            return {
                "post_id": post_id,
                "platform": "instagram",
                "views": impressions,
                "likes": likes,
                "comments": comments,
                "shares": 0,  # Instagram doesn't provide share count via API
                "saves": saved,
                "reach": reach,
                "impressions": impressions,
                "engagement_rate": round(engagement_rate, 2),
                "media_type": media_data.get("media_type"),
                "posted_at": media_data.get("timestamp"),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "source": "instagram_api"
            }
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                # Insights not available yet (post too recent)
                print(f"⚠️  Insights not available yet for post {post_id}")
                return self._generate_mock_analytics(post_id, "instagram")
            else:
                print(f"❌ Instagram API error: {e}")
                raise
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error fetching Instagram analytics: {e}")
            raise
        except Exception as e:
            print(f"❌ Error fetching Instagram analytics: {e}")
            raise
    
    def _fetch_youtube_analytics(self, video_id: str) -> Dict:
        """
        Fetch analytics from YouTube using YouTube Data API
        
        PRODUCTION IMPLEMENTATION:
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            Analytics data from YouTube
        """
        
        """
        # YouTube Data API v3 endpoint
        # Requires YouTube Data API key or OAuth token
        
        import requests
        
        # Get video statistics
        url = "https://www.googleapis.com/youtube/v3/videos"
        
        params = {
            "part": "statistics,snippet",
            "id": video_id,
            "key": self.access_token  # Or use OAuth token
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("items"):
                return {
                    "error": "Video not found",
                    "post_id": video_id,
                    "platform": "youtube"
                }
            
            video_data = data["items"][0]
            stats = video_data.get("statistics", {})
            
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))
            
            # YouTube doesn't provide shares directly
            # Estimate based on engagement patterns
            shares = int(likes * 0.05)
            
            total_engagements = likes + comments + shares
            engagement_rate = (total_engagements / views * 100) if views > 0 else 0
            
            return {
                "post_id": video_id,
                "platform": "youtube",
                "views": views,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "favorites": int(stats.get("favoriteCount", 0)),
                "engagement_rate": round(engagement_rate, 2),
                "title": video_data.get("snippet", {}).get("title"),
                "published_at": video_data.get("snippet", {}).get("publishedAt"),
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching YouTube analytics: {e}")
            return {
                "error": str(e),
                "post_id": video_id,
                "platform": "youtube"
            }
        """
        
        pass
    
    def calculate_performance_score(self, analytics: Dict) -> float:
        """
        Calculate a performance score based on engagement metrics
        
        Args:
            analytics: Analytics dictionary
        
        Returns:
            Performance score (0-100)
        """
        
        engagement_rate = analytics.get("engagement_rate", 0)
        views = analytics.get("views", 0)
        
        # Weighted scoring
        # Engagement rate: 60% weight
        # View count: 40% weight (normalized)
        
        engagement_score = min(engagement_rate * 10, 60)  # Max 60 points
        
        # Normalize views (assuming 10k views = max score)
        view_score = min((views / 10000) * 40, 40)  # Max 40 points
        
        total_score = engagement_score + view_score
        
        return round(min(total_score, 100), 2)
    
    def get_top_performing_posts(self, post_analytics: List[Dict], limit: int = 5) -> List[Dict]:
        """
        Get top performing posts based on engagement metrics
        
        Args:
            post_analytics: List of post analytics
            limit: Number of top posts to return
        
        Returns:
            List of top performing posts with scores
        """
        
        # Calculate performance score for each post
        for analytics in post_analytics:
            analytics["performance_score"] = self.calculate_performance_score(analytics)
        
        # Sort by performance score
        sorted_posts = sorted(
            post_analytics,
            key=lambda x: x.get("performance_score", 0),
            reverse=True
        )
        
        return sorted_posts[:limit]


# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = AnalyticsAgent()
    
    # Fetch single post analytics
    print("=== Single Post Analytics ===")
    post_analytics = agent.fetch_post_analytics("post_123", "instagram")
    print(f"Post ID: {post_analytics['post_id']}")
    print(f"Views: {post_analytics['views']}")
    print(f"Likes: {post_analytics['likes']}")
    print(f"Comments: {post_analytics['comments']}")
    print(f"Engagement Rate: {post_analytics['engagement_rate']}%")
    
    # Fetch campaign analytics
    print("\n=== Campaign Analytics ===")
    campaign_analytics = agent.fetch_campaign_analytics(
        "campaign_456",
        ["post_1", "post_2", "post_3", "post_4", "post_5"]
    )
    print(f"Total Posts: {campaign_analytics['total_posts']}")
    print(f"Total Views: {campaign_analytics['total_views']}")
    print(f"Total Likes: {campaign_analytics['total_likes']}")
    print(f"Overall Engagement Rate: {campaign_analytics['engagement_rate']}%")
    
    # Get top performing posts
    print("\n=== Top Performing Posts ===")
    top_posts = agent.get_top_performing_posts(campaign_analytics['post_analytics'], limit=3)
    for i, post in enumerate(top_posts, 1):
        print(f"{i}. Post {post['post_id']}: Score {post['performance_score']}")
