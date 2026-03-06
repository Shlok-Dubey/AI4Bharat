"""
Tests for analytics API endpoints.

Tests analytics aggregation endpoint.

Requirements: 8.3
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from shared.schemas.analytics import AnalyticsSummary
from shared.services.jwt_service import generate_access_token


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user ID."""
    return "user-123"


@pytest.fixture
def auth_headers(mock_auth_user):
    """Generate authentication headers with valid JWT."""
    token = generate_access_token(mock_auth_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_analytics_success(client: AsyncClient, auth_headers, mock_auth_user):
    """Test successful analytics retrieval."""
    # Arrange
    start_date = "2024-01-01T00:00:00"
    end_date = "2024-01-31T23:59:59"
    
    mock_summary = AnalyticsSummary(
        total_likes=500,
        total_comments=100,
        total_reach=2000,
        total_impressions=3000,
        avg_engagement_rate=30.0,
        campaign_count=5,
        top_campaigns=[
            {
                'campaign_id': 'campaign-1',
                'engagement_rate': 35.0,
                'likes': 150,
                'comments': 30,
                'reach': 500
            }
        ],
        trend_likes=20.0,
        trend_comments=15.0,
        trend_reach=10.0,
        trend_engagement_rate=5.0,
        start_date=datetime.fromisoformat(start_date),
        end_date=datetime.fromisoformat(end_date)
    )
    
    with patch('dev_api.routes.analytics.AnalyticsService') as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_analytics_summary = AsyncMock(return_value=mock_summary)
        mock_service_class.return_value = mock_service
        
        # Act
        response = await client.get(
            f"/api/v1/analytics?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data['total_likes'] == 500
    assert data['total_comments'] == 100
    assert data['total_reach'] == 2000
    assert data['avg_engagement_rate'] == 30.0
    assert data['campaign_count'] == 5
    assert len(data['top_campaigns']) == 1


@pytest.mark.asyncio
async def test_get_analytics_invalid_date_range(client: AsyncClient, auth_headers):
    """Test analytics with invalid date range (start after end)."""
    # Arrange
    start_date = "2024-01-31T00:00:00"
    end_date = "2024-01-01T00:00:00"
    
    # Act
    response = await client.get(
        f"/api/v1/analytics?start_date={start_date}&end_date={end_date}",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == 400
    assert "start_date must be before end_date" in response.json()['detail']


@pytest.mark.asyncio
async def test_get_analytics_missing_start_date(client: AsyncClient, auth_headers):
    """Test analytics with missing start_date parameter."""
    # Arrange
    end_date = "2024-01-31T00:00:00"
    
    # Act
    response = await client.get(
        f"/api/v1/analytics?end_date={end_date}",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_analytics_missing_end_date(client: AsyncClient, auth_headers):
    """Test analytics with missing end_date parameter."""
    # Arrange
    start_date = "2024-01-01T00:00:00"
    
    # Act
    response = await client.get(
        f"/api/v1/analytics?start_date={start_date}",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_analytics_unauthorized(client: AsyncClient):
    """Test analytics without authentication."""
    # Arrange
    start_date = "2024-01-01T00:00:00"
    end_date = "2024-01-31T00:00:00"
    
    # Act
    response = await client.get(
        f"/api/v1/analytics?start_date={start_date}&end_date={end_date}"
    )
    
    # Assert
    assert response.status_code == 403  # Forbidden (no auth header)


@pytest.mark.asyncio
async def test_get_analytics_no_data(client: AsyncClient, auth_headers, mock_auth_user):
    """Test analytics with no campaign data."""
    # Arrange
    start_date = "2024-01-01T00:00:00"
    end_date = "2024-01-31T23:59:59"
    
    mock_summary = AnalyticsSummary(
        total_likes=0,
        total_comments=0,
        total_reach=0,
        total_impressions=0,
        avg_engagement_rate=0.0,
        campaign_count=0,
        top_campaigns=[],
        start_date=datetime.fromisoformat(start_date),
        end_date=datetime.fromisoformat(end_date)
    )
    
    with patch('dev_api.routes.analytics.AnalyticsService') as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_analytics_summary = AsyncMock(return_value=mock_summary)
        mock_service_class.return_value = mock_service
        
        # Act
        response = await client.get(
            f"/api/v1/analytics?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data['total_likes'] == 0
    assert data['campaign_count'] == 0
    assert data['top_campaigns'] == []


@pytest.mark.asyncio
async def test_get_analytics_service_error(client: AsyncClient, auth_headers):
    """Test analytics with service error."""
    # Arrange
    start_date = "2024-01-01T00:00:00"
    end_date = "2024-01-31T00:00:00"
    
    with patch('dev_api.routes.analytics.AnalyticsService') as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_analytics_summary = AsyncMock(
            side_effect=Exception("Database error")
        )
        mock_service_class.return_value = mock_service
        
        # Act
        response = await client.get(
            f"/api/v1/analytics?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
    
    # Assert
    assert response.status_code == 500
    assert "Failed to retrieve analytics" in response.json()['detail']


@pytest.mark.asyncio
async def test_get_analytics_with_trends(client: AsyncClient, auth_headers, mock_auth_user):
    """Test analytics response includes trend data."""
    # Arrange
    start_date = "2024-02-01T00:00:00"
    end_date = "2024-02-28T23:59:59"
    
    mock_summary = AnalyticsSummary(
        total_likes=600,
        total_comments=120,
        total_reach=2500,
        total_impressions=3500,
        avg_engagement_rate=28.8,
        campaign_count=6,
        top_campaigns=[],
        trend_likes=20.0,
        trend_comments=20.0,
        trend_reach=25.0,
        trend_engagement_rate=-4.0,
        start_date=datetime.fromisoformat(start_date),
        end_date=datetime.fromisoformat(end_date)
    )
    
    with patch('dev_api.routes.analytics.AnalyticsService') as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_analytics_summary = AsyncMock(return_value=mock_summary)
        mock_service_class.return_value = mock_service
        
        # Act
        response = await client.get(
            f"/api/v1/analytics?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data['trend_likes'] == 20.0
    assert data['trend_comments'] == 20.0
    assert data['trend_reach'] == 25.0
    assert data['trend_engagement_rate'] == -4.0
