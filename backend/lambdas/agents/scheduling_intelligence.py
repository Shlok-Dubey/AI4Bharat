"""
Scheduling Intelligence Agent Lambda
Determines optimal posting time using engagement data
"""
import json
import os
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta
import sys

# Add shared directory to path for Lambda imports
sys.path.insert(0, '/opt/python')  # Lambda layer path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.utils.bedrock_client import BedrockClient
from repositories.memory_repository import MemoryRepository
from repositories.user_repository import UserRepository


async def determine_optimal_posting_time(
    user_id: str
) -> Dict[str, Any]:
    """
    Determine optimal posting time using historical engagement data.
    
    Args:
        user_id: User ID
    
    Returns:
        Dictionary with optimal posting time and reasoning
    """
    # Initialize clients
    bedrock = BedrockClient()
    memory_repo = MemoryRepository()
    user_repo = UserRepository()
    
    # Retrieve user for timezone
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    user_timezone = user.timezone
    
    # Retrieve engagement patterns from memory
    engagement_patterns = await memory_repo.get_memory(user_id, "engagement_patterns")
    
    # Build context for Bedrock
    patterns_context = {}
    if engagement_patterns and engagement_patterns.confidence > 0.3:
        patterns_context = engagement_patterns.data
    
    # Get current time in user's timezone
    current_time = datetime.utcnow()
    
    # Construct prompt for Bedrock
    system_prompt = """You are a social media scheduling expert specializing in Instagram engagement optimization. 
Your task is to determine the optimal posting time based on historical engagement patterns and audience behavior."""
    
    user_prompt = f"""Determine the optimal posting time for this user:

User Timezone: {user_timezone}
Current Time (UTC): {current_time.isoformat()}

Historical Engagement Patterns:
{json.dumps(patterns_context, indent=2) if patterns_context else "No past engagement data available"}

Based on this information, provide a scheduling recommendation in JSON format with the following structure:
{{
  "optimal_time_utc": "ISO 8601 datetime string in UTC",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation of why this time was chosen"
}}

Requirements:
- Recommend a time within the next 24-48 hours
- Consider the user's timezone and typical audience activity patterns
- If no historical data is available, recommend based on general Instagram best practices (weekday evenings, 6-9 PM in user's timezone)
- Provide confidence score based on available data (0.3-0.5 for no data, 0.6-0.8 for some data, 0.9+ for strong patterns)

Respond ONLY with valid JSON, no additional text."""
    
    # Call Bedrock for AI reasoning
    response_text = await bedrock.invoke_model(
        prompt=user_prompt,
        system_prompt=system_prompt,
        max_tokens=512,
        temperature=0.4  # Lower temperature for more consistent scheduling
    )
    
    # Parse JSON response
    try:
        scheduling = json.loads(response_text.strip())
    except json.JSONDecodeError:
        # Fallback: extract JSON from response if wrapped in text
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx >= 0 and end_idx > start_idx:
            scheduling = json.loads(response_text[start_idx:end_idx])
        else:
            raise ValueError("Failed to parse scheduling from Bedrock response")
    
    # Validate and parse the optimal time
    try:
        optimal_time = datetime.fromisoformat(scheduling["optimal_time_utc"].replace('Z', '+00:00'))
    except (ValueError, KeyError):
        # Fallback: recommend 24 hours from now at 6 PM user's timezone
        optimal_time = current_time + timedelta(hours=24)
        scheduling["optimal_time_utc"] = optimal_time.isoformat()
        scheduling["confidence"] = 0.3
        scheduling["reasoning"] = "Default recommendation: 24 hours from now"
    
    return scheduling


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for scheduling intelligence.
    
    Expected event format:
    {
        "user_id": "user-uuid"
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "optimal_time_utc": "2024-01-15T18:00:00+00:00",
            "confidence": 0.8,
            "reasoning": "..."
        }
    }
    """
    try:
        # Extract user_id from event
        user_id = event.get("user_id")
        
        if not user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "user_id is required"})
            }
        
        # Run async scheduling determination
        scheduling = asyncio.run(determine_optimal_posting_time(user_id))
        
        return {
            "statusCode": 200,
            "body": json.dumps(scheduling)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
