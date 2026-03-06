"""SQS client wrapper for asynchronous job queue management."""

import os
import json
from typing import List, Dict, Any, Optional
import aioboto3
from botocore.exceptions import ClientError


class SQSClient:
    """Async SQS client wrapper for sending, receiving, and managing queue messages."""
    
    def __init__(self):
        """Initialize SQS client with queue configuration from environment."""
        self.queue_url = os.getenv("AWS_SQS_QUEUE_URL")
        if not self.queue_url:
            raise ValueError("AWS_SQS_QUEUE_URL environment variable is required")
        
        self.session = aioboto3.Session()
    
    async def send_message(
        self,
        message_body: Dict[str, Any],
        deduplication_id: Optional[str] = None,
        group_id: Optional[str] = None,
        delay_seconds: int = 0
    ) -> str:
        """
        Send a message to the SQS queue with optional deduplication.
        
        Args:
            message_body: Message payload as dictionary
            deduplication_id: Message deduplication ID for FIFO queues
            group_id: Message group ID for FIFO queues
            delay_seconds: Delay before message becomes available (0-900 seconds)
        
        Returns:
            Message ID
        
        Raises:
            ClientError: If message send fails
        """
        async with self.session.client("sqs") as sqs:
            params = {
                "QueueUrl": self.queue_url,
                "MessageBody": json.dumps(message_body),
                "DelaySeconds": delay_seconds
            }
            
            # Add FIFO queue parameters if provided
            if deduplication_id:
                params["MessageDeduplicationId"] = deduplication_id
            if group_id:
                params["MessageGroupId"] = group_id
            
            response = await sqs.send_message(**params)
            return response["MessageId"]
    
    async def receive_messages(
        self,
        max_messages: int = 1,
        wait_time_seconds: int = 20,
        visibility_timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Receive messages from the SQS queue with long polling.
        
        Args:
            max_messages: Maximum number of messages to retrieve (1-10)
            wait_time_seconds: Long polling wait time (0-20 seconds)
            visibility_timeout: Message visibility timeout in seconds
        
        Returns:
            List of message dictionaries with 'MessageId', 'ReceiptHandle', and 'Body'
        
        Raises:
            ClientError: If message retrieval fails
        """
        async with self.session.client("sqs") as sqs:
            response = await sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time_seconds,
                VisibilityTimeout=visibility_timeout,
                AttributeNames=["All"],
                MessageAttributeNames=["All"]
            )
            
            messages = response.get("Messages", [])
            
            # Parse JSON body for each message
            for message in messages:
                try:
                    message["Body"] = json.loads(message["Body"])
                except json.JSONDecodeError:
                    # Keep original body if not valid JSON
                    pass
            
            return messages
    
    async def delete_message(self, receipt_handle: str) -> None:
        """
        Delete a message from the queue after successful processing.
        
        Args:
            receipt_handle: Receipt handle from received message
        
        Raises:
            ClientError: If message deletion fails
        """
        async with self.session.client("sqs") as sqs:
            await sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
    
    async def change_message_visibility(
        self,
        receipt_handle: str,
        visibility_timeout: int
    ) -> None:
        """
        Change the visibility timeout of a message.
        
        Useful for extending processing time or making a message immediately available.
        
        Args:
            receipt_handle: Receipt handle from received message
            visibility_timeout: New visibility timeout in seconds (0-43200)
        
        Raises:
            ClientError: If visibility change fails
        """
        async with self.session.client("sqs") as sqs:
            await sqs.change_message_visibility(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=visibility_timeout
            )
    
    async def get_queue_attributes(self) -> Dict[str, Any]:
        """
        Get queue attributes including message count and depth.
        
        Returns:
            Dictionary of queue attributes
        
        Raises:
            ClientError: If attribute retrieval fails
        """
        async with self.session.client("sqs") as sqs:
            response = await sqs.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=["All"]
            )
            return response.get("Attributes", {})
