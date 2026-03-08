"""
File upload utilities for handling campaign assets.

For AWS S3 deployment:
- Replace local file storage with S3 uploads
- Use boto3 for S3 operations
- Store S3 URLs in database instead of local paths
"""

import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
import shutil

# Local storage configuration
UPLOAD_DIR = Path("uploads/campaign_assets")
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def validate_file_type(file: UploadFile) -> str:
    """
    Validate file type and return asset type.
    
    Args:
        file: Uploaded file
        
    Returns:
        Asset type: 'image' or 'video'
        
    Raises:
        ValueError: If file type is not allowed
    """
    content_type = file.content_type
    
    if content_type in ALLOWED_IMAGE_TYPES:
        return "image"
    elif content_type in ALLOWED_VIDEO_TYPES:
        return "video"
    else:
        raise ValueError(f"File type {content_type} is not allowed")

def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename to prevent collisions.
    
    Args:
        original_filename: Original file name
        
    Returns:
        Unique filename with UUID prefix
    """
    # Get file extension
    ext = Path(original_filename).suffix
    
    # Generate unique name
    unique_name = f"{uuid.uuid4()}{ext}"
    
    return unique_name

async def save_file_locally(file: UploadFile, campaign_id: str) -> tuple[str, str]:
    """
    Save uploaded file to local storage.
    
    Args:
        file: Uploaded file
        campaign_id: Campaign UUID
        
    Returns:
        Tuple of (file_path, file_name)
        
    Note:
        For production, replace with S3 upload
    """
    # Create campaign-specific directory
    campaign_dir = UPLOAD_DIR / str(campaign_id)
    campaign_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    file_path = campaign_dir / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return relative path for database storage
    relative_path = f"uploads/campaign_assets/{campaign_id}/{unique_filename}"
    
    return relative_path, unique_filename

"""
AWS S3 Upload Implementation (for production deployment)

Prerequisites:
    pip install boto3

Environment Variables:
    AWS_ACCESS_KEY_ID=your-access-key
    AWS_SECRET_ACCESS_KEY=your-secret-key
    AWS_REGION=us-east-1
    S3_BUCKET_NAME=your-bucket-name

Example Implementation:

import boto3
from botocore.exceptions import ClientError

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-east-1')
)

S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

async def upload_to_s3(file: UploadFile, campaign_id: str) -> tuple[str, str]:
    '''
    Upload file to AWS S3.
    
    Args:
        file: Uploaded file
        campaign_id: Campaign UUID
        
    Returns:
        Tuple of (s3_url, file_name)
        
    Raises:
        ClientError: If S3 upload fails
    '''
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    
    # S3 object key (path in bucket)
    s3_key = f"campaign_assets/{campaign_id}/{unique_filename}"
    
    # Determine content type
    content_type = file.content_type or 'application/octet-stream'
    
    try:
        # Upload file to S3
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={
                'ContentType': content_type,
                'ACL': 'public-read'  # Make file publicly accessible
            }
        )
        
        # Generate S3 URL
        s3_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
        
        return s3_url, unique_filename
        
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        raise

async def delete_from_s3(s3_key: str) -> bool:
    '''
    Delete file from S3.
    
    Args:
        s3_key: S3 object key
        
    Returns:
        True if successful, False otherwise
    '''
    try:
        s3_client.delete_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key
        )
        return True
    except ClientError as e:
        print(f"Error deleting from S3: {e}")
        return False

async def generate_presigned_url(s3_key: str, expiration: int = 3600) -> str:
    '''
    Generate a presigned URL for temporary access to private S3 objects.
    
    Args:
        s3_key: S3 object key
        expiration: URL expiration time in seconds (default: 1 hour)
        
    Returns:
        Presigned URL
    '''
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': s3_key
            },
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return ""

# Usage in routes:
# For production, replace save_file_locally with upload_to_s3
# file_path, file_name = await upload_to_s3(file, str(campaign_id))
"""

def get_file_size(file: UploadFile) -> int:
    """
    Get file size in bytes.
    
    Args:
        file: Uploaded file
        
    Returns:
        File size in bytes
    """
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    return size

def validate_file_size(file: UploadFile, max_size: int = MAX_FILE_SIZE) -> bool:
    """
    Validate file size.
    
    Args:
        file: Uploaded file
        max_size: Maximum allowed size in bytes
        
    Returns:
        True if valid, False otherwise
    """
    size = get_file_size(file)
    return size <= max_size
