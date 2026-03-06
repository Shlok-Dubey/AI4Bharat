"""
Performance Learning Lambda

Analyzes campaign performance and updates Campaign Intelligence Memory.
Invoked by Analytics Collector Lambda after fetching insights.

Requirements: 8.1, 8.4
"""

import json
import logging
import os
from typing import Dict, Any, List
from datetime import datetime

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import shared modules
import sys
sys.path.insert(0, '/opt/python')  # Lambda layer path

from shared.services.bedrock_client import BedrockClient
from repositories.analytics_repository import AnalyticsRepository
from repositories.campaign_repository import CampaignRepository
from repositories.memory_repository import MemoryRepository
from shared.models.domain import Memory


async def analyze_campaign_performance(
    user_id: str,
    campaign_id: str
) -> Dict[str, Any]:
    """
    Analyze a single campaign's performance and extract insights.
    
    Args:
        user_id: User ID
        campaign_id: Campaign ID
        
    Returns:
        Dictionary with insights and patterns
        
    Requirements: 8.1, 8.4
    """
    analytics_repo = AnalyticsRepository()
    campaign_repo = CampaignRepository()
    bedrock_client = BedrockClient()
    
    # Get campaign metadata
    campaign = await campaign_repo.get_by_id(user_id, campaign_id)
    if not campaign:
        logger.warning(f"Campaign {campaign_id} not found")
        return {}
    
    # Get analytics for campaign
    analytics_list = await analytics_repo.get_by_campaign(campaign_id)
    if not analytics_list:
        logger.warning(f"No analytics found for campaign {campaign_id}")
        return {}
    
    # Get latest analytics
    latest_analytics = max(analytics_list, key=lambda a: a.fetched_at)
    
    # Prepare data for Bedrock analysis
    campaign_data = {
        'caption': campaign.caption,
        'hashtags': campaign.hashtags,
        'likes': latest_analytics.likes,
        'comments': latest_analytics.comments,
        'reach': latest_analytics.reach,
        'impressions': latest_analytics.impressions,
        'engagement_rate': latest_analytics.engagement_rate,
        'published_at': campaign.published_at.isoformat() if campaign.published_at else None
    }
    
    # Create prompt for Bedrock
    prompt = f"""Analyze this Instagram campaign performance and extract insights:

Campaign Data:
{json.dumps(campaign_data, indent=2)}

Please analyze:
1. What made this campaign successful or unsuccessful?
2. What content patterns worked well (caption structure, hashtags, tone)?
3. What timing patterns are evident?
4. What should be replicated in future campaigns?
5. What should be avoided?

Provide insights in JSON format with these keys:
- success_factors: List of what worked well
- patterns_to_avoid: List of what didn't work
- content_insights: Insights about caption and hashtags
- timing_insights: Insights about posting time
- overall_assessment: Brief summary
"""
    
    try:
        # Call Bedrock for AI reasoning
        response = await bedrock_client.invoke_model(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.3
        )
        
        # Parse response (assuming JSON format)
        insights = json.loads(response)
        
        logger.info(f"Generated insights for campaign {campaign_id}")
        return insights
        
    except Exception as e:
        logger.error(f"Error analyzing campaign {campaign_id}: {e}", exc_info=True)
        return {}


async def update_memory_with_insights(
    user_id: str,
    insights: Dict[str, Any],
    campaign_data: Dict[str, Any]
):
    """
    Update Campaign Intelligence Memory with learned insights.
    
    Args:
        user_id: User ID
        insights: Insights from Bedrock analysis
        campaign_data: Campaign metadata and metrics
        
    Requirements: 8.1, 8.4
    """
    memory_repo = MemoryRepository()
    
    # Update performance_insights memory
    performance_memory = await memory_repo.get_memory(user_id, 'performance_insights')
    
    if not performance_memory:
        # Create new memory
        performance_memory = Memory(
            user_id=user_id,
            memory_type='performance_insights',
            data={
                'success_factors': [],
                'patterns_to_avoid': [],
                'best_engagement_rate': 0.0
            },
            confidence=0.1,
            sample_size=1
        )
    
    # Update success factors
    if 'success_factors' in insights:
        existing_factors = performance_memory.data.get('success_factors', [])
        new_factors = insights['success_factors']
        # Merge and deduplicate
        all_factors = existing_factors + new_factors
        performance_memory.data['success_factors'] = list(set(all_factors))[:10]  # Keep top 10
    
    # Update patterns to avoid
    if 'patterns_to_avoid' in insights:
        existing_patterns = performance_memory.data.get('patterns_to_avoid', [])
        new_patterns = insights['patterns_to_avoid']
        all_patterns = existing_patterns + new_patterns
        performance_memory.data['patterns_to_avoid'] = list(set(all_patterns))[:10]
    
    # Update best engagement rate
    current_engagement = campaign_data.get('engagement_rate', 0.0)
    best_engagement = performance_memory.data.get('best_engagement_rate', 0.0)
    if current_engagement > best_engagement:
        performance_memory.data['best_engagement_rate'] = current_engagement
        performance_memory.data['best_campaign_example'] = {
            'caption': campaign_data.get('caption', ''),
            'hashtags': campaign_data.get('hashtags', []),
            'engagement_rate': current_engagement
        }
    
    # Increase confidence and sample size
    performance_memory.sample_size += 1
    performance_memory.confidence = min(0.9, 0.1 + (performance_memory.sample_size * 0.05))
    
    await memory_repo.update_memory(performance_memory)
    
    logger.info(
        f"Updated performance_insights memory for user {user_id}: "
        f"confidence={performance_memory.confidence:.2f}, "
        f"sample_size={performance_memory.sample_size}"
    )
    
    # Update content_patterns memory
    if 'content_insights' in insights:
        content_memory = await memory_repo.get_memory(user_id, 'content_patterns')
        
        if not content_memory:
            content_memory = Memory(
                user_id=user_id,
                memory_type='content_patterns',
                data={
                    'effective_hashtags': [],
                    'caption_patterns': []
                },
                confidence=0.1,
                sample_size=1
            )
        
        # Update with new insights
        content_memory.data['latest_insights'] = insights['content_insights']
        content_memory.sample_size += 1
        content_memory.confidence = min(0.9, 0.1 + (content_memory.sample_size * 0.05))
        
        await memory_repo.update_memory(content_memory)
        
        logger.info(f"Updated content_patterns memory for user {user_id}")
    
    # Update engagement_patterns memory
    if 'timing_insights' in insights and campaign_data.get('published_at'):
        engagement_memory = await memory_repo.get_memory(user_id, 'engagement_patterns')
        
        if not engagement_memory:
            engagement_memory = Memory(
                user_id=user_id,
                memory_type='engagement_patterns',
                data={
                    'best_posting_times': []
                },
                confidence=0.1,
                sample_size=1
            )
        
        # Extract day and hour from published_at
        published_at = datetime.fromisoformat(campaign_data['published_at'].replace('Z', '+00:00'))
        day_of_week = published_at.strftime('%A')
        hour = published_at.hour
        
        # Store timing data
        timing_data = {
            'day_of_week': day_of_week,
            'hour': hour,
            'engagement_rate': campaign_data.get('engagement_rate', 0.0),
            'insights': insights['timing_insights']
        }
        
        best_times = engagement_memory.data.get('best_posting_times', [])
        best_times.append(timing_data)
        # Keep only top 10 by engagement rate
        best_times.sort(key=lambda x: x['engagement_rate'], reverse=True)
        engagement_memory.data['best_posting_times'] = best_times[:10]
        
        engagement_memory.sample_size += 1
        engagement_memory.confidence = min(0.9, 0.1 + (engagement_memory.sample_size * 0.05))
        
        await memory_repo.update_memory(engagement_memory)
        
        logger.info(f"Updated engagement_patterns memory for user {user_id}")


async def process_learning(campaign_id: str, user_id: str):
    """
    Process performance learning for a campaign.
    
    Args:
        campaign_id: Campaign ID
        user_id: User ID
        
    Requirements: 8.1, 8.4
    """
    logger.info(f"Processing performance learning for campaign {campaign_id}")
    
    # Analyze campaign performance
    insights = await analyze_campaign_performance(user_id, campaign_id)
    
    if not insights:
        logger.warning(f"No insights generated for campaign {campaign_id}")
        return
    
    # Get campaign data for memory update
    campaign_repo = CampaignRepository()
    analytics_repo = AnalyticsRepository()
    
    campaign = await campaign_repo.get_by_id(user_id, campaign_id)
    analytics_list = await analytics_repo.get_by_campaign(campaign_id)
    latest_analytics = max(analytics_list, key=lambda a: a.fetched_at) if analytics_list else None
    
    if campaign and latest_analytics:
        campaign_data = {
            'caption': campaign.caption,
            'hashtags': campaign.hashtags,
            'engagement_rate': latest_analytics.engagement_rate,
            'published_at': campaign.published_at.isoformat() if campaign.published_at else None
        }
        
        # Update memory with insights
        await update_memory_with_insights(user_id, insights, campaign_data)
        
        logger.info(f"Completed performance learning for campaign {campaign_id}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for performance learning.
    
    Invoked by Analytics Collector Lambda after fetching insights.
    
    Event format:
    {
        "campaign_id": "...",
        "user_id": "..."
    }
    
    Requirements: 8.1, 8.4
    """
    logger.info("Performance Learning Lambda triggered")
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        campaign_id = event.get('campaign_id')
        user_id = event.get('user_id')
        
        if not campaign_id or not user_id:
            raise ValueError("campaign_id and user_id are required")
        
        # Run async processing
        import asyncio
        asyncio.run(process_learning(campaign_id, user_id))
        
        logger.info(f"Performance learning completed for campaign {campaign_id}")
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Performance learning completed",
                "campaign_id": campaign_id
            })
        }
        
    except Exception as e:
        logger.error(f"Performance learning failed: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "message": "Performance learning failed"
            })
        }
