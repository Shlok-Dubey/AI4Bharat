"""
Post scheduling routes.

This module handles scheduling of approved content using AI agents.
Integrates Campaign Planner and Scheduler agents for optimal distribution.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from database_sqlite import get_db
from models.user import User
from models.campaign import Campaign
from models.content import GeneratedContent, ScheduledPost
from dependencies.auth import get_current_user
from schemas.schedule import (
    ScheduleCreateRequest,
    ScheduleCreateResponse,
    SchedulePreviewResponse,
    SchedulePreviewItem
)

router = APIRouter(prefix="/campaigns", tags=["Post Scheduling"])

@router.post("/{campaign_id}/schedule", response_model=ScheduleCreateResponse)
def schedule_campaign_posts(
    campaign_id: uuid.UUID,
    request: ScheduleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Schedule approved content for posting.
    
    This endpoint orchestrates the complete scheduling workflow:
    1. Verify campaign ownership
    2. Fetch approved content
    3. Call Campaign Planner Agent to distribute across days
    4. Call Scheduler Agent to assign optimal times
    5. Save scheduled posts to database
    6. Return schedule preview
    
    Args:
        campaign_id: UUID of the campaign
        request: Scheduling parameters (start_date, timezone_offset)
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        ScheduleCreateResponse with schedule preview
        
    Raises:
        HTTPException: If campaign not found, no approved content, or scheduling fails
        
    Workflow:
        Campaign → Approved Content → Planner Agent → Scheduler Agent → Database
        
    Note:
        - Only schedules approved content
        - Existing scheduled posts are deleted and recreated
        - Uses AI agents for optimal distribution
    """
    # Step 1: Verify campaign exists and user owns it
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Step 2: Fetch approved content
    approved_content = db.query(GeneratedContent).filter(
        GeneratedContent.campaign_id == campaign_id,
        GeneratedContent.status == "approved"
    ).all()
    
    if not approved_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No approved content found. Please approve content before scheduling."
        )
    
    # Get campaign settings
    settings = campaign.campaign_settings or {}
    campaign_days = settings.get("campaign_days", 30)
    
    # Parse start date
    if request.start_date:
        try:
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    else:
        start_date = datetime.utcnow()
    
    # Step 3: Call Campaign Planner Agent
    from agents.campaign_planner import get_campaign_planner
    planner = get_campaign_planner()
    
    # Convert content to format expected by planner
    content_for_planning = [
        {
            "id": str(content.id),
            "caption": content.content_text,
            "hashtags": content.hashtags,
            "platform": content.platform,
            "content_type": content.content_type,
            "ai_metadata": content.ai_metadata or {}
        }
        for content in approved_content
    ]
    
    # Plan content distribution across campaign days
    planned_posts = planner.plan_campaign(
        content=content_for_planning,
        campaign_days=campaign_days,
        start_date=start_date
    )
    
    # Step 4: Call Scheduler Agent
    from agents.scheduler_agent import get_scheduler_agent
    scheduler = get_scheduler_agent()
    
    # Schedule posts at optimal times
    scheduled_posts = scheduler.schedule_posts(
        posts=planned_posts,
        start_date=start_date,
        timezone_offset=request.timezone_offset
    )
    
    # Step 5: Save to database
    # Delete existing scheduled posts for this campaign
    db.query(ScheduledPost).filter(
        ScheduledPost.content_id.in_([c.id for c in approved_content])
    ).delete(synchronize_session=False)
    
    # Create new scheduled posts
    db_scheduled_posts = []
    for scheduled_post in scheduled_posts:
        # Parse scheduled datetime
        scheduled_datetime = datetime.strptime(
            scheduled_post["post_datetime"],
            "%Y-%m-%d %H:%M:%S"
        )
        
        # Create ScheduledPost record
        new_scheduled_post = ScheduledPost(
            content_id=uuid.UUID(scheduled_post["content_id"]),
            scheduled_for=scheduled_datetime,
            status="pending",
            platform_post_id=None,
            published_at=None,
            error_message=None,
            retry_count=0
        )
        
        db.add(new_scheduled_post)
        db_scheduled_posts.append(new_scheduled_post)
    
    # Commit all scheduled posts
    db.commit()
    
    # Refresh to get IDs
    for post in db_scheduled_posts:
        db.refresh(post)
    
    # Step 6: Build preview response
    # Analyze schedule
    analysis = scheduler.analyze_schedule(scheduled_posts)
    
    # Calculate end date
    end_date = start_date + timedelta(days=campaign_days - 1)
    
    # Build preview items
    preview_items = []
    for scheduled_post in scheduled_posts:
        preview_items.append(SchedulePreviewItem(
            content_id=uuid.UUID(scheduled_post["content_id"]),
            platform=scheduled_post["platform"],
            content_type=scheduled_post["content_type"],
            caption=scheduled_post["caption"][:100] + "..." if len(scheduled_post["caption"]) > 100 else scheduled_post["caption"],
            hashtags=scheduled_post.get("hashtags"),
            scheduled_for=scheduled_post["post_datetime"],
            post_time=scheduled_post["post_time"],
            post_date=scheduled_post["post_date"],
            day_of_week=scheduled_post["day_of_week"],
            day_number=scheduled_post["recommended_day"],
            is_peak_time=scheduled_post["is_peak_time"],
            is_weekend=scheduled_post["is_weekend"]
        ))
    
    # Build preview response
    preview = SchedulePreviewResponse(
        campaign_id=campaign_id,
        campaign_name=campaign.name,
        total_posts=len(scheduled_posts),
        campaign_days=campaign_days,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        posts_by_platform=analysis["posts_by_platform"],
        posts_by_day=analysis["posts_by_day"],
        peak_time_percentage=analysis["peak_time_percentage"],
        scheduled_posts=preview_items
    )
    
    return ScheduleCreateResponse(
        message=f"Successfully scheduled {len(scheduled_posts)} posts",
        campaign_id=campaign_id,
        total_scheduled=len(scheduled_posts),
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        preview=preview
    )

@router.get("/{campaign_id}/schedule/preview", response_model=SchedulePreviewResponse)
def get_schedule_preview(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get preview of scheduled posts for a campaign.
    
    This endpoint returns the current schedule without creating new scheduled posts.
    Useful for viewing existing schedules.
    
    Args:
        campaign_id: UUID of the campaign
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        SchedulePreviewResponse with scheduled posts
        
    Raises:
        HTTPException: If campaign not found or no scheduled posts
    """
    # Verify campaign
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Get scheduled posts
    scheduled_posts = db.query(ScheduledPost).join(GeneratedContent).filter(
        GeneratedContent.campaign_id == campaign_id
    ).all()
    
    if not scheduled_posts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scheduled posts found for this campaign"
        )
    
    # Build preview
    settings = campaign.campaign_settings or {}
    campaign_days = settings.get("campaign_days", 30)
    
    # Get date range
    dates = [post.scheduled_for for post in scheduled_posts]
    start_date = min(dates)
    end_date = max(dates)
    
    # Count by platform and day
    posts_by_platform = {}
    posts_by_day = {}
    
    for post in scheduled_posts:
        # Platform count
        content = post.content
        platform = content.platform
        posts_by_platform[platform] = posts_by_platform.get(platform, 0) + 1
        
        # Day count
        day_num = (post.scheduled_for.date() - start_date.date()).days + 1
        posts_by_day[day_num] = posts_by_day.get(day_num, 0) + 1
    
    # Build preview items
    preview_items = []
    for post in scheduled_posts:
        content = post.content
        day_num = (post.scheduled_for.date() - start_date.date()).days + 1
        
        preview_items.append(SchedulePreviewItem(
            content_id=content.id,
            platform=content.platform,
            content_type=content.content_type,
            caption=content.content_text[:100] + "..." if len(content.content_text) > 100 else content.content_text,
            hashtags=content.hashtags,
            scheduled_for=post.scheduled_for.strftime("%Y-%m-%d %H:%M:%S"),
            post_time=post.scheduled_for.strftime("%H:%M"),
            post_date=post.scheduled_for.strftime("%Y-%m-%d"),
            day_of_week=post.scheduled_for.strftime("%A"),
            day_number=day_num,
            is_peak_time=True,  # Would need to calculate
            is_weekend=post.scheduled_for.weekday() >= 5
        ))
    
    return SchedulePreviewResponse(
        campaign_id=campaign_id,
        campaign_name=campaign.name,
        total_posts=len(scheduled_posts),
        campaign_days=campaign_days,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        posts_by_platform=posts_by_platform,
        posts_by_day=posts_by_day,
        peak_time_percentage=0.0,  # Would need to calculate
        scheduled_posts=preview_items
    )


@router.post("/{campaign_id}/schedule/{content_id}/publish")
def publish_post_now(
    campaign_id: uuid.UUID,
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually publish a scheduled post to Instagram immediately.
    
    This endpoint allows testing Instagram posting without waiting for scheduled time.
    
    Args:
        campaign_id: UUID of the campaign
        content_id: UUID of the content to publish
        current_user: Authenticated user from JWT token
        db: Session = Database session
        
    Returns:
        dict with success status and Instagram media ID
        
    Raises:
        HTTPException: If campaign not found, content not found, or posting fails
    """
    # Verify campaign
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Get content
    content = db.query(GeneratedContent).filter(
        GeneratedContent.id == content_id,
        GeneratedContent.campaign_id == campaign_id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Get user's Instagram OAuth account
    from models.user import OAuthAccount
    oauth_account = db.query(OAuthAccount).filter(
        OAuthAccount.user_id == current_user.id,
        OAuthAccount.provider == "instagram"
    ).first()
    
    if not oauth_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instagram account not connected. Please connect your Instagram Business Account first."
        )
    
    # Get campaign assets (images)
    from models.campaign import CampaignAsset
    assets = db.query(CampaignAsset).filter(
        CampaignAsset.campaign_id == campaign_id
    ).first()
    
    if not assets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No images found for this campaign. Please upload at least one image."
        )
    
    # Construct image URL (must be publicly accessible)
    # For local testing, you'll need to use ngrok or a public URL
    image_url = f"http://192.168.31.75:8002/uploads/campaign_assets/{campaign_id}/{assets.file_path.split('/')[-1]}"
    
    print(f"\n⚠️  Image URL: {image_url}")
    print(f"⚠️  This URL must be publicly accessible for Instagram API")
    print(f"⚠️  Consider using ngrok or uploading to a public server\n")
    
    # Get posting agent
    from agents.posting_agent import get_posting_agent
    posting_agent = get_posting_agent()
    
    # Attempt to post
    success, media_id, error = posting_agent.post_to_instagram(
        access_token=oauth_account.access_token,
        instagram_account_id=oauth_account.provider_account_id,
        caption=content.content_text,
        image_url=image_url,
        hashtags=content.hashtags
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish to Instagram: {error}"
        )
    
    # Update scheduled post if exists
    scheduled_post = db.query(ScheduledPost).filter(
        ScheduledPost.content_id == content_id
    ).first()
    
    if scheduled_post:
        scheduled_post.status = "published"
        scheduled_post.platform_post_id = media_id
        scheduled_post.published_at = datetime.utcnow()
        db.commit()
    
    return {
        "success": True,
        "message": "Post published to Instagram successfully!",
        "media_id": media_id,
        "content_id": str(content_id),
        "campaign_id": str(campaign_id),
        "published_at": datetime.utcnow().isoformat()
    }
