"""
Business Profiling Agent Lambda
Understands business identity, target audience, and brand voice
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
from shared.models.domain import Memory


async def analyze_business_profile(user_id: str) -> Dict[str, Any]:
    """
    Analyze business context and generate business profile.
    
    Args:
        user_id: User ID
    
    Returns:
        Business profile dictionary
    """
    # Initialize clients
    bedrock = BedrockClient()
    memory_repo = MemoryRepository()
    product_repo = ProductRepository()
    
    # Retrieve existing business profile from memory
    existing_profile = await memory_repo.get_memory(user_id, "business_profile")
    
    # Retrieve user's products for context
    products = await product_repo.get_by_user(user_id)
    
    # Build context for Bedrock
    product_context = []
    for product in products[:10]:  # Limit to 10 most recent products
        product_info = {
            "name": product.name,
            "description": product.description
        }
        if product.image_analysis:
            product_info["labels"] = product.image_analysis.labels[:5]
        product_context.append(product_info)
    
    # Construct prompt for Bedrock
    system_prompt = """You are a business intelligence analyst specializing in understanding business identity and brand positioning. 
Your task is to analyze a business's products and infer their business type, target audience, brand voice, and value propositions."""
    
    user_prompt = f"""Analyze the following business based on their product catalog:

Products:
{json.dumps(product_context, indent=2)}

Based on this information, provide a comprehensive business profile in JSON format with the following structure:
{{
  "business_type": "brief description of the business type",
  "target_audience": {{
    "demographics": "age range and characteristics",
    "interests": ["interest1", "interest2"],
    "values": ["value1", "value2"]
  }},
  "brand_voice": {{
    "tone": "overall tone description",
    "personality_traits": ["trait1", "trait2", "trait3"],
    "language_style": "description of language style"
  }},
  "value_propositions": ["proposition1", "proposition2"]
}}

Respond ONLY with valid JSON, no additional text."""
    
    # Call Bedrock for AI reasoning
    response_text = await bedrock.invoke_model(
        prompt=user_prompt,
        system_prompt=system_prompt,
        max_tokens=1024,
        temperature=0.3  # Lower temperature for more consistent analysis
    )
    
    # Parse JSON response
    try:
        business_profile = json.loads(response_text.strip())
    except json.JSONDecodeError:
        # Fallback: extract JSON from response if wrapped in text
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx >= 0 and end_idx > start_idx:
            business_profile = json.loads(response_text[start_idx:end_idx])
        else:
            raise ValueError("Failed to parse business profile from Bedrock response")
    
    # Update memory with new profile
    confidence = 0.5 if len(products) < 5 else 0.8  # Higher confidence with more products
    memory = Memory(
        user_id=user_id,
        memory_type="business_profile",
        data=business_profile,
        confidence=confidence,
        sample_size=len(products)
    )
    await memory_repo.update_memory(memory)
    
    return business_profile


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for business profiling.
    
    Expected event format:
    {
        "user_id": "user-uuid"
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "business_profile": {...}
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
        
        # Run async analysis
        business_profile = asyncio.run(analyze_business_profile(user_id))
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "business_profile": business_profile
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
