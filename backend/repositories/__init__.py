"""
Repository layer for data access.

This module provides repository classes for all domain entities,
implementing the repository pattern for DynamoDB operations.
"""

from .user_repository import UserRepository
from .product_repository import ProductRepository
from .campaign_repository import CampaignRepository
from .analytics_repository import AnalyticsRepository
from .memory_repository import MemoryRepository

__all__ = [
    'UserRepository',
    'ProductRepository',
    'CampaignRepository',
    'AnalyticsRepository',
    'MemoryRepository',
]
