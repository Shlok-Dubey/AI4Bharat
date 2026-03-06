"""
Product management routes for local development API.

Implements product CRUD operations with image upload, analysis, and S3 storage.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 24.3
"""

import logging
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from datetime import datetime

from shared.schemas.product import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductResponse,
    ProductListResponse,
    ImageAnalysisResponse,
)
from shared.models.domain import Product, ImageAnalysis
from shared.services.auth_middleware import get_current_user
from shared.services.image_analysis_service import ImageAnalysisService
from shared.utils.s3_client import S3Client
from repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


def _image_analysis_to_response(analysis: ImageAnalysis) -> ImageAnalysisResponse:
    """Convert ImageAnalysis domain model to response schema."""
    return ImageAnalysisResponse(
        labels=analysis.labels,
        confidence_scores=analysis.confidence_scores,
        has_faces=analysis.has_faces,
        dominant_colors=analysis.dominant_colors,
        detected_text=analysis.detected_text,
        is_safe=analysis.is_safe,
    )


def _product_to_response(product: Product) -> ProductResponse:
    """Convert Product domain model to response schema."""
    return ProductResponse(
        product_id=product.product_id,
        user_id=product.user_id,
        name=product.name,
        description=product.description,
        image_url=product.image_url,
        image_s3_key=product.image_s3_key,
        image_analysis=_image_analysis_to_response(product.image_analysis) if product.image_analysis else None,
        created_at=product.created_at.isoformat(),
        updated_at=product.updated_at.isoformat(),
        deleted_at=product.deleted_at.isoformat() if product.deleted_at else None,
    )


async def _validate_image_file(file: UploadFile) -> bytes:
    """
    Validate image file format and size.
    
    Args:
        file: Uploaded file
        
    Returns:
        File content as bytes
        
    Raises:
        HTTPException: If validation fails
        
    Requirements: 3.2
    """
    # Validate content type
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Only JPEG and PNG are supported."
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB in bytes
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image file too large. Maximum size is 10MB."
        )
    
    return content


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """
    Create a new product with image upload and analysis.
    
    Steps:
    1. Validate image file (JPEG/PNG, max 10MB)
    2. Upload image to S3
    3. Analyze image with Rekognition
    4. Create product in database with user_id association
    5. Return product with image_url and analysis
    
    Requirements: 3.1, 3.2, 3.3
    """
    product_repo = ProductRepository()
    s3_client = S3Client()
    image_service = ImageAnalysisService()
    
    try:
        # Validate request data using Pydantic
        request = ProductCreateRequest(name=name, description=description)
        
        # Validate image file
        image_content = await _validate_image_file(image)
        
        # Generate unique product ID
        product_id = str(uuid.uuid4())
        
        # Upload image to S3
        file_extension = "jpg" if image.content_type == "image/jpeg" else "png"
        file_id = f"{product_id}.{file_extension}"
        
        s3_key = await s3_client.upload_file(
            file_data=image_content,
            user_id=user_id,
            resource_type="products",
            file_id=file_id,
            content_type=image.content_type
        )
        
        # Generate presigned URL for image access
        image_url = await s3_client.generate_presigned_url(s3_key, expiry_seconds=3600)
        
        # Analyze image with Rekognition
        image_analysis = None
        try:
            image_analysis = await image_service.analyze_image(image_content)
            logger.info(f"Image analysis completed for product: {product_id}")
        except Exception as e:
            # Log error but continue with product creation
            logger.error(f"Image analysis failed for product {product_id}: {e}")
        
        # Create product domain model
        product = Product(
            product_id=product_id,
            user_id=user_id,
            name=request.name,
            description=request.description,
            image_url=image_url,
            image_s3_key=s3_key,
            image_analysis=image_analysis,
        )
        
        # Save to database
        created_product = await product_repo.create(product)
        
        logger.info(f"Product created successfully: {product_id} for user: {user_id}")
        
        return _product_to_response(created_product)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Product creation failed"
        )


@router.get("", response_model=ProductListResponse)
async def list_products(
    page: int = 1,
    page_size: int = 20,
    user_id: str = Depends(get_current_user)
):
    """
    List all products for authenticated user with pagination.
    
    Steps:
    1. Filter by authenticated user_id
    2. Exclude soft-deleted products
    3. Support pagination
    4. Return list of products
    
    Requirements: 3.4
    """
    product_repo = ProductRepository()
    
    try:
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be >= 1"
            )
        
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100"
            )
        
        # Get all products for user (excluding soft-deleted)
        all_products = await product_repo.get_by_user(user_id, include_deleted=False)
        
        # Sort by created_at descending (newest first)
        all_products.sort(key=lambda p: p.created_at, reverse=True)
        
        # Calculate pagination
        total = len(all_products)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Get page of products
        page_products = all_products[start_idx:end_idx]
        
        # Check if more pages available
        has_more = end_idx < total
        
        logger.info(f"Listed {len(page_products)} products for user: {user_id} (page {page})")
        
        return ProductListResponse(
            products=[_product_to_response(p) for p in page_products],
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing products for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list products"
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get a specific product by ID.
    
    Verifies ownership before returning product.
    
    Requirements: 3.4
    """
    product_repo = ProductRepository()
    
    try:
        # Get product with tenant isolation
        product = await product_repo.get_by_id(user_id, product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        logger.info(f"Retrieved product: {product_id} for user: {user_id}")
        
        return _product_to_response(product)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id} for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get product"
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    request: ProductUpdateRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Update an existing product.
    
    Steps:
    1. Verify ownership
    2. Validate changes
    3. Update database record
    
    Requirements: 3.5
    """
    product_repo = ProductRepository()
    
    try:
        # Get existing product with tenant isolation
        product = await product_repo.get_by_id(user_id, product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Update fields if provided
        if request.name is not None:
            product.name = request.name
        
        if request.description is not None:
            product.description = request.description
        
        # Update timestamp
        product.updated_at = datetime.utcnow()
        
        # Save changes
        updated_product = await product_repo.update(product)
        
        logger.info(f"Product updated successfully: {product_id} for user: {user_id}")
        
        return _product_to_response(updated_product)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating product {product_id} for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Product update failed"
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Soft-delete a product.
    
    Steps:
    1. Verify ownership
    2. Soft-delete by setting deleted_at timestamp
    3. Keep record in database
    
    Requirements: 3.6, 24.3
    """
    product_repo = ProductRepository()
    
    try:
        # Soft delete with tenant isolation
        deleted = await product_repo.soft_delete(user_id, product_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or already deleted"
            )
        
        logger.info(f"Product soft-deleted successfully: {product_id} for user: {user_id}")
        
        # Return 204 No Content
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product {product_id} for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Product deletion failed"
        )
