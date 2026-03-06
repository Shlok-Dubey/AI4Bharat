"""Bedrock client wrapper for AI agent reasoning and content generation."""

import os
import json
import asyncio
from typing import Dict, Any, Optional
import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError


class BedrockClient:
    """Async Bedrock Runtime client wrapper for Claude 3 Sonnet model invocation."""
    
    def __init__(self):
        """Initialize Bedrock client with timeout and retry configuration."""
        self.model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
        
        # Configure timeouts: 5s connection, 15s response
        self.config = Config(
            connect_timeout=5,
            read_timeout=15,
            retries={"max_attempts": 0}  # We handle retries manually
        )
        
        self.session = aioboto3.Session()
        self.max_retries = 3
        self.retry_delays = [2, 4, 8]  # Exponential backoff: 2s, 4s, 8s
    
    async def invoke_model(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Invoke Claude 3 Sonnet model with retry logic and exponential backoff.
        
        Args:
            prompt: User prompt for the model
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            system_prompt: Optional system prompt for context
        
        Returns:
            Generated text response from the model
        
        Raises:
            ClientError: If all retry attempts fail
        """
        # Construct request body for Claude 3
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        if system_prompt:
            request_body["system"] = system_prompt
        
        # Retry logic with exponential backoff
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.client(
                    "bedrock-runtime",
                    config=self.config
                ) as bedrock:
                    response = await bedrock.invoke_model(
                        modelId=self.model_id,
                        body=json.dumps(request_body),
                        contentType="application/json",
                        accept="application/json"
                    )
                    
                    # Parse response
                    response_body = json.loads(await response["body"].read())
                    
                    # Extract text from Claude 3 response format
                    if "content" in response_body and len(response_body["content"]) > 0:
                        return response_body["content"][0]["text"]
                    else:
                        raise ValueError("Unexpected response format from Bedrock")
            
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                
                # Retry on throttling or server errors
                if error_code in ["ThrottlingException", "ServiceUnavailableException", "InternalServerException"]:
                    last_exception = e
                    
                    # If not the last attempt, wait and retry
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delays[attempt]
                        await asyncio.sleep(delay)
                        continue
                else:
                    # Don't retry on client errors (validation, auth, etc.)
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
            raise RuntimeError("Bedrock invocation failed after all retries")
    
    async def invoke_model_with_streaming(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ):
        """
        Invoke Claude 3 Sonnet model with streaming response.
        
        Args:
            prompt: User prompt for the model
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            system_prompt: Optional system prompt for context
        
        Yields:
            Text chunks as they are generated
        
        Raises:
            ClientError: If invocation fails
        """
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        if system_prompt:
            request_body["system"] = system_prompt
        
        async with self.session.client(
            "bedrock-runtime",
            config=self.config
        ) as bedrock:
            response = await bedrock.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            # Process streaming response
            async for event in response["body"]:
                chunk = json.loads(event["chunk"]["bytes"])
                
                if chunk["type"] == "content_block_delta":
                    if "delta" in chunk and "text" in chunk["delta"]:
                        yield chunk["delta"]["text"]
