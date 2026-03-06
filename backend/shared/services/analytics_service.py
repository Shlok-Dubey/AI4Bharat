"""
Analytics service for aggregating and analyzing campaign performance.

Handles analytics aggregation, trend calculation, and performance insights.

Requirements: 8.2, 8.3
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from statistics import mean

from shared.models.domain import Analytics
from shared.schemas.analytics import AnalyticsSummary
from repositories.analytics_repository import AnalyticsRepository
from repositories.campaign_repository import CampaignRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics operations."""
    
    def __init__(
        self,
        analytics_repo: Optional[AnalyticsRepository] = None,
        campaign_repo: Optional[CampaignRepository] = None
    ):
        """Initialize AnalyticsService."""
        self.analytics_repo = analytics_repo or AnalyticsRepository()
        self.campaign_repo = campaign_repo or CampaignRepository()
    
    async def store_analytics(
        self,
        campaign_id: str,
        user_id: str,
        likes: int,
        comments: int,
        reach: int,
        impressions: int,
        engagement_rate: float
    ) -> Analytics:
        """
        Store analytics metrics for a campaign.
        
        Associates metrics with campaign_id and timestamp.
        
        Args:
            campaign_id: Campaign ID
            user_id: User ID
            likes: Number of likes
            comments: Number of comments
            reach: Number of unique accounts reached
            impressions: Total impressions
            engagement_rate: Calculated engagement rate
            
        Returns:
            Created Analytics object
            
        Requirements: 8.2
        """
        analytics = Analytics(
            campaign_id=campaign_id,
            user_id=user_id,
            likes=likes,
            comments=comments,
            reach=reach,
            impressions=impressions,
            engagement_rate=engagement_rate,
            fetched_at=datetime.utcnow()
        )
        
        await self.analytics_repo.create(analytics)
        
        logger.info(
            f"Stored analytics for campaign {campaign_id}: "
            f"likes={likes}, comments={comments}, reach={reach}, "
            f"engagement_rate={engagement_rate:.2f}%"
        )
        
        return analytics
    
    async def get_analytics_summary(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> AnalyticsSummary:
        """
        Get analytics summary for user's campaigns in date range.
        
        Calculates:
        - Totals: sum of likes, comments, reach, impressions
        - Averages: mean engagement_rate
        - Trends: compare to previous period
        - Top performing campaigns
        
        Args:
            user_id: User ID
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            AnalyticsSummary object
            
        Requirements: 8.3
        """
        # Get analytics for current period
        analytics_list = await self.analytics_repo.get_by_user_and_date_range(
            user_id, start_date, end_date
        )
        
        if not analytics_list:
            # No data for period
            return AnalyticsSummary(
                total_likes=0,
                total_comments=0,
                total_reach=0,
                total_impressions=0,
                avg_engagement_rate=0.0,
                campaign_count=0,
                top_campaigns=[],
                start_date=start_date,
                end_date=end_date
            )
        
        # Calculate totals
        total_likes = sum(a.likes for a in analytics_list)
        total_comments = sum(a.comments for a in analytics_list)
        total_reach = sum(a.reach for a in analytics_list)
        total_impressions = sum(a.impressions for a in analytics_list)
        
        # Calculate average engagement rate
        engagement_rates = [a.engagement_rate for a in analytics_list if a.engagement_rate > 0]
        avg_engagement_rate = mean(engagement_rates) if engagement_rates else 0.0
        
        # Get unique campaigns
        campaign_ids = list(set(a.campaign_id for a in analytics_list))
        campaign_count = len(campaign_ids)
        
        # Identify top performing campaigns
        # Group by campaign_id and get latest analytics for each
        campaign_analytics = {}
        for analytics in analytics_list:
            if analytics.campaign_id not in campaign_analytics:
                campaign_analytics[analytics.campaign_id] = analytics
            else:
                # Keep the latest one
                if analytics.fetched_at > campaign_analytics[analytics.campaign_id].fetched_at:
                    campaign_analytics[analytics.campaign_id] = analytics
        
        # Sort by engagement rate and get top 5
        sorted_campaigns = sorted(
            campaign_analytics.values(),
            key=lambda a: a.engagement_rate,
            reverse=True
        )[:5]
        
        top_campaigns = [
            {
                'campaign_id': a.campaign_id,
                'engagement_rate': a.engagement_rate,
                'likes': a.likes,
                'comments': a.comments,
                'reach': a.reach
            }
            for a in sorted_campaigns
        ]
        
        # Calculate trends (compare to previous period)
        period_duration = end_date - start_date
        previous_start = start_date - period_duration
        previous_end = start_date
        
        previous_analytics = await self.analytics_repo.get_by_user_and_date_range(
            user_id, previous_start, previous_end
        )
        
        trend_likes = None
        trend_comments = None
        trend_reach = None
        trend_engagement_rate = None
        
        if previous_analytics:
            prev_total_likes = sum(a.likes for a in previous_analytics)
            prev_total_comments = sum(a.comments for a in previous_analytics)
            prev_total_reach = sum(a.reach for a in previous_analytics)
            
            prev_engagement_rates = [
                a.engagement_rate for a in previous_analytics if a.engagement_rate > 0
            ]
            prev_avg_engagement_rate = mean(prev_engagement_rates) if prev_engagement_rates else 0.0
            
            # Calculate percentage changes
            if prev_total_likes > 0:
                trend_likes = ((total_likes - prev_total_likes) / prev_total_likes) * 100
            
            if prev_total_comments > 0:
                trend_comments = ((total_comments - prev_total_comments) / prev_total_comments) * 100
            
            if prev_total_reach > 0:
                trend_reach = ((total_reach - prev_total_reach) / prev_total_reach) * 100
            
            if prev_avg_engagement_rate > 0:
                trend_engagement_rate = (
                    (avg_engagement_rate - prev_avg_engagement_rate) / prev_avg_engagement_rate
                ) * 100
        
        logger.info(
            f"Generated analytics summary for user {user_id}: "
            f"{campaign_count} campaigns, avg_engagement={avg_engagement_rate:.2f}%"
        )
        
        return AnalyticsSummary(
            total_likes=total_likes,
            total_comments=total_comments,
            total_reach=total_reach,
            total_impressions=total_impressions,
            avg_engagement_rate=avg_engagement_rate,
            campaign_count=campaign_count,
            top_campaigns=top_campaigns,
            trend_likes=trend_likes,
            trend_comments=trend_comments,
            trend_reach=trend_reach,
            trend_engagement_rate=trend_engagement_rate,
            start_date=start_date,
            end_date=end_date
        )
