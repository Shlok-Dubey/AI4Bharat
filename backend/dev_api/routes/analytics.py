"""
Analytics routes for local development API.

Implements analytics aggregation and summary endpoints.

Requirements: 8.3
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, Query

from shared.schemas.analytics import AnalyticsSummary
from shared.services.auth_middleware import get_current_user
from shared.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsSummary)
async def get_analytics(
    start_date: datetime = Query(..., description="Start date for analytics query (ISO format)"),
    end_date: datetime = Query(..., description="End date for analytics query (ISO format)"),
    user_id: str = Depends(get_current_user)
):
    """
    Get analytics summary for user's campaigns in date range.
    
    Aggregates metrics across campaigns and returns:
    - Total likes, comments, reach, impressions
    - Average engagement rate
    - Top performing campaigns
    - Trends compared to previous period
    
    Requirements: 8.3
    """
    logger.info(
        f"Getting analytics for user {user_id} from {start_date} to {end_date}"
    )
    
    # Validate date range
    if start_date >= end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date"
        )
    
    try:
        analytics_service = AnalyticsService()
        summary = await analytics_service.get_analytics_summary(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(
            f"Retrieved analytics summary for user {user_id}: "
            f"{summary.campaign_count} campaigns, "
            f"avg_engagement={summary.avg_engagement_rate:.2f}%"
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting analytics for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )
