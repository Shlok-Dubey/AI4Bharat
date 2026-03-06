"""
Campaign Strategy Agent Lambda
Decides optimal campaign approach based on context and performance
"""
import json
import os
import asyncio
from typing import Dict, Any
import sys

# Add shared directory to path for Lambda imports
sys.path.insert(0, '/opt/python')  # Lambda layer path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.utils.bedrock_client import BedrockClient
from repositories.memory_repository import MemoryRepository
from repositories.product_repository import ProductRepository


async def determine_campaign_strategy(
    user_id: str,
    product_id: str,
    business_profile: Dict[str, Any],
    user_tone_preference: str = "auto"
) -> Dict[str, Any]:
    """
    Determine optimal campaign strategy based on context and past performance.
    
    Args:
        user_id: User ID
        product_id: Product ID
        business_profile: Business profile from Business Profiling Lambda
        user_tone_preference: User's preferred tone (default "auto")
    
    Returns:
        Campaign strategy dictionary
    """
    # Initialize clients
    bedrock = BedrockClient()
    memory_repo = MemoryRepository()
    product_repo = ProductRepository()
    
    # Retrieve product details
    product = await product_repo.get_by_id(user_id, product_id)
    if not product:
        raise ValueError(f"Product {product_id} not found")
    
    # Retrieve past performance insights from memory
    performance_insights = await memory_repo.get_memory(user_id, "performance_insights")
    
    # Build context for Bedrock
    product_context = {
        "name": product.name,
        "description": product.description
    }
    if product.image_analysis:
        product_context["labels"] = product.image_analysis.labels[:5]
        product_context["has_faces"] = product.image_analysis.has_faces
        product_context["dominant_colors"] = product.image_analysis.dominant_colors
    
    performance_context = {}
    if performance_insights and performance_insights.confidence > 0.3:
        performance_context = performance_insights.data
    
    # Construct prompt for Bedrock
    system_prompt = """You are a social media marketing strategist specializing in Instagram campaigns. 
Your task is to determine the optimal campaign strategy based on business context, product details, and past performance data."""
    
    user_prompt = f"""Determine the optimal campaign strategy for this product:

Business Profile:
{json.dumps(business_profile, indent=2)}

Product:
{json.dumps(product_context, indent=2)}

Past Performance Insights:
{json.dumps(performance_context, indent=2) if performance_context else "No past performance data available"}

User Tone Preference: {user_tone_preference}

Based on this information, provide a campaign strategy in JSON format with the following structure:
{{
  "tone": "recommended tone (e.g., luxury, casual, educational, inspirational)",
  "cta_style": "call-to-action style (e.g., question-based, direct, soft-sell)",
  "hook_pattern": "hook pattern to grab attention (e.g., problem-solution, benefit-first, storytelling)",
  "content_angle": "angle to approach the content (e.g., lifestyle, product-focused, value-driven)",
  "hashtag_strategy": "hashtag approach (e.g., niche-focused, broad-reach, community-building)"
}}

Consider:
- What has worked well in the past (if performance data available)
- The business's brand voice and target audience
- The product's unique characteristics
- Current Instagram best practices

Respond ONLY with valid JSON, no additional text."""
    
    # Call Bedrock for AI reasoning
    response_text = await bedrock.invoke_model(
        prompt=user_prompt,
        system_prompt=system_prompt,
        max_tokens=1024,
        temperature=0.5  # Moderate temperature for creative but consistent strategy
    )
    
    # Parse JSON response
    try:
        strategy = json.loads(response_text.strip())
    except json.JSONDecodeError:
        # Fallback: extract JSON from response if wrapped in text
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx >= 0 and end_idx > start_idx:
            strategy = json.loads(response_text[start_idx:end_idx])
        else:
            raise ValueError("Failed to parse strategy from Bedrock response")
    
    return strategy


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for campaign strategy.
    
    Expected event format:
    {
        "user_id": "user-uuid",
        "product_id": "product-uuid",
        "business_profile": {...},
        "user_tone_preference": "auto"  // optional
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "strategy": {...}
        }
    }
    """
    try:
        # Extract parameters from event
        user_id = event.get("user_id")
        product_id = event.get("product_id")
        business_profile = event.get("business_profile")
        user_tone_preference = event.get("user_tone_preference", "auto")
        
        if not user_id or not product_id or not business_profile:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "user_id, product_id, and business_profile are required"})
            }
        
        # Run async strategy determination
        strategy = asyncio.run(determine_campaign_strategy(
            user_id,
            product_id,
            business_profile,
            user_tone_preference
        ))
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "strategy": strategy
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
