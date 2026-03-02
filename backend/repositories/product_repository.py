"""
Product repository for DynamoDB operations.

Handles all product-related database operations with tenant isolation.
"""

from typing import Optional, List
from datetime import datetime
from botocore.exceptions import ClientError
import logging

from repositories.base import BaseRepository
from shared.models.domain import Product

logger = logging.getLogger(__name__)


class ProductRepository(BaseRepository):
    """Repository for Product entity operations."""
    
    def __init__(self, table_name: str = "products"):
        """Initialize ProductRepository."""
        super().__init__(table_name)
    
    async def create(self, product: Product) -> Product:
        """
        Create a new product in DynamoDB.
        
        Args:
            product: Product domain model
            
        Returns:
            Created Product
            
        Raises:
            ClientError: If product already exists or DynamoDB error occurs
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            item = product.to_dynamodb_item()
            
            try:
                await table.put_item(
                    Item=item,
                    ConditionExpression='attribute_not_exists(PK) AND attribute_not_exists(SK)'
                )
                logger.info(f"Created product: {product.product_id} for user: {product.user_id}")
                return product
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    logger.error(f"Product already exists: {product.product_id}")
                    raise ValueError(f"Product with ID {product.product_id} already exists")
                raise
    
    async def get_by_id(self, user_id: str, product_id: str) -> Optional[Product]:
        """
        Get product by ID with tenant isolation.
        
        Args:
            user_id: User ID (for tenant isolation)
            product_id: Product ID
            
        Returns:
            Product if found and not soft-deleted, None otherwise
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                response = await table.get_item(
                    Key={
                        'PK': f'USER#{user_id}',
                        'SK': f'PRODUCT#{product_id}'
                    }
                )
                
                if 'Item' in response:
                    product = Product.from_dynamodb_item(response['Item'])
                    # Exclude soft-deleted products
                    if product.deleted_at is None:
                        return product
                return None
            except ClientError as e:
                logger.error(f"Error getting product {product_id} for user {user_id}: {e}")
                raise
    
    async def get_by_user(self, user_id: str, include_deleted: bool = False) -> List[Product]:
        """
        Get all products for a user with tenant isolation.
        
        Args:
            user_id: User ID
            include_deleted: Whether to include soft-deleted products
            
        Returns:
            List of Products
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                response = await table.query(
                    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                    ExpressionAttributeValues={
                        ':pk': f'USER#{user_id}',
                        ':sk_prefix': 'PRODUCT#'
                    }
                )
                
                products = [Product.from_dynamodb_item(item) for item in response['Items']]
                
                # Filter out soft-deleted products unless requested
                if not include_deleted:
                    products = [p for p in products if p.deleted_at is None]
                
                logger.info(f"Retrieved {len(products)} products for user: {user_id}")
                return products
            except ClientError as e:
                logger.error(f"Error getting products for user {user_id}: {e}")
                raise
    
    async def update(self, product: Product) -> Product:
        """
        Update an existing product.
        
        Args:
            product: Product domain model with updated fields
            
        Returns:
            Updated Product
            
        Raises:
            ValueError: If product doesn't exist
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            product.updated_at = datetime.utcnow()
            item = product.to_dynamodb_item()
            
            try:
                await table.put_item(
                    Item=item,
                    ConditionExpression='attribute_exists(PK) AND attribute_exists(SK)'
                )
                logger.info(f"Updated product: {product.product_id} for user: {product.user_id}")
                return product
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    logger.error(f"Product not found: {product.product_id}")
                    raise ValueError(f"Product with ID {product.product_id} not found")
                raise
    
    async def soft_delete(self, user_id: str, product_id: str) -> bool:
        """
        Soft delete a product by setting deleted_at timestamp.
        
        Args:
            user_id: User ID (for tenant isolation)
            product_id: Product ID
            
        Returns:
            True if deleted, False if not found
        """
        async with self.db_manager.get_resource() as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            try:
                await table.update_item(
                    Key={
                        'PK': f'USER#{user_id}',
                        'SK': f'PRODUCT#{product_id}'
                    },
                    UpdateExpression='SET deleted_at = :deleted_at, updated_at = :updated_at',
                    ExpressionAttributeValues={
                        ':deleted_at': int(datetime.utcnow().timestamp()),
                        ':updated_at': int(datetime.utcnow().timestamp())
                    },
                    ConditionExpression='attribute_exists(PK) AND attribute_exists(SK) AND attribute_not_exists(deleted_at)'
                )
                logger.info(f"Soft deleted product: {product_id} for user: {user_id}")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    logger.warning(f"Product not found or already deleted: {product_id}")
                    return False
                raise
