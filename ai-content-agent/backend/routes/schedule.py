"""
Post scheduling routes.

This module handles scheduling of approved content using AI agents.
Integrates Campaign Planner and Scheduler agents for optimal distribution.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
import uuid

from dependencies.auth import get_current_user
from schemas.schedule import (
    ScheduleCreateRequest,
    ScheduleCreateResponse,
    SchedulePreviewResponse,
    SchedulePreviewItem,
    ScheduleUpdateRequest
)
from utils.aws_eventbridge import create_scheduled_post_rule, delete_scheduled_post_rule, update_scheduled_post_rule

router = APIRouter(prefix="/campaigns", tags=["Post Scheduling"])

@router.post("/{campaign_id}/schedule", response_model=ScheduleCreateResponse)
def schedule_campaign_posts(
    campaign_id: uuid.UUID,
    request: ScheduleCreateRequest,
    current_user = Depends(get_current_user)
):
    """
    Schedule approved content for posting.
    
    This endpoint orchestrates the complete scheduling workflow:
    1. Verify campaign ownership
    2. Fetch approved content
    3. Call Campaign Planner Agent to distribute across days
    4. Call Scheduler Agent to assign optimal times
    5. Save scheduled posts to DynamoDB
    6. Return schedule preview
    
    Args:
        campaign_id: UUID of the campaign
        request: Scheduling parameters (start_date, timezone_offset)
        current_user: Authenticated user from JWT token
        
    Returns:
        ScheduleCreateResponse with schedule preview
        
    Raises:
        HTTPException: If campaign not found, no approved content, or scheduling fails
        
    Workflow:
        Campaign → Approved Content → Planner Agent → Scheduler Agent → DynamoDB
        
    Note:
        - Only schedules approved content
        - Existing scheduled posts are deleted and recreated
        - Uses AI agents for optimal distribution
    """
    import dynamodb_client as dynamodb
    from utils.aws_eventbridge import validate_scheduler_config
    
    # Check EventBridge configuration
    config_valid, config_error = validate_scheduler_config()
    if not config_valid:
        print(f"[Scheduler Error] {config_error}")
        print(f"[Scheduler] Posts will be scheduled in DynamoDB but automatic posting is disabled")
    
    # Step 1: Verify campaign exists and user owns it
    campaign = dynamodb.get_campaign(str(campaign_id))
    
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
    
    # Step 2: Fetch approved content
    all_content = dynamodb.get_generated_content_by_campaign(str(campaign_id))
    approved_content = [c for c in all_content if c.get('status') == 'approved']
    
    if not approved_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No approved content found. Please approve content before scheduling."
        )
    
    # Get campaign settings
    settings = campaign.get('campaign_settings', {})
    campaign_days = int(settings.get("campaign_days", 30))  # Convert to int
    
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
            "id": content['content_id'],
            "caption": content['content_text'],
            "hashtags": content.get('hashtags', ''),
            "platform": content['platform'],
            "content_type": content['content_type'],
            "ai_metadata": content.get('ai_metadata', {})
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
    
    # Step 5: Save to DynamoDB
    # Delete existing scheduled posts for this campaign's content
    existing_scheduled = dynamodb.get_scheduled_posts_by_campaign(str(campaign_id))
    for post in existing_scheduled:
        dynamodb.delete_scheduled_post(post['post_id'])
    
    # Create new scheduled posts
    db_scheduled_posts = []
    for scheduled_post in scheduled_posts:
        # Parse scheduled datetime
        scheduled_datetime = datetime.strptime(
            scheduled_post["post_datetime"],
            "%Y-%m-%d %H:%M:%S"
        )
        
        # Create ScheduledPost record in DynamoDB
        new_scheduled_post = dynamodb.create_scheduled_post(
            content_id=scheduled_post["content_id"],
            scheduled_for=scheduled_datetime,
            status="pending"
        )
        
        db_scheduled_posts.append(new_scheduled_post)
        
        # Create EventBridge rule for this post (optional - for automatic posting)
        success, error = create_scheduled_post_rule(
            new_scheduled_post['post_id'], 
            scheduled_datetime
        )
        if not success:
            # Track if EventBridge is not configured
            if "not configured" in str(error):
                print(f"ℹ️  EventBridge not configured for post {new_scheduled_post['post_id']} (automatic posting disabled)")
                # Don't fail the request, just note that automatic posting won't work
            else:
                print(f"⚠️  Failed to create EventBridge rule for post {new_scheduled_post['post_id']}: {error}")
                # Still don't fail - schedule is saved to DynamoDB
    
    # Step 6: Build preview response
    # Analyze schedule
    analysis = scheduler.analyze_schedule(scheduled_posts)
    
    # Calculate end date
    end_date = start_date + timedelta(days=campaign_days - 1)
    
    # Build preview items
    preview_items = []
    for i, scheduled_post in enumerate(scheduled_posts):
        try:
            # Get the corresponding database post for the post_id
            db_post = db_scheduled_posts[i] if i < len(db_scheduled_posts) else None
            
            preview_items.append(SchedulePreviewItem(
                post_id=uuid.UUID(db_post['post_id']) if db_post else None,
                content_id=uuid.UUID(scheduled_post["content_id"]),
                platform=scheduled_post["platform"],
                content_type=scheduled_post["content_type"],
                caption=scheduled_post.get("caption", "")[:100] + "..." if len(scheduled_post.get("caption", "")) > 100 else scheduled_post.get("caption", ""),
                hashtags=scheduled_post.get("hashtags"),
                scheduled_for=scheduled_post["post_datetime"],
                post_time=scheduled_post["post_time"],
                post_date=scheduled_post["post_date"],
                day_of_week=scheduled_post["day_of_week"],
                day_number=scheduled_post["recommended_day"],
                is_peak_time=scheduled_post["is_peak_time"],
                is_weekend=scheduled_post["is_weekend"]
            ))
        except Exception as e:
            print(f"❌ Error building preview item: {e}")
            print(f"   Post data: {scheduled_post}")
            import traceback
            traceback.print_exc()
            raise
    
    # Build preview response
    preview = SchedulePreviewResponse(
        campaign_id=campaign_id,
        campaign_name=campaign['name'],
        total_posts=len(scheduled_posts),
        campaign_days=campaign_days,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        posts_by_platform=analysis["posts_by_platform"],
        posts_by_day=analysis["posts_by_day"],
        peak_time_percentage=analysis["peak_time_percentage"],
        scheduled_posts=preview_items
    )
    
    print(f"✅ Schedule created successfully: {len(scheduled_posts)} posts")
    
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
    current_user = Depends(get_current_user)
):
    """
    Get preview of scheduled posts for a campaign.
    
    This endpoint returns the current schedule without creating new scheduled posts.
    Useful for viewing existing schedules.
    
    Args:
        campaign_id: UUID of the campaign
        current_user: Authenticated user from JWT token
        
    Returns:
        SchedulePreviewResponse with scheduled posts
        
    Raises:
        HTTPException: If campaign not found or no scheduled posts
    """
    import dynamodb_client as dynamodb
    
    # Verify campaign
    campaign = dynamodb.get_campaign(str(campaign_id))
    
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
    
    # Get scheduled posts for this campaign
    scheduled_posts = dynamodb.get_scheduled_posts_by_campaign(str(campaign_id))
    
    if not scheduled_posts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scheduled posts found for this campaign"
        )
    
    # Build preview
    settings = campaign.get('campaign_settings', {})
    campaign_days = int(settings.get("campaign_days", 30))  # Convert to int
    
    # Get date range and parse datetimes
    dates = []
    for post in scheduled_posts:
        scheduled_for = datetime.fromisoformat(post['scheduled_for']) if isinstance(post['scheduled_for'], str) else post['scheduled_for']
        dates.append(scheduled_for)
    
    start_date = min(dates)
    end_date = max(dates)
    
    # Count by platform and day
    posts_by_platform = {}
    posts_by_day = {}
    
    for post in scheduled_posts:
        # Get content for this post
        content = dynamodb.get_generated_content(post['content_id'])
        if not content:
            continue
            
        # Platform count
        platform = content['platform']
        posts_by_platform[platform] = posts_by_platform.get(platform, 0) + 1
        
        # Day count
        scheduled_for = datetime.fromisoformat(post['scheduled_for']) if isinstance(post['scheduled_for'], str) else post['scheduled_for']
        day_num = (scheduled_for.date() - start_date.date()).days + 1
        posts_by_day[day_num] = posts_by_day.get(day_num, 0) + 1
    
    # Build preview items
    preview_items = []
    for post in scheduled_posts:
        content = dynamodb.get_generated_content(post['content_id'])
        if not content:
            continue
            
        scheduled_for = datetime.fromisoformat(post['scheduled_for']) if isinstance(post['scheduled_for'], str) else post['scheduled_for']
        day_num = (scheduled_for.date() - start_date.date()).days + 1
        
        preview_items.append(SchedulePreviewItem(
            post_id=uuid.UUID(post['post_id']),
            content_id=uuid.UUID(content['content_id']),
            platform=content['platform'],
            content_type=content['content_type'],
            caption=content['content_text'][:100] + "..." if len(content['content_text']) > 100 else content['content_text'],
            hashtags=content.get('hashtags'),
            scheduled_for=scheduled_for.strftime("%Y-%m-%d %H:%M:%S"),
            post_time=scheduled_for.strftime("%H:%M"),
            post_date=scheduled_for.strftime("%Y-%m-%d"),
            day_of_week=scheduled_for.strftime("%A"),
            day_number=day_num,
            is_peak_time=True,  # Would need to calculate
            is_weekend=scheduled_for.weekday() >= 5
        ))
    
    return SchedulePreviewResponse(
        campaign_id=campaign_id,
        campaign_name=campaign['name'],
        total_posts=len(scheduled_posts),
        campaign_days=campaign_days,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        posts_by_platform=posts_by_platform,
        posts_by_day=posts_by_day,
        peak_time_percentage=0.0,  # Would need to calculate
        scheduled_posts=preview_items
    )

# Manual publish endpoint - allows users to publish scheduled posts immediately
@router.post("/{campaign_id}/posts/{post_id}/publish")
def publish_post_now(
    campaign_id: uuid.UUID,
    post_id: uuid.UUID,
    current_user = Depends(get_current_user)
):
    """
    Manually publish a scheduled post to Instagram immediately.
    
    This endpoint allows users to publish posts without waiting for scheduled time.
    
    Args:
        campaign_id: UUID of the campaign
        post_id: UUID of the scheduled post
        current_user: Authenticated user from JWT token
        
    Returns:
        dict with success status and Instagram media ID
        
    Raises:
        HTTPException: If campaign not found, post not found, or posting fails
    """
    import dynamodb_client as dynamodb
    
    # Verify campaign exists and user owns it
    campaign = dynamodb.get_campaign(str(campaign_id))
    
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
    
    # Get scheduled post
    scheduled_post = dynamodb.get_scheduled_post(str(post_id))
    
    if not scheduled_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found"
        )
    
    # Check if already published
    if scheduled_post.get('status') == 'published':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post has already been published"
        )
    
    # Get content
    content = dynamodb.get_generated_content(scheduled_post['content_id'])
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Get user's Instagram OAuth account
    oauth_account = dynamodb.get_oauth_account_by_provider(current_user['user_id'], 'meta')
    
    if not oauth_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instagram account not connected. Please connect your Instagram Business Account first."
        )
    
    # Get campaign assets (images)
    assets = dynamodb.get_campaign_assets(str(campaign_id))
    
    if not assets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No images found for this campaign. Please upload at least one image."
        )
    
    # Get first asset's S3 URL
    image_url = assets[0]['file_path']
    
    print(f"\n✅ Using S3 image URL: {image_url}")
    print(f"✅ Publishing post to Instagram\n")
    
    # Get posting agent
    from agents.posting_agent import get_posting_agent
    posting_agent = get_posting_agent()
    
    # Attempt to post (with automatic token refresh)
    success, media_id, error = posting_agent.post_to_instagram(
        access_token=oauth_account['access_token'],
        instagram_account_id=oauth_account['provider_account_id'],
        caption=content['content_text'],
        image_url=image_url,
        hashtags=content.get('hashtags', ''),
        user_id=current_user['user_id']
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish to Instagram: {error}"
        )
    
    # Update scheduled post status
    dynamodb.update_scheduled_post(
        str(post_id),
        status='published',
        platform_post_id=media_id,
        published_at=datetime.utcnow()
    )
    
    print(f"✅ Post published successfully: {media_id}")
    
    return {
        "success": True,
        "message": "Post published to Instagram successfully!",
        "media_id": media_id,
        "post_id": str(post_id),
        "campaign_id": str(campaign_id),
        "published_at": datetime.utcnow().isoformat()
    }

@router.patch("/{campaign_id}/schedule/{post_id}/time")
def update_scheduled_time(
    campaign_id: uuid.UUID,
    post_id: uuid.UUID,
    request: ScheduleUpdateRequest,
    current_user = Depends(get_current_user)
):
    """
    Update the scheduled time for a specific post.
    
    This endpoint allows users to manually adjust the AI-suggested posting time.
    
    Args:
        campaign_id: UUID of the campaign
        post_id: UUID of the scheduled post
        request: New scheduled datetime
        current_user: Authenticated user from JWT token
        
    Returns:
        dict with updated schedule details
        
    Raises:
        HTTPException: If campaign not found, post not found, or invalid datetime
    """
    import dynamodb_client as dynamodb
    
    # Verify campaign exists and user owns it
    campaign = dynamodb.get_campaign(str(campaign_id))
    
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
    
    # Get scheduled post
    scheduled_post = dynamodb.get_scheduled_post(str(post_id))
    
    if not scheduled_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found"
        )
    
    # Parse new datetime
    try:
        new_datetime = datetime.strptime(request.scheduled_for, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid datetime format. Use YYYY-MM-DD HH:MM:SS"
        )
    
    # Validate datetime is in the future
    if new_datetime < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be in the future"
        )
    
    # Store old time for logging
    old_time = scheduled_post.get('scheduled_for')
    
    # Update scheduled time in DynamoDB
    updated_post = dynamodb.update_scheduled_post(
        str(post_id),
        scheduled_for=new_datetime
    )
    
    print(f"[Scheduler] EventBridge rule updated after user edit: {post_id}")
    
    # Delete old EventBridge rule
    delete_success, delete_error = delete_scheduled_post_rule(str(post_id))
    if not delete_success:
        print(f"⚠️  Failed to delete old EventBridge rule: {delete_error}")
    
    # Create new EventBridge rule with updated time
    create_success, create_error = create_scheduled_post_rule(str(post_id), new_datetime)
    if not create_success:
        print(f"⚠️  Failed to create new EventBridge rule: {create_error}")
    else:
        print(f"[Scheduler] EventBridge rule created for updated time: {new_datetime}")
    
    return {
        "success": True,
        "message": "Scheduled time updated successfully",
        "post_id": str(post_id),
        "campaign_id": str(campaign_id),
        "old_time": old_time,
        "new_time": new_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "post_time": new_datetime.strftime("%H:%M"),
        "post_date": new_datetime.strftime("%Y-%m-%d"),
        "day_of_week": new_datetime.strftime("%A")
    }

