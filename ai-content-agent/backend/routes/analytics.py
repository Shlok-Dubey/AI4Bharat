"""
Analytics Routes

Endpoints for fetching and managing post analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict
import dynamodb_client as db
from dependencies.auth import get_current_user
from agents.analytics_agent import AnalyticsAgent

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/campaign/{campaign_id}")
async def get_campaign_analytics(
    campaign_id: str,
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Get analytics for a specific campaign
    
    Args:
        campaign_id: Campaign ID
        current_user: Authenticated user
    
    Returns:
        Campaign analytics with aggregated metrics
    """
    # Verify campaign exists and user owns it
    campaign = db.get_campaign(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    if campaign.get('user_id') != current_user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign"
        )
    
    # Fetch analytics
    agent = AnalyticsAgent()
    analytics = agent.fetch_campaign_analytics(campaign_id)
    
    return analytics


@router.get("/campaign/{campaign_id}/summary")
async def get_campaign_performance_summary(
    campaign_id: str,
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Get performance summary with insights for a campaign
    
    Args:
        campaign_id: Campaign ID
        current_user: Authenticated user
    
    Returns:
        Performance summary with insights and recommendations
    """
    # Verify campaign exists and user owns it
    campaign = db.get_campaign(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    if campaign.get('user_id') != current_user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign"
        )
    
    # Get performance summary
    agent = AnalyticsAgent()
    summary = agent.get_performance_summary(campaign_id)
    
    return summary


@router.get("/post/{post_id}")
async def get_post_analytics(
    post_id: str,
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Get analytics for a specific scheduled post
    
    Args:
        post_id: Scheduled post ID
        current_user: Authenticated user
    
    Returns:
        Post analytics with engagement metrics
    """
    # Get scheduled post
    scheduled_post = db.get_scheduled_post(post_id)
    
    if not scheduled_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Get content to verify ownership
    content = db.get_generated_content(scheduled_post['content_id'])
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Get campaign to verify ownership
    campaign = db.get_campaign(content['campaign_id'])
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    if campaign.get('user_id') != current_user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this post"
        )
    
    # Fetch analytics
    agent = AnalyticsAgent()
    analytics = agent.fetch_post_analytics(post_id)
    
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analytics not available for this post yet"
        )
    
    return analytics


@router.post("/fetch")
async def trigger_analytics_fetch(
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Manually trigger analytics fetch for all published posts
    
    This endpoint runs the analytics job in the background.
    Normally this runs automatically every 12 hours via cron.
    
    Args:
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
    
    Returns:
        Status message
    """
    from analytics_job import fetch_all_analytics
    
    # Run analytics fetch in background
    background_tasks.add_task(fetch_all_analytics)
    
    return {
        "status": "success",
        "message": "Analytics fetch started in background"
    }
