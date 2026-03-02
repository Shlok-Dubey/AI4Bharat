"""
User repository for DynamoDB operations.

Handles all user-related database operations with tenant isolation.
"""

from typing import Optional
from botocore.exceptions import ClientError
import logging

from repositories.base import BaseRepository
from shared.models.domain import User

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Repository for User entity operations."""
    
    def __init__(self, table_name: str = "users"):
        """Initialize UserRepository."""
        super().__init__(table_name)
    
    async def create(self, user: User) -> User:
        """
        Create a new user in DynamoDB.
        
        Args:
            user: User domain model
            
        Returns:
            Created User
            
        Raises:
            ClientError: If user already exists or DynamoDB error occurs
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            item = user.to_dynamodb_item()
            
            try:
                await table.put_item(
                    Item=item,
                    ConditionExpression='attribute_not_exists(PK)'
                )
                logger.info(f"Created user: {user.user_id}")
                return user
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    logger.error(f"User already exists: {user.user_id}")
                    raise ValueError(f"User with ID {user.user_id} already exists")
                raise
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                response = await table.get_item(
                    Key={'PK': f'USER#{user_id}'}
                )
                
                if 'Item' in response:
                    return User.from_dynamodb_item(response['Item'])
                return None
            except ClientError as e:
                logger.error(f"Error getting user {user_id}: {e}")
                raise
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email
            
        Returns:
            User if found, None otherwise
            
        Note:
            This requires a GSI on email field in production.
            For now, we'll scan (not recommended for production).
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                # In production, use GSI query instead of scan
                response = await table.scan(
                    FilterExpression='email = :email',
                    ExpressionAttributeValues={':email': email}
                )
                
                if response['Items']:
                    return User.from_dynamodb_item(response['Items'][0])
                return None
            except ClientError as e:
                logger.error(f"Error getting user by email {email}: {e}")
                raise
    
    async def update(self, user: User) -> User:
        """
        Update an existing user.
        
        Args:
            user: User domain model with updated fields
            
        Returns:
            Updated User
            
        Raises:
            ValueError: If user doesn't exist
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            item = user.to_dynamodb_item()
            
            try:
                await table.put_item(
                    Item=item,
                    ConditionExpression='attribute_exists(PK)'
                )
                logger.info(f"Updated user: {user.user_id}")
                return user
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    logger.error(f"User not found: {user.user_id}")
                    raise ValueError(f"User with ID {user.user_id} not found")
                raise
    
    async def delete(self, user_id: str) -> bool:
        """
        Delete a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                await table.delete_item(
                    Key={'PK': f'USER#{user_id}'},
                    ConditionExpression='attribute_exists(PK)'
                )
                logger.info(f"Deleted user: {user_id}")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    logger.warning(f"User not found for deletion: {user_id}")
                    return False
                raise
