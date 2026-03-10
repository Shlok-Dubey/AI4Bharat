"""
Campaign Planner Agent

This module provides intelligent campaign planning and content scheduling.
Now enhanced with AWS Bedrock AI for optimal distribution!
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random
import json

# Import AWS Bedrock client
try:
    from utils.bedrock_client import get_bedrock_client
    from config import settings
    BEDROCK_AVAILABLE = True
except Exception as e:
    print(f"Bedrock not available for planner: {e}")
    BEDROCK_AVAILABLE = False

class CampaignPlannerAgent:
    """
    AI agent for planning campaign content distribution.
    
    This agent:
    - Distributes content across campaign days
    - Recommends optimal posting times
    - Balances content types and platforms
    - Considers engagement patterns
    
    For production:
    - Use historical engagement data
    - Integrate with platform analytics
    - Implement ML-based optimization
    - Consider timezone targeting
    """
    
    def __init__(self):
        """Initialize the campaign planner agent."""
        self.optimal_times = {
            "instagram": {
                "weekday": ["09:00", "12:00", "17:00", "20:00"],
                "weekend": ["10:00", "14:00", "19:00"]
            },
            "facebook": {
                "weekday": ["08:00", "13:00", "18:00"],
                "weekend": ["09:00", "13:00", "18:00"]
            },
            "twitter": {
                "weekday": ["08:00", "12:00", "15:00", "18:00"],
                "weekend": ["10:00", "14:00", "17:00"]
            },
            "linkedin": {
                "weekday": ["08:00", "12:00", "17:00"],
                "weekend": []  # LinkedIn less active on weekends
            }
        }
    
    def plan_campaign(
        self,
        content: List[Dict],
        campaign_days: int,
        start_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Plan campaign content distribution across days with AI optimization.
        
        This function distributes approved content across the campaign duration,
        using AWS Bedrock AI to optimize distribution strategy.
        
        Args:
            content: List of approved content pieces
            campaign_days: Total number of days in campaign
            start_date: Campaign start date (defaults to today)
            
        Returns:
            List of planned posts with AI-optimized distribution
        """
        if not content:
            return []
        
        if start_date is None:
            start_date = datetime.utcnow()
        
        # Try AI-powered planning first
        if BEDROCK_AVAILABLE:
            try:
                print(f"🤖 Using AI to optimize campaign distribution...")
                sorted_content = self._ai_prioritize_content(content, campaign_days)
            except Exception as e:
                print(f"⚠️  AI planning failed, using algorithm: {e}")
                sorted_content = self._prioritize_content(content)
        else:
            sorted_content = self._prioritize_content(content)
        
        # Distribute content across days
        planned_posts = []
        content_index = 0
        total_content = len(content)
        
        for day in range(1, campaign_days + 1):
            # Calculate how many posts for this day
            remaining_content = total_content - content_index
            remaining_days = campaign_days - day + 1
            posts_today = min(
                remaining_content,
                max(1, remaining_content // remaining_days)
            )
            
            # Get content for this day
            day_content = sorted_content[content_index:content_index + posts_today]
            
            # Plan each post for this day
            for i, item in enumerate(day_content):
                planned_post = self._create_planned_post(
                    content_item=item,
                    day_number=day,
                    start_date=start_date,
                    time_slot=i
                )
                planned_posts.append(planned_post)
            
            content_index += posts_today
        
        return planned_posts
    
    def _ai_prioritize_content(self, content: List[Dict], campaign_days: int) -> List[Dict]:
        """
        Use AWS Bedrock AI to prioritize and order content for optimal engagement.
        
        Args:
            content: List of content pieces
            campaign_days: Number of campaign days
            
        Returns:
            AI-optimized content order
        """
        bedrock_client = get_bedrock_client()
        
        # Prepare content summary for AI
        content_summary = []
        for i, item in enumerate(content):
            content_summary.append({
                "index": i,
                "platform": item.get('platform', 'instagram'),
                "content_type": item.get('content_type', 'post'),
                "caption_preview": item.get('caption', '')[:100],
                "has_hashtags": bool(item.get('hashtags'))
            })
        
        prompt = f"""You are a social media campaign strategist. Analyze this content and provide an optimal posting order for a {campaign_days}-day campaign.

Content pieces:
{json.dumps(content_summary, indent=2)}

Consider:
1. Start with high-engagement content (reels/videos)
2. Distribute content types evenly
3. Build momentum throughout campaign
4. Save strong content for key days (start, middle, end)
5. Alternate platforms if multiple

Return ONLY a JSON array of indices in optimal order, like: [2, 0, 4, 1, 3]
No explanation, just the array."""

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            response = bedrock_client.invoke_model(
                modelId=settings.BEDROCK_MODEL_ID,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            ai_response = response_body['content'][0]['text'].strip()
            
            # Clean response
            if ai_response.startswith('```'):
                ai_response = ai_response.split('```')[1]
                if ai_response.startswith('json'):
                    ai_response = ai_response[4:]
            ai_response = ai_response.strip()
            
            # Parse order
            order = json.loads(ai_response)
            
            # Reorder content based on AI recommendation
            ordered_content = [content[i] for i in order if i < len(content)]
            
            # Add any missing content
            used_indices = set(order)
            for i, item in enumerate(content):
                if i not in used_indices:
                    ordered_content.append(item)
            
            print(f"✅ AI optimized content order: {order}")
            return ordered_content
            
        except Exception as e:
            print(f"⚠️  AI prioritization failed: {e}")
            return self._prioritize_content(content)
    
    def _prioritize_content(self, content: List[Dict]) -> List[Dict]:
        """
        Prioritize content for optimal campaign flow.
        
        Strategy:
        1. Start with high-engagement content (reels, videos)
        2. Mix platforms throughout campaign
        3. Alternate content types
        4. Save some high-value content for mid and end
        
        Args:
            content: List of content pieces
            
        Returns:
            Sorted list of content
        """
        # Assign priority scores
        priority_scores = []
        
        for item in content:
            score = 0
            
            # Content type priority
            content_type = item.get('content_type', 'post')
            if content_type == 'reel':
                score += 10  # Reels have highest engagement
            elif content_type == 'story':
                score += 5
            elif content_type == 'post':
                score += 3
            
            # Platform priority (Instagram generally higher engagement)
            platform = item.get('platform', 'instagram')
            if platform == 'instagram':
                score += 5
            elif platform == 'facebook':
                score += 3
            elif platform == 'twitter':
                score += 2
            elif platform == 'linkedin':
                score += 1
            
            # Add some randomness for variety
            score += random.uniform(0, 2)
            
            priority_scores.append((score, item))
        
        # Sort by priority (highest first)
        priority_scores.sort(key=lambda x: x[0], reverse=True)
        
        # Extract sorted content
        sorted_content = [item for score, item in priority_scores]
        
        # Ensure variety by shuffling similar priority items
        return self._ensure_variety(sorted_content)
    
    def _ensure_variety(self, content: List[Dict]) -> List[Dict]:
        """
        Ensure variety in content distribution.
        
        Avoid consecutive posts of same platform or type.
        
        Args:
            content: Sorted content list
            
        Returns:
            Content list with ensured variety
        """
        if len(content) <= 2:
            return content
        
        result = [content[0]]
        remaining = content[1:]
        
        while remaining:
            last_item = result[-1]
            last_platform = last_item.get('platform')
            last_type = last_item.get('content_type')
            
            # Find next item with different platform or type
            next_item = None
            for i, item in enumerate(remaining):
                if (item.get('platform') != last_platform or 
                    item.get('content_type') != last_type):
                    next_item = remaining.pop(i)
                    break
            
            # If no different item found, just take the next one
            if next_item is None:
                next_item = remaining.pop(0)
            
            result.append(next_item)
        
        return result
    
    def _create_planned_post(
        self,
        content_item: Dict,
        day_number: int,
        start_date: datetime,
        time_slot: int
    ) -> Dict:
        """
        Create a planned post with scheduling details.
        
        Args:
            content_item: Content piece to schedule
            day_number: Day number in campaign (1-indexed)
            start_date: Campaign start date
            time_slot: Time slot for this day (0, 1, 2, ...)
            
        Returns:
            Planned post dictionary
        """
        # Calculate posting date
        posting_date = start_date + timedelta(days=day_number - 1)
        
        # Get optimal time for platform
        platform = content_item.get('platform', 'instagram')
        is_weekend = posting_date.weekday() >= 5
        
        day_type = "weekend" if is_weekend else "weekday"
        optimal_times = self.optimal_times.get(platform, {}).get(day_type, ["12:00"])
        
        # Select time based on slot
        if optimal_times:
            time_index = time_slot % len(optimal_times)
            recommended_time = optimal_times[time_index]
        else:
            recommended_time = "12:00"
        
        # Extract metadata
        metadata = content_item.get('ai_metadata', {})
        
        # Create planned post
        planned_post = {
            "content_id": content_item.get('id'),
            "caption": content_item.get('caption', ''),
            "hashtags": content_item.get('hashtags', ''),
            "script": metadata.get('reel_script'),
            "thumbnail_text": metadata.get('thumbnail_text'),
            "platform": platform,
            "content_type": content_item.get('content_type', 'post'),
            "recommended_day": day_number,
            "recommended_date": posting_date.strftime('%Y-%m-%d'),
            "recommended_time": recommended_time,
            "recommended_datetime": f"{posting_date.strftime('%Y-%m-%d')} {recommended_time}",
            "day_of_week": posting_date.strftime('%A'),
            "is_weekend": is_weekend
        }
        
        return planned_post
    
    def generate_campaign_schedule(
        self,
        campaign_days: int,
        posts_per_day: int = 1,
        platforms: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate recommended posting schedule for a campaign.
        
        This provides a template schedule showing optimal posting times
        before content is generated.
        
        Args:
            campaign_days: Number of days in campaign
            posts_per_day: Target posts per day
            platforms: List of platforms to include
            
        Returns:
            Dictionary with schedule recommendations
            
        Example:
            {
                "total_posts": 15,
                "posts_per_day": 1,
                "schedule": [
                    {
                        "day": 1,
                        "date": "2024-01-01",
                        "recommended_times": ["09:00", "17:00"],
                        "platforms": ["instagram", "facebook"]
                    }
                ]
            }
        """
        if platforms is None:
            platforms = ["instagram", "facebook", "twitter"]
        
        start_date = datetime.utcnow()
        schedule = []
        
        for day in range(1, campaign_days + 1):
            posting_date = start_date + timedelta(days=day - 1)
            is_weekend = posting_date.weekday() >= 5
            day_type = "weekend" if is_weekend else "weekday"
            
            # Get optimal times for each platform
            times_by_platform = {}
            for platform in platforms:
                times = self.optimal_times.get(platform, {}).get(day_type, ["12:00"])
                times_by_platform[platform] = times[:posts_per_day]
            
            schedule.append({
                "day": day,
                "date": posting_date.strftime('%Y-%m-%d'),
                "day_of_week": posting_date.strftime('%A'),
                "is_weekend": is_weekend,
                "recommended_times_by_platform": times_by_platform,
                "posts_planned": posts_per_day * len(platforms)
            })
        
        return {
            "total_days": campaign_days,
            "total_posts": campaign_days * posts_per_day * len(platforms),
            "posts_per_day": posts_per_day,
            "platforms": platforms,
            "schedule": schedule
        }
    
    def optimize_posting_times(
        self,
        planned_posts: List[Dict],
        engagement_data: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Optimize posting times based on engagement data.
        
        For production: Use historical engagement data to optimize times.
        
        Args:
            planned_posts: List of planned posts
            engagement_data: Historical engagement data by time/platform
            
        Returns:
            Optimized planned posts
            
        Note:
            Currently uses default optimal times.
            For production: Implement ML-based optimization using:
            - Historical engagement rates
            - Audience timezone data
            - Platform analytics
            - Competitor posting patterns
        """
        # Placeholder for ML-based optimization
        # In production, analyze engagement_data and adjust times
        
        if engagement_data:
            # TODO: Implement ML-based time optimization
            # Example:
            # - Analyze best performing times
            # - Consider audience active hours
            # - Adjust based on platform algorithms
            pass
        
        return planned_posts


# Singleton instance
_campaign_planner = None

def get_campaign_planner() -> CampaignPlannerAgent:
    """
    Get or create the campaign planner agent instance.
    
    Returns:
        CampaignPlannerAgent instance
    """
    global _campaign_planner
    if _campaign_planner is None:
        _campaign_planner = CampaignPlannerAgent()
    return _campaign_planner
