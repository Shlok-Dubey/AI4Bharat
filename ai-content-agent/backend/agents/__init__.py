"""
AI Agent modules for content generation and automation.

This package contains AI-powered agents for various tasks:
- Content generation for social media
- Campaign planning and scheduling
- Post scheduling optimization
- Automated posting to platforms
- Image analysis and description
- Hashtag generation
- Content optimization

For production deployment:
- Replace template-based generation with actual LLM APIs
- Use Amazon Bedrock for AWS deployment
- Implement caching for frequently generated content
- Add rate limiting and error handling
"""

from agents.content_generator import ContentGeneratorAgent, get_content_generator
from agents.campaign_planner import CampaignPlannerAgent, get_campaign_planner
from agents.scheduler_agent import PostSchedulerAgent, get_scheduler_agent
from agents.posting_agent import PostingAgent, get_posting_agent

__all__ = [
    "ContentGeneratorAgent",
    "get_content_generator",
    "CampaignPlannerAgent",
    "get_campaign_planner",
    "PostSchedulerAgent",
    "get_scheduler_agent",
    "PostingAgent",
    "get_posting_agent"
]
