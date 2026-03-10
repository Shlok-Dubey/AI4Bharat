"""
AWS S3 Integration Module - Production Ready

This module provides functions for uploading media files to Amazon S3.
Used for storing campaign assets and media for Instagram posting.
"""

import boto3
from botocore.exceptions import ClientError
from typing import BinaryIO, Optional
import mimetypes
import uuid
import os
from config import settings

# Initialize S3 client
def get_s3_client():
    """Get boto3 S3 client"""
    return boto3.client(
        's3',
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )


def upload_media_to_s3(file_obj: BinaryIO, file_name: str, campaign_id: str = None) -> str:
    """
    Upload media file to S3 and return public URL.
    
    This function uploads image or video files to S3 with public-read ACL,
    making them accessible for Instagram Graph API.
    
    Args:
        file_obj: File object to upload (from FastAPI UploadFile)
        file_name: Original filename
        campaign_id: Optional campaign ID for organizing files
    
    Returns:
        str: Public S3 URL of the uploaded file
    
    Raises:
        ClientError: If upload fails
    
    Example:
        url = upload_media_to_s3(file.file, file.filename, campaign_id)
    """
    s3_client = get_s3_client()
    bucket_name = settings.S3_BUCKET_NAME
    
    if not bucket_name:
        raise ValueError("AWS_S3_BUCKET environment variable not set")
    
    # Generate unique filename to avoid collisions
    file_extension = os.path.splitext(file_name)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Construct S3 key with campaign organization
    if campaign_id:
        s3_key = f"campaign_assets/{campaign_id}/{unique_filename}"
    else:
        s3_key = f"media/{unique_filename}"
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(file_name)
    if not content_type:
        # Default content types for common media
        if file_extension.lower() in ['.jpg', '.jpeg']:
            content_type = 'image/jpeg'
        elif file_extension.lower() == '.png':
            content_type = 'image/png'
        elif file_extension.lower() == '.mp4':
            content_type = 'video/mp4'
        else:
            content_type = 'application/octet-stream'
    
    try:
        # Upload file (bucket policy provides public read access)
        s3_client.upload_fileobj(
            file_obj,
            bucket_name,
            s3_key,
            ExtraArgs={
                'ContentType': content_type,
                'CacheControl': 'max-age=31536000'  # Cache for 1 year
            }
        )
        
        # Return public S3 URL
        region = settings.AWS_REGION
        s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
        
        print(f"✅ Uploaded to S3: {s3_url}")
        return s3_url
        
    except ClientError as e:
        print(f"❌ Error uploading to S3: {e}")
        raise


def delete_media_from_s3(s3_url: str) -> bool:
    """
    Delete a media file from S3 using its URL.
    
    Args:
        s3_url: Full S3 URL of the file
    
    Returns:
        bool: True if successful, False otherwise
    """
    s3_client = get_s3_client()
    bucket_name = settings.S3_BUCKET_NAME
    
    try:
        # Extract S3 key from URL
        # Format: https://bucket.s3.region.amazonaws.com/key
        s3_key = s3_url.split('.amazonaws.com/')[-1]
        
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        print(f"✅ Deleted from S3: {s3_key}")
        return True
        
    except ClientError as e:
        print(f"❌ Error deleting from S3: {e}")
        return False


def validate_media_file(file_name: str, file_size: int) -> tuple[bool, str]:
    """
    Validate media file for Instagram requirements.
    
    Instagram requirements:
    - Images: JPG, PNG (max 8MB)
    - Videos: MP4 (max 100MB, 3-60 seconds)
    
    Args:
        file_name: Name of the file
        file_size: Size in bytes
    
    Returns:
        tuple: (is_valid, error_message)
    """
    file_extension = os.path.splitext(file_name)[1].lower()
    
    # Check file type
    allowed_image_types = ['.jpg', '.jpeg', '.png']
    allowed_video_types = ['.mp4']
    
    if file_extension in allowed_image_types:
        # Image validation
        max_size = 8 * 1024 * 1024  # 8MB
        if file_size > max_size:
            return False, f"Image file too large. Max size: 8MB, got: {file_size / 1024 / 1024:.2f}MB"
        return True, ""
        
    elif file_extension in allowed_video_types:
        # Video validation
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            return False, f"Video file too large. Max size: 100MB, got: {file_size / 1024 / 1024:.2f}MB"
        return True, ""
        
    else:
        return False, f"Unsupported file type: {file_extension}. Allowed: JPG, PNG, MP4"

