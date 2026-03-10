"""
Analytics Agent Module

Purpose: Analyze engagement metrics for published posts from DynamoDB
Metrics: impressions, reach, likes, comments, saves, shares, engagement_rate

Reads analytics data stored by analytics_job.py
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
import dynamodb_client as db


class AnalyticsAgent:
    """
    Agent responsible for analyzing post engagement metrics from DynamoDB
    """
    
    def __init__(self):
        """
        Initialize Analytics Agent
        """
        pass
    
    def fetch_post_analytics(self, post_id: str) -> Optional[Dict]:
        """
        Fetch analytics for a specific scheduled post from DynamoDB.
        
        Args:
            post_id: Scheduled post ID
        
        Returns:
            Dictionary containing engagement metrics or None if not found
        """
        analytics = db.get_post_analytics(post_id)
        
        if not analytics:
            return None
        
        # Calculate engagement rate if not already calculated
        impressions = analytics.get('impressions', 0)
        likes = analytics.get('likes', 0)
        comments = analytics.get('comments', 0)
        saves = analytics.get('saves', 0)
        shares = analytics.get('shares', 0)
        
        total_engagements = likes + comments + saves + shares
        engagement_rate = (total_engagements / impressions * 100) if impressions > 0 else 0
        
        return {
            'post_id': post_id,
            'impressions': impressions,
            'reach': analytics.get('reach', 0),
            'likes': likes,
            'comments': comments,
            'saves': saves,
            'shares': shares,
            'engagement_rate': round(engagement_rate, 2),
            'fetched_at': analytics.get('fetched_at')
        }
    
    def fetch_campaign_analytics(self, campaign_id: str) -> Dict:
        """
        Fetch aggregated analytics for an entire campaign from DynamoDB
        
        Args:
            campaign_id: Campaign identifier
        
        Returns:
            Aggregated metrics for the campaign
        """
        # Get all content for this campaign
        content_list = db.get_generated_content_by_campaign(campaign_id, status='approved')
        
        if not content_list:
            return {
                'campaign_id': campaign_id,
                'total_posts': 0,
                'message': 'No approved content found for this campaign'
            }
        
        total_impressions = 0
        total_reach = 0
        total_likes = 0
        total_comments = 0
        total_saves = 0
        total_shares = 0
        post_analytics = []
        posts_with_analytics = 0
        
        for content in content_list:
            content_id = content['content_id']
            
            # Get scheduled posts for this content
            scheduled_posts = db.get_scheduled_posts_by_content(content_id)
            
            for scheduled_post in scheduled_posts:
                if scheduled_post.get('status') != 'posted':
                    continue
                
                post_id = scheduled_post['post_id']
                analytics = self.fetch_post_analytics(post_id)
                
                if analytics:
                    post_analytics.append(analytics)
                    posts_with_analytics += 1
                    
                    total_impressions += analytics.get('impressions', 0)
                    total_reach += analytics.get('reach', 0)
                    total_likes += analytics.get('likes', 0)
                    total_comments += analytics.get('comments', 0)
                    total_saves += analytics.get('saves', 0)
                    total_shares += analytics.get('shares', 0)
        
        # Calculate overall engagement rate
        total_engagements = total_likes + total_comments + total_saves + total_shares
        engagement_rate = (total_engagements / total_impressions * 100) if total_impressions > 0 else 0
        
        return {
            'campaign_id': campaign_id,
            'total_posts': len(content_list),
            'posts_with_analytics': posts_with_analytics,
            'total_impressions': total_impressions,
            'total_reach': total_reach,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_saves': total_saves,
            'total_shares': total_shares,
            'total_engagements': total_engagements,
            'engagement_rate': round(engagement_rate, 2),
            'average_impressions_per_post': round(total_impressions / posts_with_analytics, 2) if posts_with_analytics > 0 else 0,
            'post_analytics': post_analytics,
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }
    
    def get_performance_summary(self, campaign_id: str) -> Dict:
        """
        Generate a performance summary for a campaign with insights
        
        Args:
            campaign_id: Campaign identifier
        
        Returns:
            Performance summary with insights and recommendations
        """
        analytics = self.fetch_campaign_analytics(campaign_id)
        
        if analytics.get('posts_with_analytics', 0) == 0:
            return {
                'campaign_id': campaign_id,
                'status': 'no_data',
                'message': 'No analytics data available yet. Posts may be too recent or not yet published.'
            }
        
        # Get top performing posts
        top_posts = self.get_top_performing_posts(analytics.get('post_analytics', []), limit=3)
        
        # Generate insights
        insights = []
        engagement_rate = analytics.get('engagement_rate', 0)
        
        if engagement_rate > 5:
            insights.append('Excellent engagement rate! Your content is resonating well with your audience.')
        elif engagement_rate > 3:
            insights.append('Good engagement rate. Consider testing different content formats to improve further.')
        elif engagement_rate > 1:
            insights.append('Moderate engagement. Try posting at different times or experimenting with content style.')
        else:
            insights.append('Low engagement detected. Consider revising your content strategy and posting schedule.')
        
        # Analyze saves vs likes ratio
        total_saves = analytics.get('total_saves', 0)
        total_likes = analytics.get('total_likes', 0)
        if total_likes > 0:
            save_ratio = (total_saves / total_likes) * 100
            if save_ratio > 20:
                insights.append('High save rate indicates valuable content that users want to reference later.')
        
        # Analyze reach vs impressions
        total_reach = analytics.get('total_reach', 0)
        total_impressions = analytics.get('total_impressions', 0)
        if total_impressions > 0:
            reach_ratio = (total_reach / total_impressions) * 100
            if reach_ratio < 50:
                insights.append('Low reach-to-impression ratio. Consider using more relevant hashtags to expand reach.')
        
        return {
            'campaign_id': campaign_id,
            'status': 'success',
            'summary': {
                'total_posts': analytics.get('total_posts', 0),
                'posts_analyzed': analytics.get('posts_with_analytics', 0),
                'total_impressions': analytics.get('total_impressions', 0),
                'total_engagements': analytics.get('total_engagements', 0),
                'engagement_rate': analytics.get('engagement_rate', 0),
                'average_impressions': analytics.get('average_impressions_per_post', 0)
            },
            'top_performing_posts': top_posts,
            'insights': insights,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
    
    def calculate_performance_score(self, analytics: Dict) -> float:
        """
        Calculate a performance score based on engagement metrics
        
        Args:
            analytics: Analytics dictionary
        
        Returns:
            Performance score (0-100)
        """
        engagement_rate = analytics.get('engagement_rate', 0)
        impressions = analytics.get('impressions', 0)
        
        # Weighted scoring
        # Engagement rate: 60% weight
        # Impression count: 40% weight (normalized)
        
        engagement_score = min(engagement_rate * 10, 60)  # Max 60 points
        
        # Normalize impressions (assuming 10k impressions = max score)
        impression_score = min((impressions / 10000) * 40, 40)  # Max 40 points
        
        total_score = engagement_score + impression_score
        
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
        if not post_analytics:
            return []
        
        # Calculate performance score for each post
        for analytics in post_analytics:
            analytics['performance_score'] = self.calculate_performance_score(analytics)
        
        # Sort by performance score
        sorted_posts = sorted(
            post_analytics,
            key=lambda x: x.get('performance_score', 0),
            reverse=True
        )
        
        return sorted_posts[:limit]


# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = AnalyticsAgent()
    
    # Example: Fetch campaign analytics
    print("=== Campaign Analytics ===")
    campaign_id = "your-campaign-id"
    
    try:
        campaign_analytics = agent.fetch_campaign_analytics(campaign_id)
        print(f"Campaign ID: {campaign_analytics['campaign_id']}")
        print(f"Total Posts: {campaign_analytics.get('total_posts', 0)}")
        print(f"Posts with Analytics: {campaign_analytics.get('posts_with_analytics', 0)}")
        print(f"Total Impressions: {campaign_analytics.get('total_impressions', 0)}")
        print(f"Total Engagements: {campaign_analytics.get('total_engagements', 0)}")
        print(f"Engagement Rate: {campaign_analytics.get('engagement_rate', 0)}%")
        
        # Get performance summary
        print("\n=== Performance Summary ===")
        summary = agent.get_performance_summary(campaign_id)
        print(f"Status: {summary.get('status')}")
        if summary.get('status') == 'success':
            print(f"Insights:")
            for insight in summary.get('insights', []):
                print(f"  - {insight}")
    except Exception as e:
        print(f"Error: {e}")
