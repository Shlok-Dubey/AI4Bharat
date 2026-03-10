"""
Analytics Fetching Job

Periodically fetches Instagram analytics for published posts.
Run this as a scheduled task (cron) every 12 hours.

Usage:
    python analytics_job.py
"""

import dynamodb_client as db
import requests
from datetime import datetime
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_instagram_insights(post_id: str, access_token: str) -> Optional[Dict]:
    """
    Fetch insights for a specific Instagram post.
    
    Args:
        post_id: Instagram media ID
        access_token: Instagram access token
    
    Returns:
        Dict with metrics or None if failed
    """
    url = f"https://graph.facebook.com/v19.0/{post_id}/insights"
    params = {
        "metric": "impressions,reach,likes,comments,saves,shares",
        "access_token": access_token
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch insights for {post_id}: {response.text}")
            return None
        
        data = response.json()
        
        # Parse metrics
        metrics = {}
        for item in data.get('data', []):
            metric_name = item.get('name')
            metric_value = item.get('values', [{}])[0].get('value', 0)
            metrics[metric_name] = metric_value
        
        # Also fetch basic post data for likes/comments
        post_url = f"https://graph.facebook.com/v19.0/{post_id}"
        post_params = {
            "fields": "like_count,comments_count",
            "access_token": access_token
        }
        
        post_response = requests.get(post_url, params=post_params, timeout=30)
        if post_response.status_code == 200:
            post_data = post_response.json()
            metrics['likes'] = post_data.get('like_count', 0)
            metrics['comments'] = post_data.get('comments_count', 0)
        
        return {
            'impressions': metrics.get('impressions', 0),
            'reach': metrics.get('reach', 0),
            'likes': metrics.get('likes', 0),
            'comments': metrics.get('comments', 0),
            'saves': metrics.get('saves', 0),
            'shares': metrics.get('shares', 0)
        }
        
    except Exception as e:
        logger.error(f"Error fetching insights for {post_id}: {e}")
        return None


def store_analytics(post_id: str, metrics: Dict):
    """
    Store analytics in DynamoDB.
    
    Args:
        post_id: Scheduled post ID
        metrics: Analytics metrics
    """
    try:
        # Check if analytics already exist
        existing = db.get_post_analytics(post_id)
        
        if existing:
            # Update existing analytics
            db.update_post_analytics(
                existing['analytics_id'],
                impressions=metrics['impressions'],
                reach=metrics['reach'],
                likes=metrics['likes'],
                comments=metrics['comments'],
                saves=metrics['saves'],
                shares=metrics.get('shares', 0)
            )
            logger.info(f"✅ Updated analytics for post {post_id}")
        else:
            # Create new analytics record
            db.create_post_analytics(
                post_id=post_id,
                impressions=metrics['impressions'],
                reach=metrics['reach'],
                likes=metrics['likes'],
                comments=metrics['comments'],
                saves=metrics['saves'],
                shares=metrics.get('shares', 0)
            )
            logger.info(f"✅ Created analytics for post {post_id}")
            
    except Exception as e:
        logger.error(f"Failed to store analytics for {post_id}: {e}")


def fetch_all_analytics():
    """
    Main job function - fetch analytics for all published posts.
    """
    logger.info("🚀 Starting analytics fetch job...")
    
    try:
        # Get all published posts
        response = db.scheduled_posts_table.scan(
            FilterExpression='#status = :status AND attribute_exists(platform_post_id)',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'posted'}
        )
        
        posts = [db.dynamodb_to_python(item) for item in response.get('Items', [])]
        
        logger.info(f"📊 Found {len(posts)} published posts")
        
        if not posts:
            logger.info("No posts to fetch analytics for")
            return
        
        success_count = 0
        failed_count = 0
        
        for post in posts:
            post_id = post['post_id']
            platform_post_id = post.get('platform_post_id')
            
            if not platform_post_id:
                logger.warning(f"⚠️  Post {post_id} has no platform_post_id")
                continue
            
            # Get content to find campaign and user
            content_id = post.get('content_id')
            if not content_id:
                logger.warning(f"⚠️  Post {post_id} has no content_id")
                continue
            
            content = db.get_generated_content(content_id)
            if not content:
                logger.warning(f"⚠️  Content {content_id} not found")
                continue
            
            # Get campaign to find user
            campaign_id = content.get('campaign_id')
            if not campaign_id:
                logger.warning(f"⚠️  Content {content_id} has no campaign_id")
                continue
            
            campaign = db.get_campaign(campaign_id)
            if not campaign:
                logger.warning(f"⚠️  Campaign {campaign_id} not found")
                continue
            
            # Get OAuth account for access token
            user_id = campaign.get('user_id')
            oauth_account = db.get_oauth_account_by_provider(user_id, 'meta')
            
            if not oauth_account:
                logger.warning(f"⚠️  No Instagram OAuth for user {user_id}")
                continue
            
            access_token = oauth_account.get('access_token')
            
            # Fetch insights
            logger.info(f"📈 Fetching insights for post {post_id} (Instagram: {platform_post_id})")
            metrics = fetch_instagram_insights(platform_post_id, access_token)
            
            if metrics:
                # Store in DynamoDB
                store_analytics(post_id, metrics)
                success_count += 1
            else:
                failed_count += 1
        
        logger.info(f"✅ Analytics fetch complete: {success_count} success, {failed_count} failed")
        
        return {
            'total_posts': len(posts),
            'success': success_count,
            'failed': failed_count
        }
        
    except Exception as e:
        logger.error(f"❌ Analytics job failed: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


if __name__ == "__main__":
    result = fetch_all_analytics()
    logger.info(f"Job result: {result}")
