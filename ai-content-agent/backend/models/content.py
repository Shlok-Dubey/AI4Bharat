"""
Content generation, scheduling, and analytics models.

For AWS DynamoDB deployment:
- Convert to PynamoDB models
- Use JSONAttribute for metadata and analytics_data
- Use NumberAttribute for engagement metrics
- Define GSI on campaign_id and scheduled_for for queries
"""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, JSON, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from base import Base
from utils.guid import GUID

class GeneratedContent(Base):
    """
    Generated content model for AI-created social media posts.
    
    DynamoDB equivalent:
    - table_name = 'generated_content'
    - Hash key: id (UnicodeAttribute)
    - GSI on campaign_id for campaign content lookups
    - Use JSONAttribute for ai_metadata
    """
    __tablename__ = "generated_content"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )  # twitter, facebook, instagram, linkedin
    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )  # post, story, reel, tweet
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[str] = mapped_column(Text, nullable=True)  # Comma-separated
    media_urls: Mapped[dict] = mapped_column(
        JSON,
        nullable=True
    )  # List of media URLs
    ai_model: Mapped[str] = mapped_column(String(100), nullable=True)  # e.g., 'gpt-4', 'claude-3'
    ai_metadata: Mapped[dict] = mapped_column(
        JSON,
        nullable=True
    )  # prompt, temperature, tokens used
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        nullable=False
    )  # draft, approved, rejected, scheduled, published
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="generated_content")
    scheduled_posts: Mapped[list["ScheduledPost"]] = relationship(
        "ScheduledPost",
        back_populates="content",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<GeneratedContent(id={self.id}, platform={self.platform}, status={self.status})>"


class ScheduledPost(Base):
    """
    Scheduled post model for managing post publishing schedule.
    
    DynamoDB equivalent:
    - table_name = 'scheduled_posts'
    - Hash key: id (UnicodeAttribute)
    - GSI on content_id for content lookups
    - GSI on scheduled_for for time-based queries
    - Use UTCDateTimeAttribute for scheduled_for
    """
    __tablename__ = "scheduled_posts"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("generated_content.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False
    )  # pending, published, failed, cancelled
    platform_post_id: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )  # ID from social media platform after publishing
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    content: Mapped["GeneratedContent"] = relationship(
        "GeneratedContent",
        back_populates="scheduled_posts"
    )
    analytics: Mapped[list["PostAnalytics"]] = relationship(
        "PostAnalytics",
        back_populates="scheduled_post",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ScheduledPost(id={self.id}, scheduled_for={self.scheduled_for}, status={self.status})>"


class PostAnalytics(Base):
    """
    Post analytics model for tracking engagement metrics.
    
    DynamoDB equivalent:
    - table_name = 'post_analytics'
    - Hash key: id (UnicodeAttribute)
    - GSI on scheduled_post_id for post analytics lookups
    - Use NumberAttribute for all metric fields
    - Use UTCDateTimeAttribute for fetched_at
    """
    __tablename__ = "post_analytics"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4
    )
    scheduled_post_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("scheduled_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reach: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shares: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    analytics_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=True
    )  # Platform-specific additional metrics
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    scheduled_post: Mapped["ScheduledPost"] = relationship(
        "ScheduledPost",
        back_populates="analytics"
    )

    def __repr__(self):
        return f"<PostAnalytics(id={self.id}, likes={self.likes}, engagement_rate={self.engagement_rate})>"
