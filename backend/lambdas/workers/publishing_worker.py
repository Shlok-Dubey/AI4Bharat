"""
Publishing Worker Lambda
Processes scheduled campaigns from SQS queue and publishes to Instagram
"""
import json
import os
import asyncio
from typing import Dict, Any
from datetime import datetime
import sys
import logging

# Add shared directory to path for Lambda imports
sys.path.insert(0, '/opt/python')  # Lambda layer path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from repositories.campaign_repository import CampaignRepository
from repositories.user_repository import UserRepository
from repositories.product_repository import ProductRepository
from shared.services.instagram_service import InstagramService
from shared.services.encryption_service import decrypt_token
from shared.utils.s3_client import S3Client

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def process_campaign_publish(
    campaign_id: str,
    scheduled_time: int
) -> Dict[str, Any]:
    """
    Process a single campaign publishing job.
    
    Workflow:
    1. Check if scheduled_time <= current_time
    2. Atomically update campaign status: scheduled → publishing
    3. Retrieve campaign, user, and product from DynamoDB
    4. Decrypt Instagram token and refresh if needed
    5. Generate S3 presigned URL for image
    6. Publish to Instagram with idempotency check
    7. Update campaign status to "published" with post_id
    8. On failure: Increment publish_attempts, retry or mark failed
    
    Args:
        campaign_id: Campaign ID to publish
        scheduled_time: Scheduled time as Unix timestamp
    
    Returns:
        Result dictionary with status and details
    """
    campaign_repo = CampaignRepository()
    user_repo = UserRepository()
    product_repo = ProductRepository()
    instagram_service = InstagramService()
    s3_client = S3Client()
    
    current_time = int(datetime.utcnow().timestamp())
    
    # Step 1: Check if scheduled time has arrived
    if scheduled_time > current_time:
        logger.info(
            f"Campaign {campaign_id} not ready yet. "
            f"Scheduled: {scheduled_time}, Current: {current_time}"
        )
        return {
            "status": "not_ready",
            "message": "Campaign not ready for publishing yet"
        }
    
    # Step 2: Get campaign to extract user_id for atomic update
    # We need user_id for the atomic status update
    # First, we need to extract user_id from campaign_id or query
    # For now, we'll do a scan to find the campaign (not optimal, but works)
    # In production, the SQS message should include user_id
    
    # For this implementation, we'll assume the message includes user_id
    # If not, we need to query DynamoDB to find it
    # Let's add a helper method to get campaign by ID without user_id
    
    # Since we don't have user_id in the message, we need to scan
    # This is not optimal but necessary for this workflow
    # In production, include user_id in SQS message
    
    logger.error(
        f"Cannot process campaign {campaign_id} without user_id. "
        "SQS message must include user_id field."
    )
    return {
        "status": "error",
        "message": "user_id required in message"
    }


async def process_campaign_publish_with_user_id(
    user_id: str,
    campaign_id: str,
    scheduled_time: int
) -> Dict[str, Any]:
    """
    Process campaign publishing with user_id provided.
    
    Args:
        user_id: User ID (for tenant isolation)
        campaign_id: Campaign ID to publish
        scheduled_time: Scheduled time as Unix timestamp
    
    Returns:
        Result dictionary with status and details
    """
    campaign_repo = CampaignRepository()
    user_repo = UserRepository()
    product_repo = ProductRepository()
    instagram_service = InstagramService()
    s3_client = S3Client()
    
    current_time = int(datetime.utcnow().timestamp())
    
    # Step 1: Check if scheduled time has arrived
    if scheduled_time > current_time:
        logger.info(
            f"Campaign {campaign_id} not ready yet. "
            f"Scheduled: {scheduled_time}, Current: {current_time}"
        )
        return {
            "status": "not_ready",
            "message": "Campaign not ready for publishing yet"
        }
    
    # Step 2: Atomically update campaign status: scheduled → publishing
    success = await campaign_repo.atomic_status_update(
        user_id=user_id,
        campaign_id=campaign_id,
        old_status="scheduled",
        new_status="publishing"
    )
    
    if not success:
        logger.warning(
            f"Campaign {campaign_id} status update failed. "
            "Already processed or status changed."
        )
        return {
            "status": "already_processed",
            "message": "Campaign already processed or status changed"
        }
    
    logger.info(f"Campaign {campaign_id} status updated to 'publishing'")
    
    try:
        # Step 3: Retrieve campaign from DynamoDB
        campaign = await campaign_repo.get_by_id(user_id, campaign_id)
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            return {
                "status": "error",
                "message": "Campaign not found"
            }
        
        # Step 4: Retrieve user from DynamoDB
        user = await user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            raise ValueError(f"User {user_id} not found")
        
        # Check if user has Instagram connected
        if not user.instagram_access_token or not user.instagram_user_id:
            logger.error(f"User {user_id} has no Instagram connection")
            raise ValueError("Instagram not connected")
        
        # Step 5: Decrypt Instagram token
        access_token = await decrypt_token(user.instagram_access_token)
        
        # Step 6: Check token expiry and refresh if needed
        if user.instagram_token_expires_at:
            if instagram_service.is_token_expired(user.instagram_token_expires_at):
                logger.info(f"Instagram token expired for user {user_id}, refreshing")
                from shared.services.instagram_service import refresh_instagram_token
                refresh_success = await refresh_instagram_token(user_id, user_repo)
                if not refresh_success:
                    raise ValueError("Failed to refresh Instagram token")
                
                # Re-fetch user to get updated token
                user = await user_repo.get_by_id(user_id)
                access_token = await decrypt_token(user.instagram_access_token)
        
        # Step 7: Retrieve product from DynamoDB
        product = await product_repo.get_by_id(user_id, campaign.product_id)
        if not product:
            logger.error(f"Product {campaign.product_id} not found")
            raise ValueError(f"Product {campaign.product_id} not found")
        
        # Step 8: Generate S3 presigned URL for image (5 min expiry)
        image_url = await s3_client.generate_presigned_url(
            key=product.image_s3_key,
            expiry_seconds=300
        )
        
        logger.info(f"Generated presigned URL for product {product.product_id}")
        
        # Step 9: Prepare caption with hashtags
        caption_with_hashtags = campaign.caption
        if campaign.hashtags:
            caption_with_hashtags += "\n\n" + " ".join(campaign.hashtags)
        
        # Step 10: Publish to Instagram with idempotency check
        post_id = await instagram_service.publish_with_idempotency_check(
            campaign_id=campaign_id,
            existing_post_id=campaign.instagram_post_id,
            access_token=access_token,
            instagram_user_id=user.instagram_user_id,
            image_url=image_url,
            caption=caption_with_hashtags
        )
        
        logger.info(f"Published campaign {campaign_id} to Instagram: {post_id}")
        
        # Step 11: Update campaign status to "published"
        campaign.status = "published"
        campaign.instagram_post_id = post_id
        campaign.published_at = datetime.utcnow()
        campaign.updated_at = datetime.utcnow()
        
        await campaign_repo.update(campaign)
        
        logger.info(f"Campaign {campaign_id} successfully published")
        
        return {
            "status": "success",
            "campaign_id": campaign_id,
            "instagram_post_id": post_id
        }
        
    except Exception as e:
        logger.error(f"Error publishing campaign {campaign_id}: {e}", exc_info=True)
        
        # Step 12: Handle failure - increment publish_attempts
        try:
            campaign = await campaign_repo.get_by_id(user_id, campaign_id)
            if campaign:
                campaign.publish_attempts += 1
                campaign.last_error = str(e)
                campaign.updated_at = datetime.utcnow()
                
                # Check if max attempts reached
                if campaign.publish_attempts >= 3:
                    logger.error(
                        f"Campaign {campaign_id} failed after {campaign.publish_attempts} attempts"
                    )
                    campaign.status = "failed"
                else:
                    logger.warning(
                        f"Campaign {campaign_id} failed, attempt {campaign.publish_attempts}/3. "
                        "Will retry."
                    )
                    campaign.status = "scheduled"  # Reset to scheduled for retry
                
                await campaign_repo.update(campaign)
        except Exception as update_error:
            logger.error(f"Failed to update campaign after error: {update_error}")
        
        # Re-raise exception for SQS retry
        if campaign and campaign.publish_attempts < 3:
            raise  # Let SQS retry
        
        return {
            "status": "failed",
            "campaign_id": campaign_id,
            "error": str(e)
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for SQS-triggered campaign publishing.
    
    Expected SQS message format:
    {
        "user_id": "user-uuid",
        "campaign_id": "campaign-uuid",
        "scheduled_time": 1234567890
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "processed": 1,
            "failed": 0
        }
    }
    
    Requirements: 6.3, 7.1, 7.5, 9.2, 9.3, 9.4, 9.5, 18.2, 21.1, 21.2, 21.3
    """
    logger.info(f"Publishing worker triggered with {len(event.get('Records', []))} messages")
    
    processed = 0
    failed = 0
    
    for record in event.get('Records', []):
        # Extract message metadata for DLQ logging
        message_id = record.get('messageId')
        receipt_handle = record.get('receiptHandle')
        approximate_receive_count = int(
            record.get('attributes', {}).get('ApproximateReceiveCount', 0)
        )
        
        try:
            # Parse SQS message body
            message_body = json.loads(record['body'])
            
            user_id = message_body.get('user_id')
            campaign_id = message_body.get('campaign_id')
            scheduled_time = message_body.get('scheduled_time')
            
            if not all([user_id, campaign_id, scheduled_time]):
                logger.error(
                    json.dumps({
                        "event": "invalid_message_format",
                        "message_id": message_id,
                        "retry_count": approximate_receive_count,
                        "payload": message_body,
                        "error": "Missing required fields: user_id, campaign_id, scheduled_time"
                    })
                )
                failed += 1
                continue
            
            logger.info(
                json.dumps({
                    "event": "processing_campaign",
                    "campaign_id": campaign_id,
                    "user_id": user_id,
                    "scheduled_time": scheduled_time,
                    "retry_count": approximate_receive_count,
                    "message_id": message_id
                })
            )
            
            # Process campaign publishing
            result = asyncio.run(process_campaign_publish_with_user_id(
                user_id=user_id,
                campaign_id=campaign_id,
                scheduled_time=scheduled_time
            ))
            
            if result['status'] in ['success', 'already_processed', 'not_ready']:
                processed += 1
                logger.info(
                    json.dumps({
                        "event": "campaign_processed",
                        "campaign_id": campaign_id,
                        "status": result['status'],
                        "retry_count": approximate_receive_count
                    })
                )
            else:
                failed += 1
                logger.error(
                    json.dumps({
                        "event": "campaign_failed",
                        "campaign_id": campaign_id,
                        "status": result['status'],
                        "error": result.get('message'),
                        "retry_count": approximate_receive_count
                    })
                )
                
        except Exception as e:
            failed += 1
            
            # Log failure with full context for DLQ investigation
            logger.error(
                json.dumps({
                    "event": "processing_exception",
                    "message_id": message_id,
                    "retry_count": approximate_receive_count,
                    "payload": record.get('body'),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "will_move_to_dlq": approximate_receive_count >= 3
                })
            )
            
            # Log to CloudWatch with structured format for DLQ monitoring
            if approximate_receive_count >= 3:
                logger.critical(
                    json.dumps({
                        "event": "message_moving_to_dlq",
                        "message_id": message_id,
                        "retry_count": approximate_receive_count,
                        "failure_reason": str(e),
                        "payload": record.get('body'),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )
            
            # Re-raise to trigger SQS retry
            raise
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "processed": processed,
            "failed": failed
        })
    }
