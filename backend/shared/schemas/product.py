"""
Product request/response schemas.

Pydantic models for product creation, updates, and responses.

Requirements: 3.1, 10.3
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime


class ProductCreateRequest(BaseModel):
    """Request schema for product creation."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: str = Field(..., min_length=1, max_length=2000, description="Product description")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate product name is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError('Product name cannot be empty or whitespace only')
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate product description is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError('Product description cannot be empty or whitespace only')
        return v.strip()


class ProductUpdateRequest(BaseModel):
    """Request schema for product updates with optional fields."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, min_length=1, max_length=2000, description="Product description")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate product name if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Product name cannot be empty or whitespace only')
            return v.strip()
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate product description if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Product description cannot be empty or whitespace only')
            return v.strip()
        return v


class ImageAnalysisResponse(BaseModel):
    """Response schema for image analysis results."""
    
    labels: List[str] = Field(default_factory=list, description="Detected labels from image")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Confidence scores for labels")
    has_faces: bool = Field(default=False, description="Whether faces were detected")
    dominant_colors: List[str] = Field(default_factory=list, description="Dominant colors in image")
    detected_text: List[str] = Field(default_factory=list, description="Text detected in image")
    is_safe: bool = Field(default=True, description="Whether image passed content safety check")


class ProductResponse(BaseModel):
    """Response schema for product with all fields."""
    
    product_id: str = Field(..., description="Unique product identifier")
    user_id: str = Field(..., description="Owner user ID")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    image_url: str = Field(..., description="Public URL for product image")
    image_s3_key: str = Field(..., description="S3 key for product image")
    image_analysis: Optional[ImageAnalysisResponse] = Field(None, description="Image analysis results")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    updated_at: str = Field(..., description="Last update timestamp (ISO format)")
    deleted_at: Optional[str] = Field(None, description="Soft deletion timestamp (ISO format)")


class ProductListResponse(BaseModel):
    """Response schema for product listing with pagination."""
    
    products: List[ProductResponse] = Field(..., description="List of products")
    total: int = Field(..., description="Total number of products")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    has_more: bool = Field(..., description="Whether more pages are available")
