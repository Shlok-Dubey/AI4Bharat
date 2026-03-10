"""
Post Scheduler Agent

This module provides intelligent post scheduling with AI optimization
using AWS Bedrock for timing predictions.
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
    print(f"Bedrock not available for scheduler: {e}")
    BEDROCK_AVAILABLE = False

class PostSchedulerAgent:
    """
    AI agent for scheduling social media posts at optimal times.
    
    This agent:
    - Determines best posting times per platform
    - Considers day of week patterns
    - Avoids scheduling conflicts
    - Balances post frequency
    
    For production:
    - Use platform analytics APIs
    - Implement ML-based time prediction
    - Consider audience timezone
    - Analyze competitor posting patterns
    - Use A/B testing for optimization
    """
    
    def __init__(self):
        """Initialize the post scheduler agent."""
        # Platform-specific peak engagement times
        # Based on industry research and best practices
        self.peak_times = {
            "instagram": {
                "weekday": ["11:00", "14:00", "19:00"],
                "weekend": ["10:00", "13:00", "18:00"]
            },
            "facebook": {
                "weekday": ["09:00", "13:00", "15:00"],
                "weekend": ["12:00", "15:00", "18:00"]
            },
            "twitter": {
                "weekday": ["08:00", "12:00", "17:00"],
                "weekend": ["09:00", "12:00", "17:00"]
            },
            "linkedin": {
                "weekday": ["08:00", "12:00", "17:00"],
                "weekend": []  # LinkedIn less active on weekends
            },
            "youtube": {
                "weekday": ["16:00", "20:00"],
                "weekend": ["14:00", "19:00"]
            },
            "tiktok": {
                "weekday": ["06:00", "10:00", "19:00"],
                "weekend": ["09:00", "12:00", "19:00"]
            }
        }
        
        # Minimum time gap between posts on same platform (in hours)
        self.min_gap_hours = 4
        
        # Maximum posts per day per platform
        self.max_posts_per_day = 3
        
        # Cache for historical data (avoid fetching multiple times)
        self._historical_data_cache = {}
        self._cache_timestamp = None
    
    def schedule_posts(
        self,
        posts: List[Dict],
        start_date: Optional[datetime] = None,
        timezone_offset: int = 0
    ) -> List[Dict]:
        """
        Schedule posts at optimal times.
        
        This function assigns specific posting times to each post based on
        platform-specific peak engagement times and scheduling constraints.
        
        Args:
            posts: List of posts to schedule (from campaign planner)
            start_date: Campaign start date (defaults to now)
            timezone_offset: Timezone offset in hours (e.g., -5 for EST)
            
        Returns:
            List of scheduled posts with:
            - post_time: Scheduled posting time (HH:MM format)
            - post_datetime: Full datetime for posting
            - platform: Target platform
            - day_of_week: Day name
            - is_peak_time: Whether scheduled at peak time
            - All original post fields
            
        Strategy:
            1. Group posts by day and platform
            2. Assign peak times first
            3. Distribute remaining posts evenly
            4. Ensure minimum gap between posts
            5. Avoid scheduling conflicts
            
        For production:
            - Use ML models for time prediction
            - Analyze historical engagement data
            - Consider audience active hours
            - Implement dynamic rescheduling
            - Use platform-specific algorithms
        """
        if not posts:
            return []
        
        if start_date is None:
            start_date = datetime.utcnow()
        
        scheduled_posts = []
        scheduled_times = {}  # Track scheduled times per platform per day
        
        for post in posts:
            scheduled_post = self._schedule_single_post(
                post=post,
                start_date=start_date,
                scheduled_times=scheduled_times,
                timezone_offset=timezone_offset
            )
            scheduled_posts.append(scheduled_post)
        
        return scheduled_posts
    
    def _schedule_single_post(
        self,
        post: Dict,
        start_date: datetime,
        scheduled_times: Dict,
        timezone_offset: int
    ) -> Dict:
        """
        Schedule a single post at optimal time.
        
        Args:
            post: Post to schedule
            start_date: Campaign start date
            scheduled_times: Already scheduled times (to avoid conflicts)
            timezone_offset: Timezone offset
            
        Returns:
            Scheduled post with time details
        """
        platform = post.get('platform', 'instagram')
        day_number = post.get('recommended_day', 1)
        
        # Calculate posting date
        posting_date = start_date + timedelta(days=day_number - 1)
        is_weekend = posting_date.weekday() >= 5
        
        # Get available times - expand to include more options for AI
        day_type = "weekend" if is_weekend else "weekday"
        
        # Try to get historical best times first
        historical_data = self._get_historical_performance(platform)
        
        if historical_data and historical_data.get('best_times'):
            # Use historical best times as available options
            available_times = historical_data['best_times'][:10]  # Top 10 times
            print(f"📊 Using {len(available_times)} times from historical data")
        else:
            # Fall back to predefined peak times
            available_times = self.peak_times.get(platform, {}).get(day_type, ["12:00"])
        
        # If no times available (e.g., LinkedIn on weekend), use default
        if not available_times:
            available_times = ["12:00"]
        
        # Get already scheduled times for this platform on this day
        day_key = f"{platform}_{day_number}"
        if day_key not in scheduled_times:
            scheduled_times[day_key] = []
        
        # Find best available time (with AI if available)
        selected_time = self._find_best_time(
            available_times=available_times,
            already_scheduled=scheduled_times[day_key],
            platform=platform,
            content_type=post.get('content_type', 'post'),
            caption=post.get('caption', '')
        )
        
        # Mark this time as scheduled
        scheduled_times[day_key].append(selected_time)
        
        # Create full datetime
        post_datetime = datetime.strptime(
            f"{posting_date.strftime('%Y-%m-%d')} {selected_time}",
            "%Y-%m-%d %H:%M"
        )
        
        # Apply timezone offset
        post_datetime = post_datetime + timedelta(hours=timezone_offset)
        
        # Check if this is a peak time
        is_peak_time = selected_time in available_times
        
        # Create scheduled post
        scheduled_post = {
            **post,  # Include all original fields
            "post_time": selected_time,
            "post_datetime": post_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "post_date": posting_date.strftime("%Y-%m-%d"),
            "day_of_week": posting_date.strftime("%A"),
            "is_weekend": is_weekend,
            "is_peak_time": is_peak_time,
            "timezone_offset": timezone_offset,
            "scheduled_at": datetime.utcnow().isoformat()
        }
        
        return scheduled_post
    
    def _find_best_time(
        self,
        available_times: List[str],
        already_scheduled: List[str],
        platform: str,
        content_type: str = "post",
        caption: str = ""
    ) -> str:
        """
        Find the best available time slot with AI optimization.
        
        Args:
            available_times: List of peak times
            already_scheduled: Times already used today
            platform: Platform name
            content_type: Type of content
            caption: Content caption for AI analysis
            
        Returns:
            Selected time string (HH:MM)
        """
        # Try AI-powered time selection
        if BEDROCK_AVAILABLE and caption:
            try:
                ai_time = self._ai_select_time(
                    available_times, 
                    already_scheduled, 
                    platform, 
                    content_type, 
                    caption
                )
                if ai_time:
                    return ai_time
            except Exception as e:
                print(f"⚠️  AI time selection failed: {e}")
        
        # Fallback to algorithm
        valid_times = []
        for time in available_times:
            if self._is_time_available(time, already_scheduled):
                valid_times.append(time)
        
        if not valid_times:
            valid_times = self._generate_alternative_times(
                available_times,
                already_scheduled
            )
        
        if valid_times:
            return valid_times[0]
        else:
            return available_times[0] if available_times else "12:00"
    
    def _ai_select_time(
        self,
        available_times: List[str],
        already_scheduled: List[str],
        platform: str,
        content_type: str,
        caption: str
    ) -> Optional[str]:
        """
        Use AWS Bedrock AI with live Instagram analytics to select optimal posting time.
        
        Args:
            available_times: Available time slots
            already_scheduled: Already used times
            platform: Social media platform
            content_type: Type of content
            caption: Content caption
            
        Returns:
            Optimal time or None if AI fails
        """
        bedrock_client = get_bedrock_client()
        
        # Try to get historical performance data from Instagram
        historical_data = self._get_historical_performance(platform)
        
        # Build context with historical data
        if historical_data:
            performance_context = f"""
Historical Performance Data (Last 30 days):
- Best performing times: {', '.join(historical_data['best_times'])}
- Average engagement by time:
{self._format_engagement_by_time(historical_data['engagement_by_time'])}
- Peak engagement days: {', '.join(historical_data['peak_days'])}
- Content type performance: {historical_data['content_type_performance']}
"""
        else:
            performance_context = "No historical data available. Using platform best practices."
        
        prompt = f"""You are a social media timing expert with access to real performance data. Select the best posting time for this content.

Platform: {platform}
Content Type: {content_type}
Caption Preview: {caption[:150]}

Available Times: {', '.join(available_times)}
Already Scheduled: {', '.join(already_scheduled) if already_scheduled else 'None'}

{performance_context}

Consider:
1. Historical performance data from this account
2. Content type (reels perform better in evening, posts in morning/lunch)
3. Platform algorithms (Instagram favors consistent timing)
4. Audience behavior patterns from actual data
5. Avoid times too close to already scheduled posts

Return ONLY the best time in HH:MM format from the available times. No explanation."""

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 50,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            response = bedrock_client.invoke_model(
                modelId=settings.BEDROCK_MODEL_ID,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            selected_time = response_body['content'][0]['text'].strip()
            
            # Validate time format and availability
            if ':' in selected_time and selected_time in available_times:
                if self._is_time_available(selected_time, already_scheduled):
                    print(f"✅ AI selected optimal time: {selected_time} (based on live analytics)")
                    return selected_time
            
            return None
            
        except Exception as e:
            print(f"⚠️  AI time selection error: {e}")
            return None
    
    def _get_historical_performance(self, platform: str) -> Optional[Dict]:
        """
        Fetch historical performance data from Instagram to inform scheduling decisions.
        Uses caching to avoid multiple database queries.
        
        Args:
            platform: Social media platform
            
        Returns:
            Dictionary with historical performance metrics or None
        """
        if platform.lower() != "instagram":
            return None
        
        # Check cache (valid for 5 minutes)
        from datetime import datetime, timedelta
        if self._cache_timestamp and self._historical_data_cache.get(platform):
            cache_age = datetime.utcnow() - self._cache_timestamp
            if cache_age < timedelta(minutes=5):
                print(f"📊 Using cached historical data")
                return self._historical_data_cache[platform]
        
        try:
            # Import analytics agent to fetch historical data
            from agents.analytics_agent import AnalyticsAgent
            import dynamodb_client as db
            
            # Get database session
            # Fetch published posts from last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            # Get all scheduled posts
            all_posts = db.scheduled_posts_table.scan(
                FilterExpression='#status = :status AND published_at >= :thirty_days_ago AND platform_post_id <> :null',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'published',
                    ':thirty_days_ago': thirty_days_ago.isoformat(),
                    ':null': ''
                }
            ).get('Items', [])
            
            published_posts = [db.dynamodb_to_python(item) for item in all_posts]
            
            if not published_posts:
                print("📊 No historical data available - using platform best practices")
                return None
            
            print(f"📊 Analyzing {len(published_posts)} historical posts for optimal timing...")
            
            # Analyze engagement by time of day
            engagement_by_time = {}
            engagement_by_day = {}
            content_type_performance = {}
            
            for post in published_posts:
                # Get analytics for this post
                analytics = db.get_post_analytics(post['post_id'])
                
                if analytics:
                    # Get content to determine type
                    content = db.get_generated_content(post['content_id'])
                    if not content:
                        continue
                    
                    # Extract hour from published time
                    published_at = db.deserialize_datetime(post['published_at'])
                    hour = published_at.hour
                    time_slot = f"{hour:02d}:00"
                    
                    # Calculate engagement score
                    engagement_score = (
                        analytics.get('likes', 0) * 1.0 +
                        analytics.get('comments', 0) * 2.0 +
                        analytics.get('shares', 0) * 3.0
                    ) / max(analytics.get('impressions', 1), 1) * 100
                    
                    # Aggregate by time
                    if time_slot not in engagement_by_time:
                        engagement_by_time[time_slot] = []
                    engagement_by_time[time_slot].append(engagement_score)
                    
                    # Aggregate by day of week
                    day_name = published_at.strftime("%A")
                    if day_name not in engagement_by_day:
                        engagement_by_day[day_name] = []
                    engagement_by_day[day_name].append(engagement_score)
                    
                    # Aggregate by content type
                    content_type = content.get('content_type', 'post')
                    if content_type not in content_type_performance:
                        content_type_performance[content_type] = []
                    content_type_performance[content_type].append(engagement_score)
            
            # Calculate averages
            avg_engagement_by_time = {
                time: sum(scores) / len(scores)
                for time, scores in engagement_by_time.items()
            }
            
            avg_engagement_by_day = {
                day: sum(scores) / len(scores)
                for day, scores in engagement_by_day.items()
            }
            
            # Find best performing times (top 10 for more variety)
            sorted_times = sorted(
                avg_engagement_by_time.items(),
                key=lambda x: x[1],
                reverse=True
            )
            best_times = [time for time, _ in sorted_times[:10]]
            
            # Find peak days
            sorted_days = sorted(
                avg_engagement_by_day.items(),
                key=lambda x: x[1],
                reverse=True
            )
            peak_days = [day for day, _ in sorted_days[:3]]
            
            # Format content type performance
            content_perf_str = ", ".join([
                f"{ctype}: {sum(scores)/len(scores):.1f}%"
                for ctype, scores in content_type_performance.items()
            ])
            
            result = {
                "best_times": best_times,
                "engagement_by_time": avg_engagement_by_time,
                "peak_days": peak_days,
                "content_type_performance": content_perf_str,
                "total_posts_analyzed": len(published_posts)
            }
            
            # Cache the result
            self._historical_data_cache[platform] = result
            self._cache_timestamp = datetime.utcnow()
            
            print(f"✅ Historical analysis complete:")
            print(f"   Best times: {', '.join(best_times[:5])}")
            print(f"   Peak days: {', '.join(peak_days)}")
            
            return result
            
        except Exception as e:
            print(f"⚠️  Failed to fetch historical data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _format_engagement_by_time(self, engagement_by_time: Dict[str, float]) -> str:
        """Format engagement data for AI prompt"""
        sorted_times = sorted(engagement_by_time.items(), key=lambda x: x[1], reverse=True)
        lines = []
        for time, engagement in sorted_times[:10]:  # Top 10 times
            lines.append(f"  {time}: {engagement:.1f}% engagement")
        return "\n".join(lines)
    
    def _is_time_available(
        self,
        time: str,
        already_scheduled: List[str]
    ) -> bool:
        """
        Check if a time slot is available (not too close to scheduled posts).
        
        Args:
            time: Time to check (HH:MM)
            already_scheduled: Already scheduled times
            
        Returns:
            True if time is available
        """
        if not already_scheduled:
            return True
        
        # Convert to minutes for comparison
        time_minutes = self._time_to_minutes(time)
        
        for scheduled_time in already_scheduled:
            scheduled_minutes = self._time_to_minutes(scheduled_time)
            gap_minutes = abs(time_minutes - scheduled_minutes)
            
            # Check minimum gap (4 hours = 240 minutes)
            if gap_minutes < (self.min_gap_hours * 60):
                return False
        
        return True
    
    def _time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM to minutes since midnight."""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    def _generate_alternative_times(
        self,
        peak_times: List[str],
        already_scheduled: List[str]
    ) -> List[str]:
        """
        Generate alternative times when peak times are unavailable.
        
        Args:
            peak_times: Original peak times
            already_scheduled: Already scheduled times
            
        Returns:
            List of alternative times
        """
        alternatives = []
        
        # Try times 1-2 hours before/after peak times
        for peak_time in peak_times:
            peak_minutes = self._time_to_minutes(peak_time)
            
            # Try 1 hour before
            alt_minutes = peak_minutes - 60
            if alt_minutes >= 0:
                alt_time = f"{alt_minutes // 60:02d}:{alt_minutes % 60:02d}"
                if self._is_time_available(alt_time, already_scheduled):
                    alternatives.append(alt_time)
            
            # Try 1 hour after
            alt_minutes = peak_minutes + 60
            if alt_minutes < 24 * 60:
                alt_time = f"{alt_minutes // 60:02d}:{alt_minutes % 60:02d}"
                if self._is_time_available(alt_time, already_scheduled):
                    alternatives.append(alt_time)
        
        return alternatives
    
    def get_optimal_times(
        self,
        platform: str,
        day_of_week: Optional[str] = None
    ) -> List[str]:
        """
        Get optimal posting times for a platform.
        
        Args:
            platform: Platform name
            day_of_week: Specific day (Monday, Tuesday, etc.)
            
        Returns:
            List of optimal times (HH:MM format)
            
        Example:
            >>> agent.get_optimal_times("instagram", "Monday")
            ["11:00", "14:00", "19:00"]
        """
        if day_of_week:
            is_weekend = day_of_week in ["Saturday", "Sunday"]
            day_type = "weekend" if is_weekend else "weekday"
        else:
            # Default to weekday
            day_type = "weekday"
        
        return self.peak_times.get(platform, {}).get(day_type, ["12:00"])
    
    def analyze_schedule(self, scheduled_posts: List[Dict]) -> Dict:
        """
        Analyze the scheduled posts for insights.
        
        Args:
            scheduled_posts: List of scheduled posts
            
        Returns:
            Dictionary with schedule analysis:
            - total_posts: Total number of posts
            - posts_by_platform: Count per platform
            - posts_by_day: Count per day
            - peak_time_percentage: % of posts at peak times
            - average_posts_per_day: Average posts per day
            
        Use for:
            - Schedule optimization
            - Reporting and analytics
            - Identifying scheduling gaps
        """
        if not scheduled_posts:
            return {
                "total_posts": 0,
                "posts_by_platform": {},
                "posts_by_day": {},
                "peak_time_percentage": 0,
                "average_posts_per_day": 0
            }
        
        # Count posts by platform
        posts_by_platform = {}
        for post in scheduled_posts:
            platform = post.get('platform', 'unknown')
            posts_by_platform[platform] = posts_by_platform.get(platform, 0) + 1
        
        # Count posts by day
        posts_by_day = {}
        for post in scheduled_posts:
            day = post.get('recommended_day', 0)
            posts_by_day[day] = posts_by_day.get(day, 0) + 1
        
        # Calculate peak time percentage
        peak_time_posts = sum(1 for post in scheduled_posts if post.get('is_peak_time', False))
        peak_time_percentage = (peak_time_posts / len(scheduled_posts)) * 100
        
        # Calculate average posts per day
        unique_days = len(set(post.get('recommended_day', 0) for post in scheduled_posts))
        average_posts_per_day = len(scheduled_posts) / unique_days if unique_days > 0 else 0
        
        return {
            "total_posts": len(scheduled_posts),
            "posts_by_platform": posts_by_platform,
            "posts_by_day": posts_by_day,
            "peak_time_percentage": round(peak_time_percentage, 2),
            "average_posts_per_day": round(average_posts_per_day, 2),
            "unique_days": unique_days
        }


# Singleton instance
_scheduler_agent = None

def get_scheduler_agent() -> PostSchedulerAgent:
    """
    Get or create the post scheduler agent instance.
    
    Returns:
        PostSchedulerAgent instance
    """
    global _scheduler_agent
    if _scheduler_agent is None:
        _scheduler_agent = PostSchedulerAgent()
    return _scheduler_agent
