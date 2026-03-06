"""S3 client wrapper for media storage operations."""

import os
from typing import Optional
import aioboto3
from botocore.exceptions import ClientError


class S3Client:
    """Async S3 client wrapper for uploading, retrieving, and deleting media files."""
    
    def __init__(self):
        """Initialize S3 client with bucket configuration from environment."""
        self.bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("AWS_S3_BUCKET_NAME environment variable is required")
        
        self.session = aioboto3.Session()
    
    async def upload_file(
        self,
        file_data: bytes,
        user_id: str,
        resource_type: str,
        file_id: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload a file to S3 with tenant-isolated key structure.
        
        Args:
            file_data: Binary file content
            user_id: User ID for tenant isolation
            resource_type: Type of resource (e.g., 'products', 'campaigns')
            file_id: Unique file identifier
            content_type: MIME type of the file
        
        Returns:
            S3 key of the uploaded file
        
        Raises:
            ClientError: If upload fails
        """
        # Construct key with tenant isolation: user_id/resource_type/file_id
        key = f"{user_id}/{resource_type}/{file_id}"
        
        async with self.session.client("s3") as s3:
            await s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_data,
                ContentType=content_type
            )
        
        return key
    
    async def generate_presigned_url(
        self,
        key: str,
        expiry_seconds: int = 300
    ) -> str:
        """
        Generate a presigned URL for temporary file access.
        
        Args:
            key: S3 object key
            expiry_seconds: URL expiry time in seconds (default: 300 = 5 minutes)
        
        Returns:
            Presigned URL string
        
        Raises:
            ClientError: If URL generation fails
        """
        async with self.session.client("s3") as s3:
            url = await s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": key
                },
                ExpiresIn=expiry_seconds
            )
        
        return url
    
    async def delete_file(self, key: str) -> None:
        """
        Delete a file from S3.
        
        Args:
            key: S3 object key to delete
        
        Raises:
            ClientError: If deletion fails
        """
        async with self.session.client("s3") as s3:
            await s3.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
    
    async def get_file(self, key: str) -> bytes:
        """
        Retrieve file content from S3.
        
        Args:
            key: S3 object key
        
        Returns:
            File content as bytes
        
        Raises:
            ClientError: If file retrieval fails
        """
        async with self.session.client("s3") as s3:
            response = await s3.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            async with response["Body"] as stream:
                return await stream.read()
