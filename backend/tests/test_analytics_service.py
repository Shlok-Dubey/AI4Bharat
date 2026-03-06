"""
Tests for analytics service.

Tests analytics aggregation, storage, and summary generation.

Requirements: 8.2, 8.3
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from shared.services.analytics_service import AnalyticsService
from shared.models.domain import Analytics
from repositories.analytics_repository import AnalyticsRepository
from repositories.campaign_repository import CampaignRepository


@pytest.fixture
def analytics_service():
    """Create AnalyticsService with mocked repositories."""
    analytics_repo = AsyncMock(spec=AnalyticsRepository)
    campaign_repo = AsyncMock(spec=CampaignRepository)
    return AnalyticsService(analytics_repo=analytics_repo, campaign_repo=campaign_repo)


@pytest.mark.asyncio
async def test_store_analytics(analytics_service):
    """Test storing analytics for a campaign."""
    # Arrange
    campaign_id = "campaign-123"
    user_id = "user-456"
    
    analytics_service.analytics_repo.create = AsyncMock(
        side_effect=lambda a: a
    )
    
    # Act
    result = await analytics_service.store_analytics(
        campaign_id=campaign_id,
        user_id=user_id,
        likes=100,
        comments=20,
        reach=500,
        impressions=800,
        engagement_rate=24.0
    )
    
    # Assert
    assert result.campaign_id == campaign_id
    assert result.user_id == user_id
    assert result.likes == 100
    assert result.comments == 20
    assert result.reach == 500
    assert result.impressions == 800
    assert result.engagement_rate == 24.0
    analytics_service.analytics_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_analytics_summary_no_data(analytics_service):
    """Test analytics summary with no data."""
    # Arrange
    user_id = "user-123"
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    
    analytics_service.analytics_repo.get_by_user_and_date_range = AsyncMock(
        return_value=[]
    )
    
    # Act
    summary = await analytics_service.get_analytics_summary(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Assert
    assert summary.total_likes == 0
    assert summary.total_comments == 0
    assert summary.total_reach == 0
    assert summary.total_impressions == 0
    assert summary.avg_engagement_rate == 0.0
    assert summary.campaign_count == 0
    assert summary.top_campaigns == []


@pytest.mark.asyncio
async def test_get_analytics_summary_with_data(analytics_service):
    """Test analytics summary with campaign data."""
    # Arrange
    user_id = "user-123"
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    
    # Create mock analytics
    analytics_list = [
        Analytics(
            campaign_id="campaign-1",
            user_id=user_id,
            likes=100,
            comments=20,
            reach=500,
            impressions=800,
            engagement_rate=24.0,
            fetched_at=datetime(2024, 1, 15)
        ),
        Analytics(
            campaign_id="campaign-2",
            user_id=user_id,
            likes=150,
            comments=30,
            reach=600,
            impressions=900,
            engagement_rate=30.0,
            fetched_at=datetime(2024, 1, 20)
        ),
        Analytics(
            campaign_id="campaign-3",
            user_id=user_id,
            likes=80,
            comments=10,
            reach=400,
            impressions=700,
            engagement_rate=22.5,
            fetched_at=datetime(2024, 1, 25)
        )
    ]
    
    analytics_service.analytics_repo.get_by_user_and_date_range = AsyncMock(
        side_effect=lambda uid, sd, ed: analytics_list if sd == start_date else []
    )
    
    # Act
    summary = await analytics_service.get_analytics_summary(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Assert
    assert summary.total_likes == 330
    assert summary.total_comments == 60
    assert summary.total_reach == 1500
    assert summary.total_impressions == 2400
    assert summary.avg_engagement_rate == pytest.approx(25.5, rel=0.1)
    assert summary.campaign_count == 3
    assert len(summary.top_campaigns) == 3
    assert summary.top_campaigns[0]['campaign_id'] == 'campaign-2'  # Highest engagement


@pytest.mark.asyncio
async def test_get_analytics_summary_with_trends(analytics_service):
    """Test analytics summary with trend calculation."""
    # Arrange
    user_id = "user-123"
    start_date = datetime(2024, 2, 1)
    end_date = datetime(2024, 2, 28)
    
    # Current period analytics
    current_analytics = [
        Analytics(
            campaign_id="campaign-1",
            user_id=user_id,
            likes=200,
            comments=40,
            reach=1000,
            impressions=1500,
            engagement_rate=24.0,
            fetched_at=datetime(2024, 2, 15)
        )
    ]
    
    # Previous period analytics
    previous_analytics = [
        Analytics(
            campaign_id="campaign-0",
            user_id=user_id,
            likes=100,
            comments=20,
            reach=500,
            impressions=800,
            engagement_rate=24.0,
            fetched_at=datetime(2024, 1, 15)
        )
    ]
    
    def mock_get_by_date_range(uid, sd, ed):
        if sd == start_date:
            return current_analytics
        else:
            return previous_analytics
    
    analytics_service.analytics_repo.get_by_user_and_date_range = AsyncMock(
        side_effect=mock_get_by_date_range
    )
    
    # Act
    summary = await analytics_service.get_analytics_summary(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Assert
    assert summary.trend_likes == pytest.approx(100.0, rel=0.1)  # 100% increase
    assert summary.trend_comments == pytest.approx(100.0, rel=0.1)
    assert summary.trend_reach == pytest.approx(100.0, rel=0.1)


@pytest.mark.asyncio
async def test_get_analytics_summary_top_campaigns(analytics_service):
    """Test that top campaigns are sorted by engagement rate."""
    # Arrange
    user_id = "user-123"
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    
    # Create 7 campaigns with different engagement rates
    analytics_list = [
        Analytics(
            campaign_id=f"campaign-{i}",
            user_id=user_id,
            likes=100 + i * 10,
            comments=20 + i * 2,
            reach=500,
            impressions=800,
            engagement_rate=20.0 + i * 2,
            fetched_at=datetime(2024, 1, 15)
        )
        for i in range(7)
    ]
    
    analytics_service.analytics_repo.get_by_user_and_date_range = AsyncMock(
        return_value=analytics_list
    )
    
    # Act
    summary = await analytics_service.get_analytics_summary(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Assert
    assert len(summary.top_campaigns) == 5  # Only top 5
    # Verify sorted by engagement rate descending
    for i in range(len(summary.top_campaigns) - 1):
        assert summary.top_campaigns[i]['engagement_rate'] >= summary.top_campaigns[i + 1]['engagement_rate']
    # Highest should be campaign-6
    assert summary.top_campaigns[0]['campaign_id'] == 'campaign-6'
