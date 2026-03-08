"""
Campaign and campaign asset models.

For AWS DynamoDB deployment:
- Convert to PynamoDB models
- Use JSONAttribute for metadata and settings
- Use ListAttribute for tags
- Define GSI on user_id for user campaign lookups
"""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from base import Base
from utils.guid import GUID

class Campaign(Base):
    """
    Campaign model for managing social media campaigns.
    
    DynamoDB equivalent:
    - table_name = 'campaigns'
    - Hash key: id (UnicodeAttribute)
    - GSI on user_id for filtering user campaigns
    - Use JSONAttribute for settings
    """
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        nullable=False
    )  # draft, active, paused, completed
    target_platforms: Mapped[dict] = mapped_column(
        JSON,
        nullable=True
    )  # e.g., {"twitter": true, "facebook": true}
    campaign_settings: Mapped[dict] = mapped_column(
        JSON,
        nullable=True
    )  # AI settings, tone, style preferences
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="campaigns")
    assets: Mapped[list["CampaignAsset"]] = relationship(
        "CampaignAsset",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    generated_content: Mapped[list["GeneratedContent"]] = relationship(
        "GeneratedContent",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Campaign(id={self.id}, name={self.name}, status={self.status})>"


class CampaignAsset(Base):
    """
    Campaign asset model for storing uploaded files and media.
    
    DynamoDB equivalent:
    - table_name = 'campaign_assets'
    - Hash key: id (UnicodeAttribute)
    - GSI on campaign_id for campaign asset lookups
    - Store file_path as S3 URL for AWS deployment
    """
    __tablename__ = "campaign_assets"

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
    asset_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )  # image, video, document, logo
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )  # Local path or S3 URL for AWS
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)  # in bytes
    mime_type: Mapped[str] = mapped_column(String(100), nullable=True)
    asset_metadata: Mapped[dict] = mapped_column(
        "metadata",  # Column name in database
        JSON,
        nullable=True
    )  # dimensions, duration, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="assets")

    def __repr__(self):
        return f"<CampaignAsset(id={self.id}, type={self.asset_type}, name={self.file_name})>"
