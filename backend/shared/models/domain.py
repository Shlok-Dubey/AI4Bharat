"""
Domain models for PostPilot AI.

These Pydantic models represent the core business entities and provide
serialization/deserialization to/from DynamoDB items.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr, field_validator
import uuid


class User(BaseModel):
    """User domain model."""
    
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Instagram OAuth
    instagram_access_token: Optional[str] = None
    instagram_refresh_token: Optional[str] = None
    instagram_token_expires_at: Optional[datetime] = None
    instagram_user_id: Optional[str] = None
    instagram_username: Optional[str] = None
    
    # Settings
    timezone: str = "UTC"
    daily_campaign_quota: int = 50
    campaigns_generated_today: int = 0
    quota_reset_date: Optional[datetime] = None
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format."""
        item = {
            'PK': f'USER#{self.user_id}',
            'user_id': self.user_id,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': int(self.created_at.timestamp()),
            'updated_at': int(self.updated_at.timestamp()),
            'timezone': self.timezone,
            'daily_campaign_quota': self.daily_campaign_quota,
            'campaigns_generated_today': self.campaigns_generated_today,
        }
        
        # Optional fields
        if self.instagram_access_token:
            item['instagram_access_token'] = self.instagram_access_token
        if self.instagram_refresh_token:
            item['instagram_refresh_token'] = self.instagram_refresh_token
        if self.instagram_token_expires_at:
            item['instagram_token_expires_at'] = int(self.instagram_token_expires_at.timestamp())
        if self.instagram_user_id:
            item['instagram_user_id'] = self.instagram_user_id
        if self.instagram_username:
            item['instagram_username'] = self.instagram_username
        if self.quota_reset_date:
            item['quota_reset_date'] = int(self.quota_reset_date.timestamp())
        
        return item
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'User':
        """Create User from DynamoDB item."""
        return cls(
            user_id=item['user_id'],
            email=item['email'],
            password_hash=item['password_hash'],
            created_at=datetime.fromtimestamp(item['created_at']),
            updated_at=datetime.fromtimestamp(item['updated_at']),
            instagram_access_token=item.get('instagram_access_token'),
            instagram_refresh_token=item.get('instagram_refresh_token'),
            instagram_token_expires_at=datetime.fromtimestamp(item['instagram_token_expires_at']) if item.get('instagram_token_expires_at') else None,
            instagram_user_id=item.get('instagram_user_id'),
            instagram_username=item.get('instagram_username'),
            timezone=item.get('timezone', 'UTC'),
            daily_campaign_quota=item.get('daily_campaign_quota', 50),
            campaigns_generated_today=item.get('campaigns_generated_today', 0),
            quota_reset_date=datetime.fromtimestamp(item['quota_reset_date']) if item.get('quota_reset_date') else None,
        )


class ImageAnalysis(BaseModel):
    """Image analysis results from Rekognition."""
    
    labels: List[str] = Field(default_factory=list)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    has_faces: bool = False
    dominant_colors: List[str] = Field(default_factory=list)
    detected_text: List[str] = Field(default_factory=list)
    is_safe: bool = True


class Product(BaseModel):
    """Product domain model."""
    
    product_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: str
    image_url: str
    image_s3_key: str
    
    # Image analysis
    image_analysis: Optional[ImageAnalysis] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format."""
        item = {
            'PK': f'USER#{self.user_id}',
            'SK': f'PRODUCT#{self.product_id}',
            'product_id': self.product_id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'image_url': self.image_url,
            'image_s3_key': self.image_s3_key,
            'created_at': int(self.created_at.timestamp()),
            'updated_at': int(self.updated_at.timestamp()),
        }
        
        if self.image_analysis:
            item['image_analysis'] = self.image_analysis.model_dump()
        
        if self.deleted_at:
            item['deleted_at'] = int(self.deleted_at.timestamp())
        
        return item
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'Product':
        """Create Product from DynamoDB item."""
        return cls(
            product_id=item['product_id'],
            user_id=item['user_id'],
            name=item['name'],
            description=item['description'],
            image_url=item['image_url'],
            image_s3_key=item['image_s3_key'],
            image_analysis=ImageAnalysis(**item['image_analysis']) if item.get('image_analysis') else None,
            created_at=datetime.fromtimestamp(item['created_at']),
            updated_at=datetime.fromtimestamp(item['updated_at']),
            deleted_at=datetime.fromtimestamp(item['deleted_at']) if item.get('deleted_at') else None,
        )


class Campaign(BaseModel):
    """Campaign domain model."""
    
    campaign_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    product_id: str
    
    # Generated content
    caption: str
    hashtags: List[str] = Field(default_factory=list)
    
    # Status
    status: str = "draft"  # draft, scheduled, publishing, published, failed, cancelled
    
    # Scheduling
    scheduled_time: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    # Instagram
    instagram_post_id: Optional[str] = None
    
    # Publishing attempts
    publish_attempts: int = 0
    last_error: Optional[str] = None
    
    # AI metadata
    bedrock_model_version: Optional[str] = None
    prompt_template_version: Optional[str] = None
    
    # Idempotency
    idempotency_key: Optional[str] = None
    
    # Analytics
    last_analytics_fetch: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format."""
        item = {
            'PK': f'USER#{self.user_id}',
            'SK': f'CAMPAIGN#{self.campaign_id}',
            'campaign_id': self.campaign_id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'caption': self.caption,
            'hashtags': self.hashtags,
            'status': self.status,
            'publish_attempts': self.publish_attempts,
            'created_at': int(self.created_at.timestamp()),
            'updated_at': int(self.updated_at.timestamp()),
        }
        
        # Optional fields
        if self.scheduled_time:
            item['scheduled_time'] = int(self.scheduled_time.timestamp())
        if self.published_at:
            item['published_at'] = int(self.published_at.timestamp())
        if self.instagram_post_id:
            item['instagram_post_id'] = self.instagram_post_id
        if self.last_error:
            item['last_error'] = self.last_error
        if self.bedrock_model_version:
            item['bedrock_model_version'] = self.bedrock_model_version
        if self.prompt_template_version:
            item['prompt_template_version'] = self.prompt_template_version
        if self.idempotency_key:
            item['idempotency_key'] = self.idempotency_key
        if self.last_analytics_fetch:
            item['last_analytics_fetch'] = int(self.last_analytics_fetch.timestamp())
        
        return item
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'Campaign':
        """Create Campaign from DynamoDB item."""
        return cls(
            campaign_id=item['campaign_id'],
            user_id=item['user_id'],
            product_id=item['product_id'],
            caption=item['caption'],
            hashtags=item.get('hashtags', []),
            status=item.get('status', 'draft'),
            scheduled_time=datetime.fromtimestamp(item['scheduled_time']) if item.get('scheduled_time') else None,
            published_at=datetime.fromtimestamp(item['published_at']) if item.get('published_at') else None,
            instagram_post_id=item.get('instagram_post_id'),
            publish_attempts=item.get('publish_attempts', 0),
            last_error=item.get('last_error'),
            bedrock_model_version=item.get('bedrock_model_version'),
            prompt_template_version=item.get('prompt_template_version'),
            idempotency_key=item.get('idempotency_key'),
            last_analytics_fetch=datetime.fromtimestamp(item['last_analytics_fetch']) if item.get('last_analytics_fetch') else None,
            created_at=datetime.fromtimestamp(item['created_at']),
            updated_at=datetime.fromtimestamp(item['updated_at']),
        )


class Analytics(BaseModel):
    """Analytics domain model for Instagram insights."""
    
    analytics_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    campaign_id: str
    user_id: str
    
    # Instagram metrics
    likes: int = 0
    comments: int = 0
    reach: int = 0
    impressions: int = 0
    engagement_rate: float = 0.0
    
    # Timestamp
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format."""
        return {
            'PK': f'CAMPAIGN#{self.campaign_id}',
            'SK': f'ANALYTICS#{int(self.fetched_at.timestamp())}',
            'analytics_id': self.analytics_id,
            'campaign_id': self.campaign_id,
            'user_id': self.user_id,
            'likes': self.likes,
            'comments': self.comments,
            'reach': self.reach,
            'impressions': self.impressions,
            'engagement_rate': float(self.engagement_rate),
            'fetched_at': int(self.fetched_at.timestamp()),
        }
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'Analytics':
        """Create Analytics from DynamoDB item."""
        return cls(
            analytics_id=item['analytics_id'],
            campaign_id=item['campaign_id'],
            user_id=item['user_id'],
            likes=item.get('likes', 0),
            comments=item.get('comments', 0),
            reach=item.get('reach', 0),
            impressions=item.get('impressions', 0),
            engagement_rate=float(item.get('engagement_rate', 0.0)),
            fetched_at=datetime.fromtimestamp(item['fetched_at']),
        )


class Memory(BaseModel):
    """Campaign Intelligence Memory domain model."""
    
    user_id: str
    memory_type: str  # business_profile, performance_insights, content_patterns, engagement_patterns
    data: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    sample_size: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format."""
        return {
            'PK': f'USER#{self.user_id}',
            'SK': f'MEMORY#{self.memory_type}',
            'user_id': self.user_id,
            'memory_type': self.memory_type,
            'data': self.data,
            'confidence': float(self.confidence),
            'sample_size': self.sample_size,
            'last_updated': int(self.last_updated.timestamp()),
            'created_at': int(self.created_at.timestamp()),
        }
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'Memory':
        """Create Memory from DynamoDB item."""
        return cls(
            user_id=item['user_id'],
            memory_type=item['memory_type'],
            data=item.get('data', {}),
            confidence=float(item.get('confidence', 0.0)),
            sample_size=item.get('sample_size', 0),
            last_updated=datetime.fromtimestamp(item['last_updated']),
            created_at=datetime.fromtimestamp(item['created_at']),
        )
