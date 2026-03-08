"""
Pydantic schemas for generated content endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class ContentGenerateRequest(BaseModel):
    """Content generation request schema"""
    platform: str = Field(..., pattern="^(instagram|facebook|twitter|linkedin)$")
    content_type: str = Field(..., pattern="^(post|story|reel|tweet)$")
    count: int = Field(default=1, ge=1, le=10, description="Number of content pieces to generate")
    tone: Optional[str] = Field(
        default="engaging",
        pattern="^(engaging|professional|casual|enthusiastic)$",
        description="Content tone"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "platform": "instagram",
                "content_type": "post",
                "count": 3,
                "tone": "engaging"
            }
        }

class ContentApproveRequest(BaseModel):
    """Content approval request schema"""
    approved: bool = Field(..., description="True to approve, False to reject")
    feedback: Optional[str] = Field(None, max_length=500, description="Optional feedback for rejected content")

    class Config:
        json_schema_extra = {
            "example": {
                "approved": True,
                "feedback": None
            }
        }

class ContentResponse(BaseModel):
    """Generated content response schema"""
    id: uuid.UUID
    campaign_id: uuid.UUID
    platform: str
    content_type: str
    caption: str
    hashtags: Optional[str]
    script: Optional[str] = None
    thumbnail_text: Optional[str] = None
    status: str
    ai_model: Optional[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def model_validate(cls, obj):
        """Custom validation to map content_text to caption"""
        if hasattr(obj, 'content_text'):
            data = {
                'id': obj.id,
                'campaign_id': obj.campaign_id,
                'platform': obj.platform,
                'content_type': obj.content_type,
                'caption': obj.content_text,
                'hashtags': obj.hashtags,
                'script': None,
                'thumbnail_text': None,
                'status': obj.status,
                'ai_model': obj.ai_model,
                'created_at': obj.created_at,
                'updated_at': obj.updated_at
            }
            return cls(**data)
        return super().model_validate(obj)

    class Config:
        from_attributes = True

class ContentDetailResponse(BaseModel):
    """Detailed content response with additional info"""
    id: uuid.UUID
    campaign_id: uuid.UUID
    platform: str
    content_type: str
    caption: str
    hashtags: Optional[str]
    script: Optional[str] = None
    thumbnail_text: Optional[str] = None
    status: str
    ai_model: Optional[str]
    ai_metadata: Optional[dict]
    media_urls: Optional[dict]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def model_validate(cls, obj):
        """Custom validation to map content_text to caption"""
        if hasattr(obj, 'content_text'):
            data = {
                'id': obj.id,
                'campaign_id': obj.campaign_id,
                'platform': obj.platform,
                'content_type': obj.content_type,
                'caption': obj.content_text,
                'hashtags': obj.hashtags,
                'script': None,
                'thumbnail_text': None,
                'status': obj.status,
                'ai_model': obj.ai_model,
                'ai_metadata': obj.ai_metadata,
                'media_urls': obj.media_urls,
                'created_at': obj.created_at,
                'updated_at': obj.updated_at
            }
            return cls(**data)
        return super().model_validate(obj)

    class Config:
        from_attributes = True

class ContentListResponse(BaseModel):
    """List of generated content"""
    content: list[ContentResponse]
    total: int
    by_status: dict = Field(
        default_factory=dict,
        description="Count of content by status"
    )
    by_platform: dict = Field(
        default_factory=dict,
        description="Count of content by platform"
    )

class ContentGenerateResponse(BaseModel):
    """Content generation response"""
    message: str
    generated_count: int
    content: list[ContentResponse]
