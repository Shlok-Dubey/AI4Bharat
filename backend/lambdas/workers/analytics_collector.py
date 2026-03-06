"""
Analytics Collector Lambda

Fetches Instagram insights for published campaigns.
Triggered by EventBridge (every 6 hours).

Requirements: 8.1, 8.4
"""

import json
import logging
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
import boto3

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import shared modules
import sys
sys.path.insert(0, '/opt/python')  # Lambda layer path

from shared.services.instagram_service import InstagramService
from shared.services.analytics_service import AnalyticsService
from shared.services.encryption_service import decrypt_token
from repositories.campaign_repository import CampaignRepository
from repositories.user_repository import UserRepository
from shared.models.domain import Campaign

# Initialize Lambda client for invoking Performance Learning Lambda
lambda_client = boto3.client('lambda')


async def process_campaigns():
    """
    Process published campaigns and fetch analytics.
    
    Requirements: 8.1, 8.4
    """
    campaign_repo = CampaignRepository()
    user_repo = UserRepository()
    instagram_service = InstagramService()
    analytics_service = AnalyticsService()
    
    # Query DynamoDB for published campaigns with last_analytics_fetch > 24h ago
    # or campaigns that have never been fetched
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    
    logger.info(f"Fetching campaigns with analytics older than {cutoff_time}")
    
    # Get all published campaigns (we'll filter by last_analytics_fetch)
    # Note: In production, this should use a GSI for efficient querying
    # For now, we'll scan and filter
    all_campaigns = await campaign_repo.get_all_published_campaigns()
    
    campaigns_to_process = [
        campaign for campaign in all_campaigns
        if (
            campaign.instagram_post_id and
            (
                campaign.last_analytics_fetch is None or
                campaign.last_analytics_fetch < cutoff_time
            )
        )
    ]
    
    logger.info(f"Found {len(campaigns_to_process)} campaigns to process")
    
    processed_count = 0
    error_count = 0
    
    for campaign in campaigns_to_process:
        try:
            # Get user to retrieve Instagram token
            user = await user_repo.get_by_id(campaign.user_id)
            if not user or not user.instagram_access_token:
                logger.warning(
                    f"User {campaign.user_id} has no Instagram token, "
                    f"skipping campaign {campaign.campaign_id}"
                )
                continue
            
            # Decrypt Instagram token
            access_token = await decrypt_token(user.instagram_access_token)
            
            # Fetch insights from Instagram
            insights = await instagram_service.fetch_insights(
                access_token=access_token,
                post_id=campaign.instagram_post_id
            )
            
            # Store analytics in DynamoDB
            await analytics_service.store_analytics(
                campaign_id=campaign.campaign_id,
                user_id=campaign.user_id,
                likes=insights.likes,
                comments=insights.comments,
                reach=insights.reach,
                impressions=insights.impressions,
                engagement_rate=insights.engagement_rate
            )
            
            # Update campaign.last_analytics_fetch timestamp
            campaign.last_analytics_fetch = datetime.utcnow()
            campaign.updated_at = datetime.utcnow()
            await campaign_repo.update(campaign)
            
            processed_count += 1
            logger.info(
                f"Processed analytics for campaign {campaign.campaign_id}: "
                f"engagement_rate={insights.engagement_rate:.2f}%"
            )
            
            # Invoke Performance Learning Lambda asynchronously
            try:
                performance_learning_function = os.getenv(
                    'PERFORMANCE_LEARNING_FUNCTION_NAME',
                    'performance-learning-lambda'
                )
                
                lambda_client.invoke(
                    FunctionName=performance_learning_function,
                    InvocationType='Event',  # Async invocation
                    Payload=json.dumps({
                        'campaign_id': campaign.campaign_id,
                        'user_id': campaign.user_id
                    })
                )
                
                logger.info(
                    f"Invoked Performance Learning Lambda for campaign {campaign.campaign_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to invoke Performance Learning Lambda for campaign {campaign.campaign_id}: {e}",
                    exc_info=True
                )
                # Don't fail the whole process if learning invocation fails
            
        except Exception as e:
            error_count += 1
            logger.error(
                f"Error processing campaign {campaign.campaign_id}: {e}",
                exc_info=True
            )
            continue
    
    logger.info(
        f"Analytics collection complete: "
        f"processed={processed_count}, errors={error_count}"
    )
    
    return {
        'processed': processed_count,
        'errors': error_count,
        'total_campaigns': len(campaigns_to_process)
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for analytics collection.
    
    Triggered by EventBridge (every 6 hours).
    
    Requirements: 8.1, 8.4
    """
    logger.info("Analytics Collector Lambda triggered")
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        # Run async processing
        import asyncio
        result = asyncio.run(process_campaigns())
        
        logger.info(f"Analytics collection result: {result}")
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Analytics collection completed",
                "result": result
            })
        }
        
    except Exception as e:
        logger.error(f"Analytics collection failed: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "message": "Analytics collection failed"
            })
        }
