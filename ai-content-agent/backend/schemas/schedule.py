"""
Pydantic schemas for post scheduling endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class ScheduleCreateRequest(BaseModel):
    """Schedule creation request schema"""
    start_date: Optional[str] = Field(
        None,
        description="Campaign start date (YYYY-MM-DD). Defaults to today if not provided."
    )
    timezone_offset: Optional[int] = Field(
        default=0,
        ge=-12,
        le=14,
        description="Timezone offset in hours (e.g., -5 for EST, 0 for UTC)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-01-15",
                "timezone_offset": -5
            }
        }

class ScheduleUpdateRequest(BaseModel):
    """Update scheduled post time"""
    scheduled_for: str = Field(
        ...,
        description="New scheduled datetime (YYYY-MM-DD HH:MM:SS)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "scheduled_for": "2024-01-15 14:30:00"
            }
        }

class ScheduledPostResponse(BaseModel):
    """Scheduled post response schema"""
    id: uuid.UUID
    content_id: uuid.UUID
    scheduled_for: datetime
    status: str
    platform: str
    content_type: str
    caption: str
    hashtags: Optional[str]
    post_time: str
    day_of_week: str
    is_peak_time: bool

    class Config:
        from_attributes = True

class SchedulePreviewItem(BaseModel):
    """Individual scheduled post preview"""
    post_id: Optional[uuid.UUID] = None
    content_id: uuid.UUID
    platform: str
    content_type: str
    caption: str
    hashtags: Optional[str]
    scheduled_for: str
    post_time: str
    post_date: str
    day_of_week: str
    day_number: int
    is_peak_time: bool
    is_weekend: bool

class SchedulePreviewResponse(BaseModel):
    """Schedule preview response"""
    campaign_id: uuid.UUID
    campaign_name: str
    total_posts: int
    campaign_days: int
    start_date: str
    end_date: str
    posts_by_platform: dict
    posts_by_day: dict
    peak_time_percentage: float
    scheduled_posts: list[SchedulePreviewItem]

class ScheduleCreateResponse(BaseModel):
    """Schedule creation response"""
    message: str
    campaign_id: uuid.UUID
    total_scheduled: int
    start_date: str
    end_date: str
    preview: SchedulePreviewResponse
