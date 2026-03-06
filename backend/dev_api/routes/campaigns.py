"""
Campaign management routes for local development API.

Implements campaign scheduling and cancellation operations.

Requirements: 6.1, 6.2, 6.5, 6.6
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends

from shared.schemas.campaign import (
    CampaignScheduleRequest,
    CampaignResponse,
    CampaignListResponse,
)
from shared.models.domain import Campaign
from shared.services.auth_middleware import get_current_user
from shared.services.scheduler_service import SchedulerService
from repositories.campaign_repository import CampaignRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/campaigns", tags=["Campaigns"])


def _campaign_to_response(campaign: Campaign) -> CampaignResponse:
    """Convert Campaign domain model to response schema."""
    return CampaignResponse(
        campaign_id=campaign.campaign_id,
        user_id=campaign.user_id,
        product_id=campaign.product_id,
        caption=campaign.caption,
        hashtags=campaign.hashtags,
        status=campaign.status,
        scheduled_time=campaign.scheduled_time.isoformat() if campaign.scheduled_time else None,
        published_at=campaign.published_at.isoformat() if campaign.published_at else None,
        instagram_post_id=campaign.instagram_post_id,
        publish_attempts=campaign.publish_attempts,
        last_error=campaign.last_error,
        created_at=campaign.created_at.isoformat(),
        updated_at=campaign.updated_at.isoformat(),
    )


@router.post("/{campaign_id}/schedule", response_model=CampaignResponse)
async def schedule_campaign(
    campaign_id: str,
    request: CampaignScheduleRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Schedule a campaign for future publishing.
    
    Steps:
    1. Validate scheduled_time is in future and within 90 days
    2. Verify campaign ownership
    3. Update campaign status to "scheduled"
    4. Call scheduler service to add to queue
    5. Return updated campaign
    
    Requirements: 6.1, 6.2, 6.6
    """
    campaign_repo = CampaignRepository()
    scheduler_service = SchedulerService()
    
    try:
        # Get campaign with tenant isolation
        campaign = await campaign_repo.get_by_id(user_id, campaign_id)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Verify campaign can be scheduled (must be in draft status)
        if campaign.status not in ["draft", "failed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Campaign cannot be scheduled from status: {campaign.status}"
            )
        
        # Update campaign status and scheduled_time
        campaign.status = "scheduled"
        campaign.scheduled_time = request.scheduled_time
        campaign.updated_at = datetime.utcnow()
        
        # Save to database
        updated_campaign = await campaign_repo.update(campaign)
        
        # Add to SQS queue
        try:
            message_id = await scheduler_service.schedule_campaign(
                campaign_id=campaign_id,
                user_id=user_id,
                scheduled_time=request.scheduled_time
            )
            logger.info(
                f"Campaign {campaign_id} scheduled successfully for {request.scheduled_time.isoformat()}, "
                f"message_id: {message_id}"
            )
        except Exception as e:
            # Rollback status if scheduling fails
            campaign.status = "draft"
            campaign.scheduled_time = None
            await campaign_repo.update(campaign)
            
            logger.error(f"Failed to schedule campaign {campaign_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to schedule campaign"
            )
        
        return _campaign_to_response(updated_campaign)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error scheduling campaign {campaign_id} for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Campaign scheduling failed"
        )


@router.post("/{campaign_id}/cancel", response_model=CampaignResponse)
async def cancel_campaign(
    campaign_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Cancel a scheduled campaign.
    
    Steps:
    1. Verify campaign ownership
    2. Update campaign status to "cancelled"
    3. Attempt to remove message from queue (best effort)
    
    Note: Message removal from SQS is best effort. The worker will check
    campaign status before publishing to handle race conditions.
    
    Requirements: 6.5
    """
    campaign_repo = CampaignRepository()
    scheduler_service = SchedulerService()
    
    try:
        # Get campaign with tenant isolation
        campaign = await campaign_repo.get_by_id(user_id, campaign_id)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Verify campaign can be cancelled (must be scheduled)
        if campaign.status != "scheduled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Campaign cannot be cancelled from status: {campaign.status}"
            )
        
        # Update campaign status to cancelled
        campaign.status = "cancelled"
        campaign.updated_at = datetime.utcnow()
        
        # Save to database
        updated_campaign = await campaign_repo.update(campaign)
        
        # Attempt to remove from queue (best effort)
        try:
            await scheduler_service.cancel_campaign(campaign_id)
            logger.info(f"Campaign {campaign_id} cancelled successfully")
        except Exception as e:
            # Log error but don't fail the request
            # Worker will check status before publishing
            logger.warning(f"Failed to remove campaign {campaign_id} from queue: {e}")
        
        return _campaign_to_response(updated_campaign)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error cancelling campaign {campaign_id} for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Campaign cancellation failed"
        )


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    page: int = 1,
    page_size: int = 20,
    status_filter: str = None,
    user_id: str = Depends(get_current_user)
):
    """
    List all campaigns for authenticated user with pagination.
    
    Steps:
    1. Filter by authenticated user_id
    2. Optionally filter by status
    3. Support pagination
    4. Return list of campaigns
    
    Requirements: 6.6
    """
    campaign_repo = CampaignRepository()
    
    try:
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be >= 1"
            )
        
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100"
            )
        
        # Get campaigns for user with optional status filter
        all_campaigns = await campaign_repo.get_by_user(user_id, status=status_filter)
        
        # Sort by created_at descending (newest first)
        all_campaigns.sort(key=lambda c: c.created_at, reverse=True)
        
        # Calculate pagination
        total = len(all_campaigns)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Get page of campaigns
        page_campaigns = all_campaigns[start_idx:end_idx]
        
        # Check if more pages available
        has_more = end_idx < total
        
        logger.info(f"Listed {len(page_campaigns)} campaigns for user: {user_id} (page {page})")
        
        return CampaignListResponse(
            campaigns=[_campaign_to_response(c) for c in page_campaigns],
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing campaigns for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list campaigns"
        )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get a specific campaign by ID.
    
    Verifies ownership before returning campaign.
    
    Requirements: 6.6
    """
    campaign_repo = CampaignRepository()
    
    try:
        # Get campaign with tenant isolation
        campaign = await campaign_repo.get_by_id(user_id, campaign_id)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        logger.info(f"Retrieved campaign: {campaign_id} for user: {user_id}")
        
        return _campaign_to_response(campaign)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign {campaign_id} for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get campaign"
        )
