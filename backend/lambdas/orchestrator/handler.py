"""
Agent Orchestrator Lambda
Coordinates multi-agent workflow for campaign generation
"""
import json
import os
import asyncio
from typing import Dict, Any
from datetime import datetime
import sys
import boto3

# Add shared directory to path for Lambda imports
sys.path.insert(0, '/opt/python')  # Lambda layer path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from repositories.campaign_repository import CampaignRepository
from shared.models.domain import Campaign


# Initialize Lambda client for invoking other Lambdas
lambda_client = boto3.client('lambda')

# Lambda function names from environment
BUSINESS_PROFILING_LAMBDA = os.getenv('BUSINESS_PROFILING_LAMBDA', 'business-profiling')
CAMPAIGN_STRATEGY_LAMBDA = os.getenv('CAMPAIGN_STRATEGY_LAMBDA', 'campaign-strategy')
CONTENT_GENERATION_LAMBDA = os.getenv('CONTENT_GENERATION_LAMBDA', 'content-generation')
SCHEDULING_INTELLIGENCE_LAMBDA = os.getenv('SCHEDULING_INTELLIGENCE_LAMBDA', 'scheduling-intelligence')

# Bedrock model version tracking
BEDROCK_MODEL_VERSION = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
PROMPT_TEMPLATE_VERSION = os.getenv('PROMPT_TEMPLATE_VERSION', 'v1.0')


async def invoke_lambda_async(function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke a Lambda function asynchronously.
    
    Args:
        function_name: Name of the Lambda function
        payload: Payload to send to the Lambda
    
    Returns:
        Response from the Lambda function
    """
    loop = asyncio.get_event_loop()
    
    # Run Lambda invocation in thread pool to avoid blocking
    response = await loop.run_in_executor(
        None,
        lambda: lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
    )
    
    # Parse response
    response_payload = json.loads(response['Payload'].read())
    
    # Check for errors
    if response_payload.get('statusCode') != 200:
        error_body = json.loads(response_payload.get('body', '{}'))
        raise RuntimeError(f"Lambda {function_name} failed: {error_body.get('error', 'Unknown error')}")
    
    # Parse body
    body = json.loads(response_payload.get('body', '{}'))
    return body


async def orchestrate_campaign_generation(
    user_id: str,
    product_id: str,
    user_tone_preference: str = "auto",
    idempotency_key: str = None
) -> Campaign:
    """
    Orchestrate multi-agent workflow for campaign generation.
    
    Workflow:
    1. Invoke Business Profiling Lambda
    2. Invoke Campaign Strategy Lambda with profile
    3. Invoke Content Generation Lambda with strategy
    4. Invoke Scheduling Intelligence Lambda
    5. Aggregate all agent outputs
    6. Store campaign in DynamoDB
    
    Args:
        user_id: User ID
        product_id: Product ID
        user_tone_preference: User's preferred tone (default "auto")
        idempotency_key: Optional idempotency key
    
    Returns:
        Created Campaign
    """
    # Step 1: Invoke Business Profiling Lambda
    business_profile_response = await invoke_lambda_async(
        BUSINESS_PROFILING_LAMBDA,
        {"user_id": user_id}
    )
    business_profile = business_profile_response.get("business_profile", {})
    
    # Step 2: Invoke Campaign Strategy Lambda
    strategy_response = await invoke_lambda_async(
        CAMPAIGN_STRATEGY_LAMBDA,
        {
            "user_id": user_id,
            "product_id": product_id,
            "business_profile": business_profile,
            "user_tone_preference": user_tone_preference
        }
    )
    strategy = strategy_response.get("strategy", {})
    
    # Step 3: Invoke Content Generation Lambda
    content_response = await invoke_lambda_async(
        CONTENT_GENERATION_LAMBDA,
        {
            "user_id": user_id,
            "product_id": product_id,
            "strategy": strategy
        }
    )
    caption = content_response.get("caption", "")
    hashtags = content_response.get("hashtags", [])
    
    # Step 4: Invoke Scheduling Intelligence Lambda
    scheduling_response = await invoke_lambda_async(
        SCHEDULING_INTELLIGENCE_LAMBDA,
        {"user_id": user_id}
    )
    optimal_time_utc = scheduling_response.get("optimal_time_utc")
    
    # Parse optimal time
    scheduled_time = None
    if optimal_time_utc:
        try:
            scheduled_time = datetime.fromisoformat(optimal_time_utc.replace('Z', '+00:00'))
        except ValueError:
            pass  # Leave as None if parsing fails
    
    # Step 5: Create Campaign object
    campaign = Campaign(
        user_id=user_id,
        product_id=product_id,
        caption=caption,
        hashtags=hashtags,
        status="draft",
        scheduled_time=scheduled_time,
        bedrock_model_version=BEDROCK_MODEL_VERSION,
        prompt_template_version=PROMPT_TEMPLATE_VERSION,
        idempotency_key=idempotency_key
    )
    
    # Step 6: Store campaign in DynamoDB
    campaign_repo = CampaignRepository()
    created_campaign = await campaign_repo.create(campaign)
    
    return created_campaign


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for agent orchestration.
    
    Expected event format:
    {
        "user_id": "user-uuid",
        "product_id": "product-uuid",
        "user_tone_preference": "auto",  // optional
        "idempotency_key": "unique-key"  // optional
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "campaign": {...}
        }
    }
    """
    try:
        # Extract parameters from event
        user_id = event.get("user_id")
        product_id = event.get("product_id")
        user_tone_preference = event.get("user_tone_preference", "auto")
        idempotency_key = event.get("idempotency_key")
        
        if not user_id or not product_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "user_id and product_id are required"})
            }
        
        # Run async orchestration
        campaign = asyncio.run(orchestrate_campaign_generation(
            user_id,
            product_id,
            user_tone_preference,
            idempotency_key
        ))
        
        # Convert campaign to dict for JSON serialization
        campaign_dict = {
            "campaign_id": campaign.campaign_id,
            "user_id": campaign.user_id,
            "product_id": campaign.product_id,
            "caption": campaign.caption,
            "hashtags": campaign.hashtags,
            "status": campaign.status,
            "scheduled_time": campaign.scheduled_time.isoformat() if campaign.scheduled_time else None,
            "bedrock_model_version": campaign.bedrock_model_version,
            "prompt_template_version": campaign.prompt_template_version,
            "created_at": campaign.created_at.isoformat(),
            "updated_at": campaign.updated_at.isoformat()
        }
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "campaign": campaign_dict
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
