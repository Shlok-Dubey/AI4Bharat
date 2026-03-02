"""
Analytics repository for DynamoDB operations.

Handles all analytics-related database operations.
"""

from typing import List
from datetime import datetime
from botocore.exceptions import ClientError
import logging

from repositories.base import BaseRepository
from shared.models.domain import Analytics

logger = logging.getLogger(__name__)


class AnalyticsRepository(BaseRepository):
    """Repository for Analytics entity operations."""
    
    def __init__(self, table_name: str = "analytics"):
        """Initialize AnalyticsRepository."""
        super().__init__(table_name)
    
    async def create(self, analytics: Analytics) -> Analytics:
        """
        Create a new analytics record in DynamoDB.
        
        Args:
            analytics: Analytics domain model
            
        Returns:
            Created Analytics
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            item = analytics.to_dynamodb_item()
            
            try:
                await table.put_item(Item=item)
                logger.info(f"Created analytics for campaign: {analytics.campaign_id}")
                return analytics
            except ClientError as e:
                logger.error(f"Error creating analytics for campaign {analytics.campaign_id}: {e}")
                raise
    
    async def get_by_campaign(self, campaign_id: str) -> List[Analytics]:
        """
        Get all analytics records for a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            List of Analytics records ordered by timestamp
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                response = await table.query(
                    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                    ExpressionAttributeValues={
                        ':pk': f'CAMPAIGN#{campaign_id}',
                        ':sk_prefix': 'ANALYTICS#'
                    },
                    ScanIndexForward=True  # Sort by SK (timestamp) ascending
                )
                
                analytics_list = [Analytics.from_dynamodb_item(item) for item in response['Items']]
                
                logger.info(f"Retrieved {len(analytics_list)} analytics records for campaign: {campaign_id}")
                return analytics_list
            except ClientError as e:
                logger.error(f"Error getting analytics for campaign {campaign_id}: {e}")
                raise
    
    async def get_by_user_and_date_range(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Analytics]:
        """
        Get all analytics records for a user within a date range.
        
        Args:
            user_id: User ID
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of Analytics records
            
        Note:
            In production, this requires a GSI with:
            - PK: user_id
            - SK: fetched_at
            For now, we'll scan with filter (not optimal).
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                start_timestamp = int(start_date.timestamp())
                end_timestamp = int(end_date.timestamp())
                
                # For now, scan with filter (not optimal for production)
                # In production, use GSI query
                response = await table.scan(
                    FilterExpression='user_id = :user_id AND fetched_at BETWEEN :start_date AND :end_date',
                    ExpressionAttributeValues={
                        ':user_id': user_id,
                        ':start_date': start_timestamp,
                        ':end_date': end_timestamp
                    }
                )
                
                analytics_list = [Analytics.from_dynamodb_item(item) for item in response['Items']]
                
                # Sort by fetched_at
                analytics_list.sort(key=lambda x: x.fetched_at)
                
                logger.info(f"Retrieved {len(analytics_list)} analytics records for user: {user_id}")
                return analytics_list
            except ClientError as e:
                logger.error(f"Error getting analytics for user {user_id}: {e}")
                raise
