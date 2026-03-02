"""
Memory repository for DynamoDB operations.

Handles Campaign Intelligence Memory operations for AI learning.
"""

from typing import Optional
from datetime import datetime
from botocore.exceptions import ClientError
import logging

from repositories.base import BaseRepository
from shared.models.domain import Memory

logger = logging.getLogger(__name__)


class MemoryRepository(BaseRepository):
    """Repository for Campaign Intelligence Memory operations."""
    
    def __init__(self, table_name: str = "memory"):
        """Initialize MemoryRepository."""
        super().__init__(table_name)
    
    async def get_memory(self, user_id: str, memory_type: str) -> Optional[Memory]:
        """
        Get memory by user ID and memory type.
        
        Args:
            user_id: User ID
            memory_type: Memory type (business_profile, performance_insights, 
                        content_patterns, engagement_patterns)
            
        Returns:
            Memory if found, None otherwise
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                response = await table.get_item(
                    Key={
                        'PK': f'USER#{user_id}',
                        'SK': f'MEMORY#{memory_type}'
                    }
                )
                
                if 'Item' in response:
                    return Memory.from_dynamodb_item(response['Item'])
                return None
            except ClientError as e:
                logger.error(f"Error getting memory {memory_type} for user {user_id}: {e}")
                raise
    
    async def update_memory(self, memory: Memory) -> Memory:
        """
        Update or create memory record.
        
        Args:
            memory: Memory domain model
            
        Returns:
            Updated Memory
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            memory.last_updated = datetime.utcnow()
            item = memory.to_dynamodb_item()
            
            try:
                await table.put_item(Item=item)
                logger.info(f"Updated memory {memory.memory_type} for user: {memory.user_id}")
                return memory
            except ClientError as e:
                logger.error(f"Error updating memory {memory.memory_type} for user {memory.user_id}: {e}")
                raise
    
    async def increment_confidence(
        self,
        user_id: str,
        memory_type: str,
        confidence_delta: float,
        sample_size_delta: int = 1
    ) -> bool:
        """
        Atomically increment confidence score and sample size.
        
        This is useful when learning from new campaign performance data.
        
        Args:
            user_id: User ID
            memory_type: Memory type
            confidence_delta: Amount to add to confidence (can be negative)
            sample_size_delta: Amount to add to sample size (default 1)
            
        Returns:
            True if update succeeded, False if memory doesn't exist
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                await table.update_item(
                    Key={
                        'PK': f'USER#{user_id}',
                        'SK': f'MEMORY#{memory_type}'
                    },
                    UpdateExpression='SET confidence = confidence + :confidence_delta, '
                                   'sample_size = sample_size + :sample_size_delta, '
                                   'last_updated = :last_updated',
                    ExpressionAttributeValues={
                        ':confidence_delta': float(confidence_delta),
                        ':sample_size_delta': sample_size_delta,
                        ':last_updated': int(datetime.utcnow().timestamp()),
                        ':min_confidence': 0.0,
                        ':max_confidence': 1.0
                    },
                    ConditionExpression='attribute_exists(PK) AND attribute_exists(SK) AND '
                                      'confidence + :confidence_delta BETWEEN :min_confidence AND :max_confidence'
                )
                logger.info(f"Incremented confidence for memory {memory_type} for user: {user_id}")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    logger.warning(f"Memory {memory_type} not found or confidence out of bounds for user: {user_id}")
                    return False
                raise
