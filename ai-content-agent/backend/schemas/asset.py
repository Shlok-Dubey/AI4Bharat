"""
Pydantic schemas for campaign asset endpoints.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class AssetUploadResponse(BaseModel):
    """Asset upload response schema"""
    id: uuid.UUID
    campaign_id: uuid.UUID
    asset_type: str
    file_name: str
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class AssetListResponse(BaseModel):
    """List of campaign assets"""
    assets: list[AssetUploadResponse]
    total: int

class AssetDeleteResponse(BaseModel):
    """Asset deletion response"""
    message: str
    deleted_asset_id: uuid.UUID
