"""
AWS Bedrock Client - Active Integration

This module provides real AI content generation using AWS Bedrock.
"""

import boto3
import json
import os
from botocore.exceptions import ClientError
from typing import Dict, Optional


def get_bedrock_client():
    """Get boto3 Bedrock Runtime client"""
    return boto3.client(
        'bedrock-runtime',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )


def generate_social_content_with_bedrock(
    product_name: str,
    product_description: str,
    platform: str,
    content_type: str,
    tone: str = "engaging and professional"
) -> Dict[str, str]:
    """
    Generate social media content using AWS Bedrock (Claude)
    
    Args:
        product_name: Name of the product
        product_description: Description of the product
        platform: Target platform (instagram, facebook, etc.)
        content_type: Type of content (post, reel, story)
        tone: Desired tone for the content
    
    Returns:
        dict: Generated content with caption, hashtags, script, etc.
    """
    bedrock_client = get_bedrock_client()
    
    # Create comprehensive prompt based on content type
    if content_type == "reel":
        prompt = f"""You are a social media content expert. Generate engaging content for an Instagram Reel.

Product Name: {product_name}
Product Description: {product_description}
Tone: {tone}

Please generate the following in JSON format:
1. caption: An engaging caption for the reel (max 150 words, include emojis)
2. hashtags: 15-20 relevant and trending hashtags (space-separated)
3. reel_script: A detailed 30-second video script with scene descriptions and timing
4. thumbnail_text: Eye-catching text for thumbnail (max 5 words, all caps)

Make it viral-worthy and engaging. Use emojis appropriately.

Return ONLY valid JSON without any markdown formatting or code blocks."""

    else:  # Regular post
        prompt = f"""You are a social media content expert. Generate engaging content for {platform}.

Product Name: {product_name}
Product Description: {product_description}
Tone: {tone}

Please generate the following in JSON format:
1. caption: An engaging caption (max 150 words, include emojis)
2. hashtags: 15-20 relevant and trending hashtags (space-separated)

Make it engaging and shareable. Use emojis appropriately.

Return ONLY valid JSON without any markdown formatting or code blocks."""
    
    # Prepare request for Claude
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "temperature": 0.8,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        # Invoke Claude model
        model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
        
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        generated_text = response_body['content'][0]['text']
        
        # Clean up the response (remove markdown if present)
        generated_text = generated_text.strip()
        if generated_text.startswith('```json'):
            generated_text = generated_text[7:]
        if generated_text.startswith('```'):
            generated_text = generated_text[3:]
        if generated_text.endswith('```'):
            generated_text = generated_text[:-3]
        generated_text = generated_text.strip()
        
        # Parse JSON response
        content = json.loads(generated_text)
        
        return {
            "caption": content.get("caption", ""),
            "hashtags": content.get("hashtags", ""),
            "reel_script": content.get("reel_script", ""),
            "thumbnail_text": content.get("thumbnail_text", "")
        }
        
    except (ClientError, json.JSONDecodeError) as e:
        print(f"Error generating content with Bedrock: {e}")
        # Fallback to template if Bedrock fails
        return {
            "caption": f"Discover {product_name}! {product_description[:100]}... ✨",
            "hashtags": "#product #innovation #new #trending #viral #lifestyle #quality #amazing #musthave #shop",
            "reel_script": f"[0-5s] Hook: Introducing {product_name}!\n[5-15s] Show product features\n[15-25s] Benefits and use cases\n[25-30s] Call to action",
            "thumbnail_text": f"NEW {product_name.upper()}"
        }


def test_bedrock_connection() -> bool:
    """Test if Bedrock is accessible"""
    try:
        bedrock_client = get_bedrock_client()
        # Try to list models as a connection test
        boto3.client(
            'bedrock',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        ).list_foundation_models()
        return True
    except Exception as e:
        print(f"Bedrock connection test failed: {e}")
        return False
