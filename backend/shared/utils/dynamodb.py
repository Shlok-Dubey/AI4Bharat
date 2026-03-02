"""
DynamoDB connection manager for async operations.

This module provides a singleton connection manager for DynamoDB using aioboto3.
It handles connection lifecycle, health checks, and graceful shutdown.
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager
import aioboto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DynamoDBConnectionManager:
    """
    Async DynamoDB connection manager with health checks and graceful shutdown.
    
    This class implements a singleton pattern to manage DynamoDB connections
    across Lambda invocations and local development.
    """
    
    _instance: Optional['DynamoDBConnectionManager'] = None
    _session: Optional[aioboto3.Session] = None
    _resource = None
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the connection manager."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._session = None
            self._resource = None
            self._region = os.getenv('AWS_REGION', 'us-east-1')
            self._endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL')  # For local testing
    
    @asynccontextmanager
    async def get_resource(self):
        """
        Get DynamoDB resource as async context manager.
        
        Yields:
            DynamoDB resource for async operations
            
        Example:
            async with db_manager.get_resource() as dynamodb:
                table = await dynamodb.Table('users')
        """
        if self._session is None:
            self._session = aioboto3.Session()
        
        async with self._session.resource(
            'dynamodb',
            region_name=self._region,
            endpoint_url=self._endpoint_url
        ) as dynamodb:
            yield dynamodb
    
    async def health_check(self) -> bool:
        """
        Check DynamoDB connectivity.
        
        Returns:
            bool: True if DynamoDB is accessible, False otherwise
            
        This method attempts to list tables to verify connectivity.
        It's designed to complete quickly for health check endpoints.
        """
        try:
            async with self.get_resource() as dynamodb:
                # List tables to verify connectivity
                client = dynamodb.meta.client
                response = await client.list_tables(Limit=1)
                logger.info("DynamoDB health check passed")
                return True
        except ClientError as e:
            logger.error(f"DynamoDB health check failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during DynamoDB health check: {e}")
            return False
    
    async def shutdown(self):
        """
        Gracefully shutdown DynamoDB connections.
        
        This method should be called during Lambda shutdown or application termination
        to ensure all connections are properly closed.
        """
        try:
            if self._resource is not None:
                # aioboto3 resources are context managers, no explicit close needed
                self._resource = None
            
            if self._session is not None:
                self._session = None
            
            logger.info("DynamoDB connection manager shutdown complete")
        except Exception as e:
            logger.error(f"Error during DynamoDB shutdown: {e}")


# Global singleton instance
db_manager = DynamoDBConnectionManager()
