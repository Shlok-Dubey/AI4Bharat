"""
Content Generation Agent Lambda
Generates engaging captions and hashtags
"""
import json
import os
import asyncio
from typing import Dict, Any, List
import sys

# Add shared directory to path for Lambda imports
sys.path.insert(0, '/opt/python')  # Lambda layer path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.utils.bedrock_client import BedrockClient
from shared.utils.hashtag_generator import generate_hashtags
from repositories.memory_repository import MemoryRepository
from repositories.product_repository import ProductRepository


async def generate_campaign_content(
    user_id: str,
    product_id: str,
    strategy: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate campaign content (caption and hashtags).
    
    Args:
        user_id: User ID
        product_id: Product ID
        strategy: Campaign strategy from Campaign Strategy Lambda
    
    Returns:
        Dictionary with caption and hashtags
    """
    # Initialize clients
    bedrock = BedrockClient()
    memory_repo = MemoryRepository()
    product_repo = ProductRepository()
    
    # Retrieve product details
    product = await product_repo.get_by_id(user_id, product_id)
    if not product:
        raise ValueError(f"Product {product_id} not found")
    
    # Retrieve best-performing content patterns from memory
    content_patterns = await memory_repo.get_memory(user_id, "content_patterns")
    
    # Build context for Bedrock
    product_context = {
        "name": product.name,
        "description": product.description
    }
    if product.image_analysis:
        product_context["labels"] = product.image_analysis.labels[:5]
        product_context["has_faces"] = product.image_analysis.has_faces
        product_context["dominant_colors"] = product.image_analysis.dominant_colors
    
    patterns_context = {}
    if content_patterns and content_patterns.confidence > 0.3:
        patterns_context = content_patterns.data
    
    # Construct prompt for Bedrock
    system_prompt = """You are a creative social media content writer specializing in Instagram captions. 
Your task is to generate engaging, authentic captions that drive engagement while matching the brand voice."""
    
    user_prompt = f"""Generate Instagram campaign content for this product:

Product:
{json.dumps(product_context, indent=2)}

Campaign Strategy:
{json.dumps(strategy, indent=2)}

Best-Performing Content Patterns:
{json.dumps(patterns_context, indent=2) if patterns_context else "No past content patterns available"}

Generate content in JSON format with the following structure:
{{
  "caption": "engaging caption (120-180 characters)",
  "suggested_hashtags": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"]
}}

Requirements:
- Caption should be {strategy.get('tone', 'engaging')} in tone
- Use {strategy.get('hook_pattern', 'benefit-first')} hook pattern
- Include a {strategy.get('cta_style', 'question-based')} call-to-action
- Keep caption between 120-180 characters
- Suggest 5 relevant hashtags (without # prefix)
- Make it feel authentic and human-written, not templated
- Incorporate the product's unique value proposition

Respond ONLY with valid JSON, no additional text."""
    
    # Call Bedrock for AI reasoning
    response_text = await bedrock.invoke_model(
        prompt=user_prompt,
        system_prompt=system_prompt,
        max_tokens=512,
        temperature=0.8  # Higher temperature for more creative content
    )
    
    # Parse JSON response
    try:
        content = json.loads(response_text.strip())
    except json.JSONDecodeError:
        # Fallback: extract JSON from response if wrapped in text
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx >= 0 and end_idx > start_idx:
            content = json.loads(response_text[start_idx:end_idx])
        else:
            raise ValueError("Failed to parse content from Bedrock response")
    
    # Apply hashtag generation algorithm
    suggested_hashtags = content.get("suggested_hashtags", [])
    product_labels = product.image_analysis.labels if product.image_analysis else None
    
    final_hashtags = generate_hashtags(
        suggested_hashtags=suggested_hashtags,
        product_labels=product_labels,
        max_hashtags=10
    )
    
    return {
        "caption": content.get("caption", ""),
        "hashtags": final_hashtags
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for content generation.
    
    Expected event format:
    {
        "user_id": "user-uuid",
        "product_id": "product-uuid",
        "strategy": {...}
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "caption": "...",
            "hashtags": ["#tag1", "#tag2", ...]
        }
    }
    """
    try:
        # Extract parameters from event
        user_id = event.get("user_id")
        product_id = event.get("product_id")
        strategy = event.get("strategy")
        
        if not user_id or not product_id or not strategy:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "user_id, product_id, and strategy are required"})
            }
        
        # Run async content generation
        content = asyncio.run(generate_campaign_content(
            user_id,
            product_id,
            strategy
        ))
        
        return {
            "statusCode": 200,
            "body": json.dumps(content)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
