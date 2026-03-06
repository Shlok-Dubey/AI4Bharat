"""
Campaign request/response schemas for API validation.

Provides Pydantic models for campaign endpoints.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class CampaignScheduleRequest(BaseModel):
    """Request schema for scheduling a campaign."""
    
    scheduled_time: datetime = Field(..., description="ISO 8601 datetime for campaign publishing")
    
    @field_validator('scheduled_time')
    @classmethod
    def validate_scheduled_time(cls, v: datetime) -> datetime:
        """Validate scheduled_time is in future and within 90 days."""
        now = datetime.utcnow()
        
        # Check if in future
        if v <= now:
            raise ValueError("scheduled_time must be in the future")
        
        # Check if within 90 days
        max_days = 90
        max_seconds = max_days * 24 * 60 * 60
        delta_seconds = (v - now).total_seconds()
        
        if delta_seconds > max_seconds:
            raise ValueError(f"scheduled_time must be within {max_days} days")
        
        return v


class CampaignResponse(BaseModel):
    """Response schema for campaign operations."""
    
    campaign_id: str
    user_id: str
    product_id: str
    caption: str
    hashtags: List[str]
    status: str
    scheduled_time: Optional[str] = None
    published_at: Optional[str] = None
    instagram_post_id: Optional[str] = None
    publish_attempts: int = 0
    last_error: Optional[str] = None
    created_at: str
    updated_at: str


class CampaignListResponse(BaseModel):
    """Response schema for campaign list operations."""
    
    campaigns: List[CampaignResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
