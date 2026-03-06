"""
Analytics request/response schemas.

Pydantic models for analytics aggregation and summary.

Requirements: 8.3
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class AnalyticsSummary(BaseModel):
    """Summary of analytics across campaigns."""
    
    # Totals
    total_likes: int = Field(..., description="Sum of all likes")
    total_comments: int = Field(..., description="Sum of all comments")
    total_reach: int = Field(..., description="Sum of all reach")
    total_impressions: int = Field(..., description="Sum of all impressions")
    
    # Averages
    avg_engagement_rate: float = Field(..., description="Mean engagement rate across campaigns")
    
    # Campaign count
    campaign_count: int = Field(..., description="Number of campaigns analyzed")
    
    # Top performing campaigns
    top_campaigns: List[dict] = Field(default_factory=list, description="Top performing campaigns by engagement rate")
    
    # Trends (comparison to previous period)
    trend_likes: Optional[float] = Field(None, description="Percentage change in likes vs previous period")
    trend_comments: Optional[float] = Field(None, description="Percentage change in comments vs previous period")
    trend_reach: Optional[float] = Field(None, description="Percentage change in reach vs previous period")
    trend_engagement_rate: Optional[float] = Field(None, description="Percentage change in engagement rate vs previous period")
    
    # Date range
    start_date: datetime = Field(..., description="Start of analysis period")
    end_date: datetime = Field(..., description="End of analysis period")


class AnalyticsQueryParams(BaseModel):
    """Query parameters for analytics endpoint."""
    
    start_date: datetime = Field(..., description="Start date for analytics query")
    end_date: datetime = Field(..., description="End date for analytics query")
