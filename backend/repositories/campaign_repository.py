"""
Campaign repository for DynamoDB operations.

Handles all campaign-related database operations with tenant isolation.
"""

from typing import Optional, List
from datetime import datetime
from botocore.exceptions import ClientError
import logging

from repositories.base import BaseRepository
from shared.models.domain import Campaign

logger = logging.getLogger(__name__)


class CampaignRepository(BaseRepository):
    """Repository for Campaign entity operations."""
    
    def __init__(self, table_name: str = "campaigns"):
        """Initialize CampaignRepository."""
        super().__init__(table_name)
    
    async def create(self, campaign: Campaign) -> Campaign:
        """
        Create a new campaign in DynamoDB.
        
        Args:
            campaign: Campaign domain model
            
        Returns:
            Created Campaign
            
        Raises:
            ClientError: If campaign already exists or DynamoDB error occurs
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            item = campaign.to_dynamodb_item()
            
            try:
                await table.put_item(
                    Item=item,
                    ConditionExpression='attribute_not_exists(PK) AND attribute_not_exists(SK)'
                )
                logger.info(f"Created campaign: {campaign.campaign_id} for user: {campaign.user_id}")
                return campaign
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    logger.error(f"Campaign already exists: {campaign.campaign_id}")
                    raise ValueError(f"Campaign with ID {campaign.campaign_id} already exists")
                raise
    
    async def get_by_id(self, user_id: str, campaign_id: str) -> Optional[Campaign]:
        """
        Get campaign by ID with tenant isolation.
        
        Args:
            user_id: User ID (for tenant isolation)
            campaign_id: Campaign ID
            
        Returns:
            Campaign if found, None otherwise
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                response = await table.get_item(
                    Key={
                        'PK': f'USER#{user_id}',
                        'SK': f'CAMPAIGN#{campaign_id}'
                    }
                )
                
                if 'Item' in response:
                    return Campaign.from_dynamodb_item(response['Item'])
                return None
            except ClientError as e:
                logger.error(f"Error getting campaign {campaign_id} for user {user_id}: {e}")
                raise
    
    async def get_by_user(self, user_id: str, status: Optional[str] = None) -> List[Campaign]:
        """
        Get all campaigns for a user with tenant isolation.
        
        Args:
            user_id: User ID
            status: Optional status filter
            
        Returns:
            List of Campaigns
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                query_params = {
                    'KeyConditionExpression': 'PK = :pk AND begins_with(SK, :sk_prefix)',
                    'ExpressionAttributeValues': {
                        ':pk': f'USER#{user_id}',
                        ':sk_prefix': 'CAMPAIGN#'
                    }
                }
                
                # Add status filter if provided
                if status:
                    query_params['FilterExpression'] = '#status = :status'
                    query_params['ExpressionAttributeNames'] = {'#status': 'status'}
                    query_params['ExpressionAttributeValues'][':status'] = status
                
                response = await table.query(**query_params)
                
                campaigns = [Campaign.from_dynamodb_item(item) for item in response['Items']]
                
                logger.info(f"Retrieved {len(campaigns)} campaigns for user: {user_id}")
                return campaigns
            except ClientError as e:
                logger.error(f"Error getting campaigns for user {user_id}: {e}")
                raise
    
    async def atomic_status_update(
        self,
        user_id: str,
        campaign_id: str,
        old_status: str,
        new_status: str
    ) -> bool:
        """
        Atomically update campaign status using conditional update.
        
        This ensures that status transitions are atomic and prevents race conditions
        in distributed systems (e.g., multiple Lambda workers).
        
        Args:
            user_id: User ID (for tenant isolation)
            campaign_id: Campaign ID
            old_status: Expected current status
            new_status: New status to set
            
        Returns:
            True if update succeeded, False if condition failed
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                await table.update_item(
                    Key={
                        'PK': f'USER#{user_id}',
                        'SK': f'CAMPAIGN#{campaign_id}'
                    },
                    UpdateExpression='SET #status = :new_status, updated_at = :updated_at',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':old_status': old_status,
                        ':new_status': new_status,
                        ':updated_at': int(datetime.utcnow().timestamp())
                    },
                    ConditionExpression='#status = :old_status'
                )
                logger.info(f"Atomically updated campaign {campaign_id} status: {old_status} -> {new_status}")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    logger.warning(f"Campaign {campaign_id} status update failed: expected {old_status}, got different value")
                    return False
                raise
    
    async def get_scheduled(self, limit: int = 100) -> List[Campaign]:
        """
        Get scheduled campaigns ready for publishing.
        
        This method uses a GSI on status and scheduled_time for efficient querying.
        
        Args:
            limit: Maximum number of campaigns to retrieve
            
        Returns:
            List of scheduled Campaigns
            
        Note:
            In production, this requires a GSI with:
            - PK: status
            - SK: scheduled_time
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                # For now, scan with filter (not optimal for production)
                # In production, use GSI query
                current_time = int(datetime.utcnow().timestamp())
                
                response = await table.scan(
                    FilterExpression='#status = :status AND scheduled_time <= :current_time',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'scheduled',
                        ':current_time': current_time
                    },
                    Limit=limit
                )
                
                campaigns = [Campaign.from_dynamodb_item(item) for item in response['Items']]
                
                logger.info(f"Retrieved {len(campaigns)} scheduled campaigns")
                return campaigns
            except ClientError as e:
                logger.error(f"Error getting scheduled campaigns: {e}")
                raise
    
    async def update(self, campaign: Campaign) -> Campaign:
        """
        Update an existing campaign.
        
        Args:
            campaign: Campaign domain model with updated fields
            
        Returns:
            Updated Campaign
            
        Raises:
            ValueError: If campaign doesn't exist
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            campaign.updated_at = datetime.utcnow()
            item = campaign.to_dynamodb_item()
            
            try:
                await table.put_item(
                    Item=item,
                    ConditionExpression='attribute_exists(PK) AND attribute_exists(SK)'
                )
                logger.info(f"Updated campaign: {campaign.campaign_id} for user: {campaign.user_id}")
                return campaign
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    logger.error(f"Campaign not found: {campaign.campaign_id}")
                    raise ValueError(f"Campaign with ID {campaign.campaign_id} not found")
                raise
    
    async def get_all_published_campaigns(self) -> List[Campaign]:
        """
        Get all published campaigns across all users.
        
        Used by Analytics Collector Lambda to fetch campaigns for analytics.
        
        Returns:
            List of published Campaigns
            
        Note:
            In production, this should use a GSI on status for efficient querying.
            For now, we scan with filter (not optimal for large datasets).
            
        Requirements: 8.1, 8.4
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                # Scan with filter for published campaigns
                response = await table.scan(
                    FilterExpression='#status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'published'
                    }
                )
                
                campaigns = [Campaign.from_dynamodb_item(item) for item in response['Items']]
                
                logger.info(f"Retrieved {len(campaigns)} published campaigns")
                return campaigns
            except ClientError as e:
                logger.error(f"Error getting published campaigns: {e}")
                raise
