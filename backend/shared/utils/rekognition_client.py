"""Rekognition client wrapper for image analysis operations."""

import asyncio
from typing import List, Dict, Any
import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError


class RekognitionClient:
    """Async Rekognition client wrapper for image analysis with retry logic."""
    
    def __init__(self):
        """Initialize Rekognition client with timeout and retry configuration."""
        # Configure timeouts: 5s connection, 10s response
        self.config = Config(
            connect_timeout=5,
            read_timeout=10,
            retries={"max_attempts": 0}  # We handle retries manually
        )
        
        self.session = aioboto3.Session()
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s
        self.min_confidence = 75.0
    
    async def _retry_operation(self, operation_func):
        """
        Execute an operation with retry logic and exponential backoff.
        
        Args:
            operation_func: Async function to execute
        
        Returns:
            Result from the operation
        
        Raises:
            ClientError: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await operation_func()
            
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                
                # Retry on throttling or server errors
                if error_code in ["ThrottlingException", "ProvisionedThroughputExceededException", "InternalServerError"]:
                    last_exception = e
                    
                    # If not the last attempt, wait and retry
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delays[attempt]
                        await asyncio.sleep(delay)
                        continue
                else:
                    # Don't retry on client errors
                    raise
            
            except Exception as e:
                # Retry on unexpected errors
                last_exception = e
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt]
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("Rekognition operation failed after all retries")
    
    async def detect_labels(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Detect labels in an image with minimum confidence threshold.
        
        Args:
            image_bytes: Image content as bytes
        
        Returns:
            List of detected labels with confidence scores and metadata
        
        Raises:
            ClientError: If detection fails after retries
        """
        async def _detect():
            async with self.session.client(
                "rekognition",
                config=self.config
            ) as rekognition:
                response = await rekognition.detect_labels(
                    Image={"Bytes": image_bytes},
                    MinConfidence=self.min_confidence,
                    MaxLabels=50
                )
                return response.get("Labels", [])
        
        return await self._retry_operation(_detect)
    
    async def detect_faces(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Detect faces in an image with detailed attributes.
        
        Args:
            image_bytes: Image content as bytes
        
        Returns:
            List of detected faces with attributes (age range, emotions, etc.)
        
        Raises:
            ClientError: If detection fails after retries
        """
        async def _detect():
            async with self.session.client(
                "rekognition",
                config=self.config
            ) as rekognition:
                response = await rekognition.detect_faces(
                    Image={"Bytes": image_bytes},
                    Attributes=["ALL"]
                )
                return response.get("FaceDetails", [])
        
        return await self._retry_operation(_detect)
    
    async def detect_moderation_labels(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Detect inappropriate or unsafe content in an image.
        
        Args:
            image_bytes: Image content as bytes
        
        Returns:
            List of moderation labels with confidence scores
        
        Raises:
            ClientError: If detection fails after retries
        """
        async def _detect():
            async with self.session.client(
                "rekognition",
                config=self.config
            ) as rekognition:
                response = await rekognition.detect_moderation_labels(
                    Image={"Bytes": image_bytes},
                    MinConfidence=self.min_confidence
                )
                return response.get("ModerationLabels", [])
        
        return await self._retry_operation(_detect)
    
    async def detect_text(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Detect text in an image.
        
        Args:
            image_bytes: Image content as bytes
        
        Returns:
            List of detected text with confidence scores and bounding boxes
        
        Raises:
            ClientError: If detection fails after retries
        """
        async def _detect():
            async with self.session.client(
                "rekognition",
                config=self.config
            ) as rekognition:
                response = await rekognition.detect_text(
                    Image={"Bytes": image_bytes}
                )
                return response.get("TextDetections", [])
        
        return await self._retry_operation(_detect)
    
    async def analyze_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Perform comprehensive image analysis including labels, faces, and moderation.
        
        Args:
            image_bytes: Image content as bytes
        
        Returns:
            Dictionary containing all analysis results
        
        Raises:
            ClientError: If any detection fails after retries
        """
        # Run all detections concurrently
        labels, faces, moderation_labels = await asyncio.gather(
            self.detect_labels(image_bytes),
            self.detect_faces(image_bytes),
            self.detect_moderation_labels(image_bytes)
        )
        
        return {
            "labels": labels,
            "faces": faces,
            "moderation_labels": moderation_labels,
            "has_faces": len(faces) > 0,
            "is_safe": len(moderation_labels) == 0
        }
