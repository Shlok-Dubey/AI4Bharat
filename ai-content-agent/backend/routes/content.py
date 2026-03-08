"""
Generated content management routes.

This module handles CRUD operations for AI-generated campaign content.
Content generation uses placeholder data until AI integration is implemented.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
import uuid

from database_sqlite import get_db
from models.user import User
from models.campaign import Campaign
from models.content import GeneratedContent
from dependencies.auth import get_current_user
from schemas.content import (
    ContentGenerateRequest,
    ContentApproveRequest,
    ContentResponse,
    ContentDetailResponse,
    ContentListResponse,
    ContentGenerateResponse
)

router = APIRouter(prefix="/campaigns", tags=["Content Generation"])
content_router = APIRouter(prefix="/content", tags=["Content Management"])

@router.get("/{campaign_id}/content", response_model=ContentListResponse)
def get_campaign_content(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = None,
    platform_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get all generated content for a campaign.
    
    This endpoint returns a list of AI-generated content pieces for a campaign.
    Results can be filtered by status and platform.
    
    Args:
        campaign_id: UUID of the campaign
        current_user: Authenticated user from JWT token
        db: Database session
        status_filter: Filter by status (draft, approved, rejected, scheduled, published)
        platform_filter: Filter by platform (instagram, facebook, twitter, linkedin)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
    Returns:
        List of generated content with statistics
        
    Raises:
        HTTPException: If campaign not found or user doesn't own it
    """
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
    
    # Build query
    query = db.query(GeneratedContent).filter(
        GeneratedContent.campaign_id == campaign_id
    )
    
    # Apply filters
    if status_filter:
        # Support both 'draft' and 'pending' for backward compatibility
        if status_filter == "draft":
            query = query.filter(GeneratedContent.status.in_(["draft", "pending"]))
        else:
            query = query.filter(GeneratedContent.status == status_filter)
    
    if platform_filter:
        query = query.filter(GeneratedContent.platform == platform_filter)
    
    # Get total count
    total = query.count()
    
    # Get content
    content = query.order_by(
        GeneratedContent.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    # Get statistics
    status_counts = db.query(
        GeneratedContent.status,
        func.count(GeneratedContent.id)
    ).filter(
        GeneratedContent.campaign_id == campaign_id
    ).group_by(GeneratedContent.status).all()
    
    platform_counts = db.query(
        GeneratedContent.platform,
        func.count(GeneratedContent.id)
    ).filter(
        GeneratedContent.campaign_id == campaign_id
    ).group_by(GeneratedContent.platform).all()
    
    return ContentListResponse(
        content=[ContentResponse.model_validate(c) for c in content],
        total=total,
        by_status={status: count for status, count in status_counts},
        by_platform={platform: count for platform, count in platform_counts}
    )

@router.post("/{campaign_id}/generate-content", response_model=ContentGenerateResponse)
def generate_campaign_content(
    campaign_id: uuid.UUID,
    request: ContentGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI content for a campaign.
    
    This endpoint integrates with the Content Generator Agent to create
    AI-powered social media content. Content is marked as 'pending' status
    and requires approval before scheduling.
    
    Workflow:
    1. Verify campaign ownership
    2. Fetch campaign product information
    3. Call Content Generator Agent
    4. Save generated content to database
    5. Mark content as 'pending' (awaiting approval)
    6. Return generated content to frontend
    
    Args:
        campaign_id: UUID of the campaign
        request: Content generation parameters (platform, content_type, count)
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        ContentGenerateResponse with generated content pieces
        
    Raises:
        HTTPException: If campaign not found or user doesn't own it
        
    Note:
        Currently uses template-based generation.
        For production: Replace with AWS Bedrock or OpenAI API.
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
    
    # Step 2: Fetch campaign product information
    settings = campaign.campaign_settings or {}
    product_name = settings.get("product_name", "Product")
    product_description = settings.get("product_description", "")
    
    # Validate product information
    if not product_name or not product_description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign must have product name and description to generate content"
        )
    
    # Step 3: Initialize Content Generator Agent
    from agents.content_generator import get_content_generator
    agent = get_content_generator()
    
    generated_content = []
    
    try:
        # Generate content for each requested piece
        for i in range(request.count):
            # Step 4: Call Content Generator Agent
            ai_content = agent.generate_social_content(
                product_name=product_name,
                product_description=product_description,
                platform=request.platform,
                content_type=request.content_type,
                tone=request.tone if hasattr(request, 'tone') else "engaging"
            )
            
            # Step 5: Save generated content to database
            new_content = GeneratedContent(
                campaign_id=campaign_id,
                platform=request.platform,
                content_type=request.content_type,
                content_text=ai_content["instagram_caption"],
                hashtags=ai_content["hashtags"],
                ai_model=agent.model_name,
                ai_metadata={
                    "prompt": f"Generate {request.content_type} for {request.platform}",
                    "product_name": product_name,
                    "temperature": agent.temperature,
                    "max_tokens": agent.max_tokens,
                    "reel_script": ai_content.get("reel_script"),
                    "thumbnail_text": ai_content.get("thumbnail_text"),
                    "generation_timestamp": datetime.utcnow().isoformat()
                },
                media_urls=None,  # Will be populated when media is uploaded
                status="pending"  # Mark as pending approval
            )
            
            db.add(new_content)
            generated_content.append(new_content)
        
        # Commit all generated content
        db.commit()
        
        # Refresh to get database-generated IDs and timestamps
        for content in generated_content:
            db.refresh(content)
        
        # Step 6: Return generated content to frontend
        return ContentGenerateResponse(
            message=f"Successfully generated {request.count} content piece(s) for {request.platform}",
            generated_count=request.count,
            content=[ContentResponse.model_validate(c) for c in generated_content]
        )
        
    except Exception as e:
        # Rollback on error
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )

@content_router.get("/{content_id}", response_model=ContentDetailResponse)
def get_content_detail(
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific content piece.
    
    Args:
        content_id: UUID of the content
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Detailed content information
        
    Raises:
        HTTPException: If content not found or user doesn't own it
    """
    # Get content with campaign check
    content = db.query(GeneratedContent).join(Campaign).filter(
        GeneratedContent.id == content_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    return ContentDetailResponse.model_validate(content)

@content_router.put("/{content_id}/approve", response_model=ContentDetailResponse)
def approve_content(
    content_id: uuid.UUID,
    request: ContentApproveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve or reject generated content.
    
    This endpoint allows users to review and approve/reject AI-generated content.
    Approved content can be scheduled for posting.
    
    Args:
        content_id: UUID of the content
        request: Approval decision and optional feedback
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Updated content details
        
    Raises:
        HTTPException: If content not found or user doesn't own it
    """
    # Get content with campaign check
    content = db.query(GeneratedContent).join(Campaign).filter(
        GeneratedContent.id == content_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Update status based on approval decision
    if request.approved:
        content.status = "approved"
        # Store approval timestamp
        metadata = content.ai_metadata or {}
        metadata["approved_at"] = datetime.utcnow().isoformat()
        metadata["approved_by"] = str(current_user.id)
        content.ai_metadata = metadata
    else:
        content.status = "rejected"
        # Store rejection feedback and timestamp
        if request.feedback:
            metadata = content.ai_metadata or {}
            metadata["rejection_feedback"] = request.feedback
            metadata["rejected_at"] = datetime.utcnow().isoformat()
            metadata["rejected_by"] = str(current_user.id)
            content.ai_metadata = metadata
    
    content.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(content)
    
    return ContentDetailResponse.model_validate(content)

def _generate_placeholder_content(
    platform: str,
    content_type: str,
    product_name: str,
    product_description: str,
    index: int
) -> dict:
    """
    Generate placeholder content until AI integration is complete.
    
    Args:
        platform: Social media platform
        content_type: Type of content
        product_name: Name of the product
        product_description: Description of the product
        index: Content variation number
        
    Returns:
        Dictionary with caption, hashtags, script, thumbnail_text
        
    TODO: Replace with actual AI generation
    """
    # Platform-specific templates
    templates = {
        "instagram": {
            "post": {
                "caption": f"✨ Discover {product_name}! {product_description[:100]}... Perfect for your lifestyle! 💫 #NewProduct #Innovation",
                "hashtags": "#product #lifestyle #innovation #quality #musthave",
                "thumbnail_text": f"{product_name}\nNow Available"
            },
            "story": {
                "caption": f"Swipe up to learn more about {product_name}! 🔥",
                "hashtags": "#story #newlaunch",
                "thumbnail_text": f"NEW!\n{product_name}"
            },
            "reel": {
                "caption": f"Watch how {product_name} transforms your daily routine! 🎬",
                "hashtags": "#reels #trending #viral #product",
                "script": f"[0-3s] Hook: Show problem\n[3-7s] Introduce {product_name}\n[7-12s] Demonstrate benefits\n[12-15s] Call to action",
                "thumbnail_text": f"{product_name}\nGame Changer"
            }
        },
        "facebook": {
            "post": {
                "caption": f"Introducing {product_name}! 🎉\n\n{product_description[:150]}...\n\nLearn more and get yours today!",
                "hashtags": "#NewProduct #Innovation #Quality"
            }
        },
        "twitter": {
            "tweet": {
                "caption": f"🚀 Excited to introduce {product_name}! {product_description[:100]}... #Innovation #Product",
                "hashtags": "#tech #innovation #newproduct"
            }
        },
        "linkedin": {
            "post": {
                "caption": f"We're thrilled to announce {product_name}.\n\n{product_description[:200]}...\n\nThis represents our commitment to innovation and quality.",
                "hashtags": "#Business #Innovation #ProductLaunch"
            }
        }
    }
    
    # Get template for platform and content type
    platform_templates = templates.get(platform, templates["instagram"])
    content_template = platform_templates.get(content_type, platform_templates.get("post", {}))
    
    # Add variation to caption
    variations = [
        f" [Variation {index}]",
        f" - Version {index}",
        f" (Option {index})"
    ]
    
    result = {
        "caption": content_template.get("caption", f"Check out {product_name}!") + variations[index % 3],
        "hashtags": content_template.get("hashtags", "#product #new"),
        "script": content_template.get("script"),
        "thumbnail_text": content_template.get("thumbnail_text")
    }
    
    return result
