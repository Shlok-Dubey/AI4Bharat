"""
Pydantic schemas for campaign endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class CampaignCreateRequest(BaseModel):
    """Campaign creation request schema"""
    campaign_name: str = Field(..., min_length=2, max_length=255)
    product_name: str = Field(..., min_length=2, max_length=255)
    product_description: str = Field(..., min_length=10)
    campaign_days: int = Field(..., ge=1, le=365, description="Number of days for the campaign")

    class Config:
        json_schema_extra = {
            "example": {
                "campaign_name": "Summer Product Launch",
                "product_name": "EcoBottle Pro",
                "product_description": "A sustainable, insulated water bottle made from recycled materials. Keeps drinks cold for 24 hours and hot for 12 hours.",
                "campaign_days": 30
            }
        }

class CampaignUpdateRequest(BaseModel):
    """Campaign update request schema"""
    campaign_name: Optional[str] = Field(None, min_length=2, max_length=255)
    product_name: Optional[str] = Field(None, min_length=2, max_length=255)
    product_description: Optional[str] = Field(None, min_length=10)
    campaign_days: Optional[int] = Field(None, ge=1, le=365)
    status: Optional[str] = Field(None, pattern="^(draft|active|paused|completed)$")

    class Config:
        json_schema_extra = {
            "example": {
                "campaign_name": "Updated Campaign Name",
                "status": "active"
            }
        }

class CampaignResponse(BaseModel):
    """Campaign response schema"""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str
    status: str
    campaign_settings: Optional[dict]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CampaignDetailResponse(BaseModel):
    """Detailed campaign response with additional info"""
    id: uuid.UUID
    user_id: uuid.UUID
    campaign_name: str
    product_name: str
    product_description: str
    campaign_days: int
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Statistics (to be populated later)
    total_content: int = 0
    scheduled_posts: int = 0
    published_posts: int = 0

    class Config:
        from_attributes = True

class CampaignListResponse(BaseModel):
    """List of campaigns response"""
    campaigns: list[CampaignResponse]
    total: int
