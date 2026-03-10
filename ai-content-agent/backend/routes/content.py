"""
Generated content management routes.

This module handles CRUD operations for AI-generated campaign content.
Content generation uses AWS Bedrock for AI-powered content creation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from datetime import datetime
import uuid

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
    current_user = Depends(get_current_user),
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
        status_filter: Filter by status (draft, approved, rejected, scheduled, published)
        platform_filter: Filter by platform (instagram, facebook, twitter, linkedin)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
    Returns:
        List of generated content with statistics
        
    Raises:
        HTTPException: If campaign not found or user doesn't own it
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
    
    # Get all content for campaign
    all_content = dynamodb.get_generated_content_by_campaign(str(campaign_id))
    
    # Apply filters
    filtered_content = all_content
    
    if status_filter:
        # Support both 'draft' and 'pending' for backward compatibility
        if status_filter == "draft":
            filtered_content = [c for c in filtered_content if c.get('status') in ['draft', 'pending']]
        else:
            filtered_content = [c for c in filtered_content if c.get('status') == status_filter]
    
    if platform_filter:
        filtered_content = [c for c in filtered_content if c.get('platform') == platform_filter]
    
    # Sort by created_at descending
    filtered_content.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Apply pagination
    total = len(filtered_content)
    paginated_content = filtered_content[skip:skip + limit]
    
    # Calculate statistics
    status_counts = {}
    platform_counts = {}
    
    for content in all_content:
        content_status = content.get('status', 'unknown')
        content_platform = content.get('platform', 'unknown')
        
        status_counts[content_status] = status_counts.get(content_status, 0) + 1
        platform_counts[content_platform] = platform_counts.get(content_platform, 0) + 1
    
    # Build response
    content_responses = []
    for content in paginated_content:
        created_at = datetime.fromisoformat(content['created_at']) if isinstance(content['created_at'], str) else content['created_at']
        updated_at = datetime.fromisoformat(content['updated_at']) if isinstance(content['updated_at'], str) else content['updated_at']
        
        content_responses.append(ContentResponse(
            id=content['content_id'],
            campaign_id=uuid.UUID(content['campaign_id']),
            platform=content['platform'],
            content_type=content['content_type'],
            caption=content['content_text'],
            hashtags=content.get('hashtags'),
            script=content.get('ai_metadata', {}).get('reel_script'),
            thumbnail_text=content.get('ai_metadata', {}).get('thumbnail_text'),
            status=content['status'],
            ai_model=content.get('ai_model'),
            created_at=created_at,
            updated_at=updated_at
        ))
    
    return ContentListResponse(
        content=content_responses,
        total=total,
        by_status=status_counts,
        by_platform=platform_counts
    )

@router.post("/{campaign_id}/generate-content", response_model=ContentGenerateResponse)
def generate_campaign_content(
    campaign_id: uuid.UUID,
    request: ContentGenerateRequest,
    current_user = Depends(get_current_user)
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
    4. Save generated content to DynamoDB
    5. Mark content as 'pending' (awaiting approval)
    6. Return generated content to frontend
    
    Args:
        campaign_id: UUID of the campaign
        request: Content generation parameters (platform, content_type, count)
        current_user: Authenticated user from JWT token
        
    Returns:
        ContentGenerateResponse with generated content pieces
        
    Raises:
        HTTPException: If campaign not found or user doesn't own it
        
    Note:
        Currently uses template-based generation.
        For production: Replace with AWS Bedrock or OpenAI API.
    """
    import dynamodb_client as dynamodb
    
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
    
    # Step 2: Fetch campaign product information
    settings = campaign.get('campaign_settings', {})
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
            
            # Step 5: Save generated content to DynamoDB
            new_content = dynamodb.create_generated_content(
                campaign_id=str(campaign_id),
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
            
            generated_content.append(new_content)
        
        # Step 6: Return generated content to frontend
        content_responses = []
        for content in generated_content:
            # Parse datetime from ISO string
            created_at = datetime.fromisoformat(content['created_at']) if isinstance(content['created_at'], str) else content['created_at']
            updated_at = datetime.fromisoformat(content['updated_at']) if isinstance(content['updated_at'], str) else content['updated_at']
            
            content_responses.append(ContentResponse(
                id=content['content_id'],
                campaign_id=uuid.UUID(content['campaign_id']),
                platform=content['platform'],
                content_type=content['content_type'],
                caption=content['content_text'],  # Map content_text to caption
                hashtags=content.get('hashtags'),
                script=content.get('ai_metadata', {}).get('reel_script'),
                thumbnail_text=content.get('ai_metadata', {}).get('thumbnail_text'),
                status=content['status'],
                ai_model=content.get('ai_model'),
                created_at=created_at,
                updated_at=updated_at
            ))
        
        return ContentGenerateResponse(
            message=f"Successfully generated {request.count} content piece(s) for {request.platform}",
            generated_count=request.count,
            content=content_responses
        )
        
    except Exception as e:
        import traceback
        print(f"❌ Error generating content:")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )

@content_router.get("/{content_id}", response_model=ContentDetailResponse)
def get_content_detail(
    content_id: uuid.UUID,
    current_user = Depends(get_current_user)
):
    """
    Get detailed information about a specific content piece.
    
    Args:
        content_id: UUID of the content
        current_user: Authenticated user from JWT token
        
    Returns:
        Detailed content information
        
    Raises:
        HTTPException: If content not found or user doesn't own it
    """
    import dynamodb_client as dynamodb
    
    # Get content
    content = dynamodb.get_generated_content(str(content_id))
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Verify user owns the campaign
    campaign = dynamodb.get_campaign(content['campaign_id'])
    
    if not campaign or campaign.get('user_id') != current_user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this content"
        )
    
    # Parse datetime
    created_at = datetime.fromisoformat(content['created_at']) if isinstance(content['created_at'], str) else content['created_at']
    updated_at = datetime.fromisoformat(content['updated_at']) if isinstance(content['updated_at'], str) else content['updated_at']
    
    return ContentDetailResponse(
        id=content['content_id'],
        campaign_id=uuid.UUID(content['campaign_id']),
        platform=content['platform'],
        content_type=content['content_type'],
        caption=content['content_text'],
        hashtags=content.get('hashtags'),
        script=content.get('ai_metadata', {}).get('reel_script'),
        thumbnail_text=content.get('ai_metadata', {}).get('thumbnail_text'),
        status=content['status'],
        ai_model=content.get('ai_model'),
        ai_metadata=content.get('ai_metadata'),
        media_urls=content.get('media_urls'),
        created_at=created_at,
        updated_at=updated_at
    )

@content_router.put("/{content_id}/approve", response_model=ContentDetailResponse)
def approve_content(
    content_id: uuid.UUID,
    request: ContentApproveRequest,
    current_user = Depends(get_current_user)
):
    """
    Approve or reject generated content.
    
    This endpoint allows users to review and approve/reject AI-generated content.
    Approved content can be scheduled for posting.
    
    Args:
        content_id: UUID of the content
        request: Approval decision and optional feedback
        current_user: Authenticated user from JWT token
        
    Returns:
        Updated content details
        
    Raises:
        HTTPException: If content not found or user doesn't own it
    """
    import dynamodb_client as dynamodb
    
    # Get content
    content = dynamodb.get_generated_content(str(content_id))
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Verify user owns the campaign
    campaign = dynamodb.get_campaign(content['campaign_id'])
    
    if not campaign or campaign.get('user_id') != current_user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this content"
        )
    
    # Update status based on approval decision
    metadata = content.get('ai_metadata', {})
    
    if request.approved:
        new_status = "approved"
        metadata["approved_at"] = datetime.utcnow().isoformat()
        metadata["approved_by"] = current_user['user_id']
    else:
        new_status = "rejected"
        if request.feedback:
            metadata["rejection_feedback"] = request.feedback
        metadata["rejected_at"] = datetime.utcnow().isoformat()
        metadata["rejected_by"] = current_user['user_id']
    
    # Update content in DynamoDB
    updated_content = dynamodb.update_generated_content(
        str(content_id),
        status=new_status,
        ai_metadata=metadata
    )
    
    # Parse datetime
    created_at = datetime.fromisoformat(updated_content['created_at']) if isinstance(updated_content['created_at'], str) else updated_content['created_at']
    updated_at = datetime.fromisoformat(updated_content['updated_at']) if isinstance(updated_content['updated_at'], str) else updated_content['updated_at']
    
    return ContentDetailResponse(
        id=updated_content['content_id'],
        campaign_id=uuid.UUID(updated_content['campaign_id']),
        platform=updated_content['platform'],
        content_type=updated_content['content_type'],
        caption=updated_content['content_text'],
        hashtags=updated_content.get('hashtags'),
        script=updated_content.get('ai_metadata', {}).get('reel_script'),
        thumbnail_text=updated_content.get('ai_metadata', {}).get('thumbnail_text'),
        status=updated_content['status'],
        ai_model=updated_content.get('ai_model'),
        ai_metadata=updated_content.get('ai_metadata'),
        media_urls=updated_content.get('media_urls'),
        created_at=created_at,
        updated_at=updated_at
    )

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
