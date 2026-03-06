"""
Campaign scheduling service for SQS queue management.

Handles campaign scheduling by sending messages to SQS queue with appropriate delays.

Requirements: 6.2
"""

import logging
from datetime import datetime
from typing import Optional

from shared.utils.sqs_client import SQSClient

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling campaigns via SQS."""
    
    def __init__(self):
        """Initialize SchedulerService with SQS client."""
        self.sqs_client = SQSClient()
    
    async def schedule_campaign(
        self,
        campaign_id: str,
        user_id: str,
        scheduled_time: datetime
    ) -> str:
        """
        Schedule a campaign for publishing by sending message to SQS queue.
        
        If delay > 900 seconds (15 minutes), sets delay to 0 and worker will check time.
        Uses campaign_id for message deduplication to prevent duplicate scheduling.
        
        Args:
            campaign_id: Campaign ID to schedule
            user_id: User ID (for tenant isolation)
            scheduled_time: When to publish the campaign
            
        Returns:
            SQS message ID
            
        Raises:
            ClientError: If SQS message send fails
            
        Requirements: 6.2
        """
        # Calculate delay in seconds
        now = datetime.utcnow()
        delay_seconds = int((scheduled_time - now).total_seconds())
        
        # SQS max delay is 900 seconds (15 minutes)
        # If delay > 900, set to 0 and worker will check scheduled_time
        if delay_seconds > 900:
            delay_seconds = 0
            logger.info(
                f"Campaign {campaign_id} scheduled for {scheduled_time.isoformat()}, "
                f"delay > 15 min, worker will check time"
            )
        elif delay_seconds < 0:
            # If scheduled time is in the past, send immediately
            delay_seconds = 0
            logger.warning(
                f"Campaign {campaign_id} scheduled time {scheduled_time.isoformat()} is in the past, "
                f"sending immediately"
            )
        
        # Create message payload
        message_body = {
            "campaign_id": campaign_id,
            "user_id": user_id,
            "scheduled_time": scheduled_time.isoformat(),
        }
        
        # Send message to SQS with deduplication
        message_id = await self.sqs_client.send_message(
            message_body=message_body,
            deduplication_id=campaign_id,  # Use campaign_id for deduplication
            delay_seconds=delay_seconds
        )
        
        logger.info(
            f"Campaign {campaign_id} scheduled successfully, "
            f"message_id: {message_id}, delay: {delay_seconds}s"
        )
        
        return message_id
    
    async def cancel_campaign(self, campaign_id: str) -> bool:
        """
        Attempt to remove a scheduled campaign from the queue (best effort).
        
        Note: This is a best-effort operation. If the message is already being processed
        or has been delivered, it cannot be removed. The worker should check campaign
        status before publishing.
        
        Args:
            campaign_id: Campaign ID to cancel
            
        Returns:
            True if cancellation was attempted (does not guarantee message was removed)
            
        Requirements: 6.5
        """
        # Note: SQS doesn't provide a direct way to delete a message by deduplication ID
        # The worker must check campaign status before publishing
        # This is a placeholder for future implementation if needed
        
        logger.info(
            f"Campaign {campaign_id} cancellation requested. "
            f"Worker will check status before publishing."
        )
        
        # In a production system, you might:
        # 1. Use a separate tracking table to mark campaigns as cancelled
        # 2. Have the worker check campaign status before publishing
        # 3. Use SQS message attributes to filter cancelled campaigns
        
        return True
