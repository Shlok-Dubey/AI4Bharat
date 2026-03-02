"""
Base repository class for DynamoDB operations.

Provides common functionality for all repositories.
"""

from typing import Optional
from shared.utils.dynamodb import db_manager


class BaseRepository:
    """Base repository with common DynamoDB operations."""
    
    def __init__(self, table_name: str):
        """
        Initialize repository with table name.
        
        Args:
            table_name: Name of the DynamoDB table
        """
        self.table_name = table_name
        self.db_manager = db_manager
    
    async def get_table(self):
        """
        Get DynamoDB table resource.
        
        Returns:
            DynamoDB table resource
        """
        async with self.db_manager.get_resource() as dynamodb:
            return await dynamodb.Table(self.table_name)
