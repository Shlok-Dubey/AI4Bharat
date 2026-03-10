"""
Campaign management routes.

This module handles CRUD operations for campaigns.
Campaigns are associated with authenticated users via JWT tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from typing import List
from datetime import datetime, timedelta
import uuid

from dependencies.auth import get_current_user
from schemas.campaign import (
    CampaignCreateRequest,
    CampaignUpdateRequest,
    CampaignResponse,
    CampaignDetailResponse,
    CampaignListResponse
)
from schemas.asset import (
    AssetUploadResponse,
    AssetListResponse,
    AssetDeleteResponse
)

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

@router.post("", response_model=CampaignDetailResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    campaign_data: CampaignCreateRequest,
    current_user = Depends(get_current_user)
):
    """
    Create a new campaign.
    
    This endpoint creates a campaign associated with the authenticated user.
    The campaign will be in 'draft' status by default.
    
    Args:
        campaign_data: Campaign creation data
        current_user: Authenticated user from JWT token
        
    Returns:
        Created campaign details
        
    Note:
        - Campaign starts in 'draft' status
        - start_date and end_date are calculated based on campaign_days
        - campaign_settings stores product info for AI generation later
    """
    import dynamodb_client as dynamodb
    from datetime import datetime, timedelta
    
    # Calculate campaign dates
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=campaign_data.campaign_days)
    
    # Store campaign details in settings for AI generation
    campaign_settings = {
        "product_name": campaign_data.product_name,
        "product_description": campaign_data.product_description,
        "campaign_days": campaign_data.campaign_days
    }
    
    # Create campaign in DynamoDB
    new_campaign = dynamodb.create_campaign(
        user_id=current_user['user_id'],
        name=campaign_data.campaign_name,
        description=f"Campaign for {campaign_data.product_name}",
        status="draft",
        campaign_settings=campaign_settings,
        start_date=start_date,
        end_date=end_date
    )
    
    # Build detailed response
    return CampaignDetailResponse(
        id=new_campaign['campaign_id'],
        user_id=new_campaign['user_id'],
        campaign_name=campaign_data.campaign_name,
        product_name=campaign_data.product_name,
        product_description=campaign_data.product_description,
        campaign_days=campaign_data.campaign_days,
        status=new_campaign['status'],
        start_date=new_campaign['start_date'],
        end_date=new_campaign['end_date'],
        created_at=new_campaign['created_at'],
        updated_at=new_campaign['updated_at'],
        total_content=0,
        scheduled_posts=0,
        published_posts=0
    )

@router.get("", response_model=CampaignListResponse)
def get_campaigns(
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all campaigns for the authenticated user.
    
    This endpoint returns a paginated list of campaigns owned by the user.
    Campaigns are ordered by creation date (newest first).
    
    Args:
        current_user: Authenticated user from JWT token
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
    Returns:
        List of campaigns with total count
    """
    import dynamodb_client as dynamodb
    
    # Get all campaigns for user
    all_campaigns = dynamodb.get_campaigns_by_user(current_user['user_id'])
    
    # Sort by created_at descending
    all_campaigns.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Apply pagination
    total = len(all_campaigns)
    paginated_campaigns = all_campaigns[skip:skip + limit]
    
    # Build response
    campaign_responses = []
    for campaign in paginated_campaigns:
        settings = campaign.get('campaign_settings', {})
        
        # Parse datetime
        created_at = datetime.fromisoformat(campaign['created_at']) if isinstance(campaign['created_at'], str) else campaign['created_at']
        updated_at = datetime.fromisoformat(campaign['updated_at']) if isinstance(campaign['updated_at'], str) else campaign['updated_at']
        start_date = datetime.fromisoformat(campaign['start_date']) if isinstance(campaign.get('start_date'), str) else campaign.get('start_date')
        end_date = datetime.fromisoformat(campaign['end_date']) if isinstance(campaign.get('end_date'), str) else campaign.get('end_date')
        
        campaign_responses.append(CampaignResponse(
            id=campaign['campaign_id'],
            user_id=campaign['user_id'],
            name=campaign['name'],
            description=campaign.get('description', ''),
            status=campaign['status'],
            campaign_settings=settings,
            start_date=start_date,
            end_date=end_date,
            created_at=created_at,
            updated_at=updated_at
        ))
    
    return CampaignListResponse(
        campaigns=campaign_responses,
        total=total
    )

@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
def get_campaign(
    campaign_id: uuid.UUID,
    current_user = Depends(get_current_user)
):
    """
    Get a specific campaign by ID.
    
    This endpoint returns detailed information about a campaign.
    Users can only access their own campaigns.
    
    Args:
        campaign_id: UUID of the campaign
        current_user: Authenticated user from JWT token
        
    Returns:
        Detailed campaign information
        
    Raises:
        HTTPException: If campaign not found or user doesn't own it
    """
    import dynamodb_client as dynamodb
    
    # Get campaign
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
    
    # Extract campaign details from settings
    settings = campaign.get('campaign_settings', {})
    product_name = settings.get("product_name", "")
    product_description = settings.get("product_description", "")
    campaign_days = settings.get("campaign_days", 0)
    
    # Count related content
    all_content = dynamodb.get_generated_content_by_campaign(str(campaign_id))
    total_content = len(all_content)
    scheduled_posts = len([c for c in all_content if c.get('status') == 'scheduled'])
    published_posts = len([c for c in all_content if c.get('status') == 'published'])
    
    # Parse datetime
    created_at = datetime.fromisoformat(campaign['created_at']) if isinstance(campaign['created_at'], str) else campaign['created_at']
    updated_at = datetime.fromisoformat(campaign['updated_at']) if isinstance(campaign['updated_at'], str) else campaign['updated_at']
    start_date = datetime.fromisoformat(campaign['start_date']) if isinstance(campaign.get('start_date'), str) else campaign.get('start_date')
    end_date = datetime.fromisoformat(campaign['end_date']) if isinstance(campaign.get('end_date'), str) else campaign.get('end_date')
    
    return CampaignDetailResponse(
        id=campaign['campaign_id'],
        user_id=campaign['user_id'],
        campaign_name=campaign['name'],
        product_name=product_name,
        product_description=product_description,
        campaign_days=campaign_days,
        status=campaign['status'],
        start_date=start_date,
        end_date=end_date,
        created_at=created_at,
        updated_at=updated_at,
        total_content=total_content,
        scheduled_posts=scheduled_posts,
        published_posts=published_posts
    )

@router.put("/{campaign_id}", response_model=CampaignDetailResponse)
def update_campaign(
    campaign_id: uuid.UUID,
    campaign_data: CampaignUpdateRequest,
    current_user = Depends(get_current_user)
):
    """
    Update a campaign.
    
    This endpoint allows updating campaign details.
    Only the campaign owner can update it.
    
    Args:
        campaign_id: UUID of the campaign
        campaign_data: Updated campaign data
        current_user: Authenticated user from JWT token
        
    Returns:
        Updated campaign details
        
    Raises:
        HTTPException: If campaign not found or user doesn't own it
    """
    import dynamodb_client as dynamodb
    
    # Get campaign
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
    
    # Prepare update data
    update_data = {}
    settings = campaign.get('campaign_settings', {})
    
    if campaign_data.campaign_name is not None:
        update_data['name'] = campaign_data.campaign_name
    
    if campaign_data.product_name is not None:
        settings["product_name"] = campaign_data.product_name
    
    if campaign_data.product_description is not None:
        settings["product_description"] = campaign_data.product_description
    
    if campaign_data.campaign_days is not None:
        settings["campaign_days"] = campaign_data.campaign_days
        # Recalculate end date
        start_date = datetime.fromisoformat(campaign['start_date']) if isinstance(campaign.get('start_date'), str) else campaign.get('start_date')
        if start_date:
            update_data['end_date'] = start_date + timedelta(days=campaign_data.campaign_days)
    
    if campaign_data.status is not None:
        update_data['status'] = campaign_data.status
    
    update_data['campaign_settings'] = settings
    
    # Update campaign in DynamoDB
    updated_campaign = dynamodb.update_campaign(str(campaign_id), **update_data)
    
    # Parse datetime
    created_at = datetime.fromisoformat(updated_campaign['created_at']) if isinstance(updated_campaign['created_at'], str) else updated_campaign['created_at']
    updated_at = datetime.fromisoformat(updated_campaign['updated_at']) if isinstance(updated_campaign['updated_at'], str) else updated_campaign['updated_at']
    start_date = datetime.fromisoformat(updated_campaign['start_date']) if isinstance(updated_campaign.get('start_date'), str) else updated_campaign.get('start_date')
    end_date = datetime.fromisoformat(updated_campaign['end_date']) if isinstance(updated_campaign.get('end_date'), str) else updated_campaign.get('end_date')
    
    # Build response
    return CampaignDetailResponse(
        id=updated_campaign['campaign_id'],
        user_id=updated_campaign['user_id'],
        campaign_name=updated_campaign['name'],
        product_name=settings.get("product_name", ""),
        product_description=settings.get("product_description", ""),
        campaign_days=settings.get("campaign_days", 0),
        status=updated_campaign['status'],
        start_date=start_date,
        end_date=end_date,
        created_at=created_at,
        updated_at=updated_at,
        total_content=0,
        scheduled_posts=0,
        published_posts=0
    )

@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: uuid.UUID,
    current_user = Depends(get_current_user)
):
    """
    Delete a campaign.
    
    This endpoint deletes a campaign and all associated data.
    Only the campaign owner can delete it.
    
    Args:
        campaign_id: UUID of the campaign
        current_user: Authenticated user from JWT token
        
    Raises:
        HTTPException: If campaign not found or user doesn't own it
        
    Note:
        This will cascade delete all related content, assets, and posts.
    """
    import dynamodb_client as dynamodb
    
    # Get campaign
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
    
    # Delete campaign from DynamoDB
    dynamodb.delete_campaign(str(campaign_id))
    
    return None


@router.post("/{campaign_id}/upload-assets", response_model=list[AssetUploadResponse])
async def upload_campaign_assets(
    campaign_id: uuid.UUID,
    files: list[UploadFile],
    current_user = Depends(get_current_user)
):
    """
    Upload assets (images/videos) for a campaign to AWS S3.
    
    This endpoint accepts multiple file uploads and stores them in S3.
    The S3 URLs are stored in DynamoDB and used for Instagram posting.
    
    Args:
        campaign_id: UUID of the campaign
        files: List of uploaded files
        current_user: Authenticated user from JWT token
        
    Returns:
        List of uploaded asset details with S3 URLs
        
    Raises:
        HTTPException: If campaign not found, file type invalid, or upload fails
        
    Note:
        - Supports images: JPEG, PNG (for Instagram)
        - Supports videos: MP4
        - Max file size: Images 8MB, Videos 100MB
        - Files stored in S3 with public-read ACL for Instagram API
    """
    from utils.aws_s3 import upload_media_to_s3, validate_media_file
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
    
    uploaded_assets = []
    
    for file in files:
        try:
            # Read file size
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
            
            # Validate file for Instagram requirements
            is_valid, error_msg = validate_media_file(file.filename, file_size)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            
            # Determine asset type
            file_extension = file.filename.lower().split('.')[-1]
            if file_extension in ['jpg', 'jpeg', 'png']:
                asset_type = 'image'
            elif file_extension == 'mp4':
                asset_type = 'video'
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: {file_extension}"
                )
            
            # Upload to S3
            s3_url = upload_media_to_s3(file.file, file.filename, str(campaign_id))
            
            # Create asset record in DynamoDB with S3 URL
            asset = dynamodb.create_campaign_asset(
                campaign_id=str(campaign_id),
                asset_type=asset_type,
                file_name=file.filename,
                file_path=s3_url,  # Store S3 URL
                file_size=file_size,
                mime_type=file.content_type
            )
            
            # Parse datetime from ISO string
            from datetime import datetime
            created_at = datetime.fromisoformat(asset['created_at']) if isinstance(asset['created_at'], str) else asset['created_at']
            
            uploaded_assets.append(AssetUploadResponse(
                id=asset['asset_id'],
                campaign_id=campaign_id,
                asset_type=asset_type,
                file_name=file.filename,
                file_path=s3_url,
                file_size=file_size,
                mime_type=file.content_type,
                created_at=created_at
            ))
            
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            print(f"❌ Error uploading {file.filename}:")
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload {file.filename}: {str(e)}"
            )
    
    return uploaded_assets

@router.get("/{campaign_id}/assets", response_model=AssetListResponse)
def get_campaign_assets(
    campaign_id: uuid.UUID,
    current_user = Depends(get_current_user)
):
    """
    Get all assets for a campaign.
    
    Args:
        campaign_id: UUID of the campaign
        current_user: Authenticated user from JWT token
        
    Returns:
        List of campaign assets
        
    Raises:
        HTTPException: If campaign not found
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
    
    # Get assets
    assets = dynamodb.get_campaign_assets(str(campaign_id))
    
    # Build response
    asset_responses = []
    for asset in assets:
        created_at = datetime.fromisoformat(asset['created_at']) if isinstance(asset['created_at'], str) else asset['created_at']
        
        asset_responses.append(AssetUploadResponse(
            id=asset['asset_id'],
            campaign_id=uuid.UUID(asset['campaign_id']),
            asset_type=asset['asset_type'],
            file_name=asset['file_name'],
            file_path=asset['file_path'],
            file_size=asset['file_size'],
            mime_type=asset.get('mime_type'),
            created_at=created_at
        ))
    
    return AssetListResponse(
        assets=asset_responses,
        total=len(asset_responses)
    )

@router.delete("/{campaign_id}/assets/{asset_id}", response_model=AssetDeleteResponse)
def delete_campaign_asset(
    campaign_id: uuid.UUID,
    asset_id: uuid.UUID,
    current_user = Depends(get_current_user)
):
    """
    Delete a campaign asset.
    
    Args:
        campaign_id: UUID of the campaign
        asset_id: UUID of the asset
        current_user: Authenticated user from JWT token
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If campaign or asset not found
        
    Note:
        Also deletes file from S3 bucket
    """
    import dynamodb_client as dynamodb
    from utils.aws_s3 import delete_media_from_s3
    
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
    
    # Get asset
    asset = dynamodb.get_campaign_asset(str(asset_id))
    
    if not asset or asset.get('campaign_id') != str(campaign_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Delete file from S3
    try:
        delete_media_from_s3(asset['file_path'])
    except Exception as e:
        print(f"Error deleting file from S3: {e}")
    
    # Delete database record
    dynamodb.delete_campaign_asset(str(asset_id))
    
    return AssetDeleteResponse(
        message="Asset deleted successfully",
        deleted_asset_id=asset_id
    )


@router.get("/{campaign_id}/analytics")
def get_campaign_analytics(
    campaign_id: uuid.UUID,
    current_user = Depends(get_current_user)
):
    """
    Get analytics for a campaign.
    
    This endpoint fetches engagement metrics for all published posts in a campaign.
    Uses the Analytics Agent to gather metrics from social media platforms.
    
    Args:
        campaign_id: UUID of the campaign
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Aggregated analytics data for the campaign
        
    Raises:
        HTTPException: If campaign not found or user doesn't own it
        
    Note:
        - Fetches analytics from DynamoDB (populated by analytics_job.py)
        - Metrics include: impressions, reach, likes, comments, saves, shares, engagement_rate
    """
    from agents.analytics_agent import AnalyticsAgent
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
    
    # Initialize Analytics Agent
    agent = AnalyticsAgent()
    
    # Fetch campaign analytics from DynamoDB
    analytics = agent.fetch_campaign_analytics(str(campaign_id))
    
    return analytics
