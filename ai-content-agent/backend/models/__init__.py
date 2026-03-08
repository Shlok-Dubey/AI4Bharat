"""
SQLAlchemy models for the AI Content Agent platform.

For AWS DynamoDB deployment:
- Replace these models with PynamoDB models
- Each model should inherit from pynamodb.models.Model
- Use DynamoDB-specific attributes (UnicodeAttribute, UTCDateTimeAttribute, etc.)
"""

from models.user import User, OAuthAccount
from models.campaign import Campaign, CampaignAsset
from models.content import GeneratedContent, ScheduledPost, PostAnalytics

__all__ = [
    "User",
    "OAuthAccount",
    "Campaign",
    "CampaignAsset",
    "GeneratedContent",
    "ScheduledPost",
    "PostAnalytics"
]
