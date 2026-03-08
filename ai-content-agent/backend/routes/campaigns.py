"""
Campaign management routes.

This module handles CRUD operations for campaigns.
Campaigns are associated with authenticated users via JWT tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta
import uuid

from database_sqlite import get_db
from models.user import User
from models.campaign import Campaign
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new campaign.
    
    This endpoint creates a campaign associated with the authenticated user.
    The campaign will be in 'draft' status by default.
    
    Args:
        campaign_data: Campaign creation data
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Created campaign details
        
    Note:
        - Campaign starts in 'draft' status
        - start_date and end_date are calculated based on campaign_days
        - campaign_settings stores product info for AI generation later
    """
    # Calculate campaign dates
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=campaign_data.campaign_days)
    
    # Store campaign details in settings for AI generation
    campaign_settings = {
        "product_name": campaign_data.product_name,
        "product_description": campaign_data.product_description,
        "campaign_days": campaign_data.campaign_days
    }
    
    # Create campaign
    new_campaign = Campaign(
        user_id=current_user.id,
        name=campaign_data.campaign_name,
        description=f"Campaign for {campaign_data.product_name}",
        status="draft",
        campaign_settings=campaign_settings,
        start_date=start_date,
        end_date=end_date
    )
    
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)
    
    # Build detailed response
    return CampaignDetailResponse(
        id=new_campaign.id,
        user_id=new_campaign.user_id,
        campaign_name=campaign_data.campaign_name,
        product_name=campaign_data.product_name,
        product_description=campaign_data.product_description,
        campaign_days=campaign_data.campaign_days,
        status=new_campaign.status,
        start_date=new_campaign.start_date,
        end_date=new_campaign.end_date,
        created_at=new_campaign.created_at,
        updated_at=new_campaign.updated_at,
        total_content=0,
        scheduled_posts=0,
        published_posts=0
    )

@router.get("", response_model=CampaignListResponse)
def get_campaigns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all campaigns for the authenticated user.
    
    This endpoint returns a paginated list of campaigns owned by the user.
    Campaigns are ordered by creation date (newest first).
    
    Args:
        current_user: Authenticated user from JWT token
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
    Returns:
        List of campaigns with total count
    """
    # Get total count
    total = db.query(func.count(Campaign.id)).filter(
        Campaign.user_id == current_user.id
    ).scalar()
    
    # Get campaigns
    campaigns = db.query(Campaign).filter(
        Campaign.user_id == current_user.id
    ).order_by(
        Campaign.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return CampaignListResponse(
        campaigns=[CampaignResponse.model_validate(c) for c in campaigns],
        total=total
    )

@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
def get_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific campaign by ID.
    
    This endpoint returns detailed information about a campaign.
    Users can only access their own campaigns.
    
    Args:
        campaign_id: UUID of the campaign
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Detailed campaign information
        
    Raises:
        HTTPException: If campaign not found or user doesn't own it
    """
    # Get campaign
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Extract campaign details from settings
    settings = campaign.campaign_settings or {}
    product_name = settings.get("product_name", "")
    product_description = settings.get("product_description", "")
    campaign_days = settings.get("campaign_days", 0)
    
    # Count related content (to be implemented)
    # For now, return 0 for all counts
    total_content = 0
    scheduled_posts = 0
    published_posts = 0
    
    return CampaignDetailResponse(
        id=campaign.id,
        user_id=campaign.user_id,
        campaign_name=campaign.name,
        product_name=product_name,
        product_description=product_description,
        campaign_days=campaign_days,
        status=campaign.status,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        total_content=total_content,
        scheduled_posts=scheduled_posts,
        published_posts=published_posts
    )

@router.put("/{campaign_id}", response_model=CampaignDetailResponse)
def update_campaign(
    campaign_id: uuid.UUID,
    campaign_data: CampaignUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a campaign.
    
    This endpoint allows updating campaign details.
    Only the campaign owner can update it.
    
    Args:
        campaign_id: UUID of the campaign
        campaign_data: Updated campaign data
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Updated campaign details
        
    Raises:
        HTTPException: If campaign not found or user doesn't own it
    """
    # Get campaign
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Update campaign fields
    settings = campaign.campaign_settings or {}
    
    if campaign_data.campaign_name is not None:
        campaign.name = campaign_data.campaign_name
    
    if campaign_data.product_name is not None:
        settings["product_name"] = campaign_data.product_name
    
    if campaign_data.product_description is not None:
        settings["product_description"] = campaign_data.product_description
    
    if campaign_data.campaign_days is not None:
        settings["campaign_days"] = campaign_data.campaign_days
        # Recalculate end date
        if campaign.start_date:
            campaign.end_date = campaign.start_date + timedelta(days=campaign_data.campaign_days)
    
    if campaign_data.status is not None:
        campaign.status = campaign_data.status
    
    campaign.campaign_settings = settings
    campaign.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(campaign)
    
    # Build response
    return CampaignDetailResponse(
        id=campaign.id,
        user_id=campaign.user_id,
        campaign_name=campaign.name,
        product_name=settings.get("product_name", ""),
        product_description=settings.get("product_description", ""),
        campaign_days=settings.get("campaign_days", 0),
        status=campaign.status,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        total_content=0,
        scheduled_posts=0,
        published_posts=0
    )

@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a campaign.
    
    This endpoint deletes a campaign and all associated data.
    Only the campaign owner can delete it.
    
    Args:
        campaign_id: UUID of the campaign
        current_user: Authenticated user from JWT token
        db: Database session
        
    Raises:
        HTTPException: If campaign not found or user doesn't own it
        
    Note:
        This will cascade delete all related content, assets, and posts.
    """
    # Get campaign
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    db.delete(campaign)
    db.commit()
    
    return None


@router.post("/{campaign_id}/upload-assets", response_model=list[AssetUploadResponse])
async def upload_campaign_assets(
    campaign_id: uuid.UUID,
    files: list[UploadFile],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload assets (images/videos) for a campaign.
    
    This endpoint accepts multiple file uploads and stores them locally.
    For production deployment, files should be uploaded to AWS S3.
    
    Args:
        campaign_id: UUID of the campaign
        files: List of uploaded files
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        List of uploaded asset details
        
    Raises:
        HTTPException: If campaign not found, file type invalid, or upload fails
        
    Note:
        - Supports images: JPEG, PNG, GIF, WebP
        - Supports videos: MP4, MPEG, QuickTime, AVI
        - Max file size: 100MB per file
        - Files stored in: uploads/campaign_assets/{campaign_id}/
        
    For AWS S3 deployment:
        - Replace save_file_locally with upload_to_s3
        - Store S3 URLs in file_path field
        - Add S3 bucket configuration
        - Implement presigned URLs for private access
    """
    from models.campaign import CampaignAsset
    from utils.file_upload import (
        validate_file_type,
        validate_file_size,
        save_file_locally,
        get_file_size
    )
    
    # Verify campaign exists and user owns it
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    uploaded_assets = []
    
    for file in files:
        try:
            # Validate file type
            asset_type = validate_file_type(file)
            
            # Validate file size
            if not validate_file_size(file):
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File {file.filename} exceeds maximum size of 100MB"
                )
            
            # Get file size
            file_size = get_file_size(file)
            
            # Save file locally
            # For production: Replace with upload_to_s3(file, str(campaign_id))
            file_path, unique_filename = await save_file_locally(file, str(campaign_id))
            
            # Create asset record
            asset = CampaignAsset(
                campaign_id=campaign_id,
                asset_type=asset_type,
                file_name=unique_filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=file.content_type
            )
            
            db.add(asset)
            uploaded_assets.append(asset)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload {file.filename}: {str(e)}"
            )
    
    db.commit()
    
    # Refresh all assets to get IDs
    for asset in uploaded_assets:
        db.refresh(asset)
    
    return [AssetUploadResponse.model_validate(asset) for asset in uploaded_assets]

@router.get("/{campaign_id}/assets", response_model=AssetListResponse)
def get_campaign_assets(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all assets for a campaign.
    
    Args:
        campaign_id: UUID of the campaign
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        List of campaign assets
        
    Raises:
        HTTPException: If campaign not found
    """
    from models.campaign import CampaignAsset
    
    # Verify campaign exists and user owns it
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Get assets
    assets = db.query(CampaignAsset).filter(
        CampaignAsset.campaign_id == campaign_id
    ).order_by(CampaignAsset.created_at.desc()).all()
    
    return AssetListResponse(
        assets=[AssetUploadResponse.model_validate(asset) for asset in assets],
        total=len(assets)
    )

@router.delete("/{campaign_id}/assets/{asset_id}", response_model=AssetDeleteResponse)
def delete_campaign_asset(
    campaign_id: uuid.UUID,
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a campaign asset.
    
    Args:
        campaign_id: UUID of the campaign
        asset_id: UUID of the asset
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If campaign or asset not found
        
    Note:
        For AWS S3: Also delete file from S3 bucket
    """
    from models.campaign import CampaignAsset
    import os
    
    # Verify campaign exists and user owns it
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Get asset
    asset = db.query(CampaignAsset).filter(
        CampaignAsset.id == asset_id,
        CampaignAsset.campaign_id == campaign_id
    ).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Delete file from local storage
    # For production: Use delete_from_s3(s3_key)
    try:
        if os.path.exists(asset.file_path):
            os.remove(asset.file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    # Delete database record
    db.delete(asset)
    db.commit()
    
    return AssetDeleteResponse(
        message="Asset deleted successfully",
        deleted_asset_id=asset_id
    )


@router.get("/{campaign_id}/analytics")
def get_campaign_analytics(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
        - For local development: Returns mock analytics data
        - For production: Fetches real data from Meta Graph API, YouTube API, etc.
        - Metrics include: views, likes, comments, shares, engagement_rate
    """
    from models.content import ScheduledPost
    from agents.analytics_agent import AnalyticsAgent
    
    # Verify campaign exists and user owns it
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Get all published posts for this campaign
    # ScheduledPost -> GeneratedContent -> Campaign
    from models.content import GeneratedContent
    
    scheduled_posts = db.query(ScheduledPost).join(
        GeneratedContent,
        ScheduledPost.content_id == GeneratedContent.id
    ).filter(
        GeneratedContent.campaign_id == campaign_id,
        ScheduledPost.status == "published"
    ).all()
    
    if not scheduled_posts:
        # Return empty analytics if no published posts
        return {
            "campaign_id": str(campaign_id),
            "total_posts": 0,
            "total_views": 0,
            "total_likes": 0,
            "total_comments": 0,
            "total_shares": 0,
            "total_engagements": 0,
            "engagement_rate": 0,
            "average_views_per_post": 0,
            "post_analytics": [],
            "fetched_at": datetime.utcnow().isoformat()
        }
    
    # Initialize Analytics Agent
    # For production: Pass access token from OAuth
    # oauth_account = db.query(OAuthAccount).filter(
    #     OAuthAccount.user_id == current_user.id,
    #     OAuthAccount.provider == "meta"
    # ).first()
    # agent = AnalyticsAgent(access_token=oauth_account.access_token if oauth_account else None)
    
    agent = AnalyticsAgent()
    
    # Collect post IDs
    post_ids = [str(post.id) for post in scheduled_posts]
    
    # Fetch campaign analytics
    analytics = agent.fetch_campaign_analytics(
        campaign_id=str(campaign_id),
        post_ids=post_ids
    )
    
    return analytics
