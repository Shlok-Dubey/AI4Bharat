"""
Tests for Instagram insights fetching.

Tests Instagram Graph API insights integration.

Requirements: 8.1
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from shared.services.instagram_service import InstagramService
from shared.schemas.instagram import InstagramInsights


@pytest.fixture
def instagram_service():
    """Create InstagramService instance."""
    return InstagramService()


@pytest.mark.asyncio
async def test_fetch_insights_success(instagram_service):
    """Test successful insights fetching."""
    # Arrange
    access_token = "test-token"
    post_id = "post-123"
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'data': [
            {'name': 'likes', 'values': [{'value': 150}]},
            {'name': 'comments', 'values': [{'value': 30}]},
            {'name': 'reach', 'values': [{'value': 500}]},
            {'name': 'impressions', 'values': [{'value': 800}]}
        ]
    }
    mock_response.raise_for_status = MagicMock()
    
    # Mock httpx.AsyncClient
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        # Act
        insights = await instagram_service.fetch_insights(
            access_token=access_token,
            post_id=post_id
        )
    
    # Assert
    assert isinstance(insights, InstagramInsights)
    assert insights.likes == 150
    assert insights.comments == 30
    assert insights.reach == 500
    assert insights.impressions == 800
    # Engagement rate = (150 + 30) / 500 * 100 = 36%
    assert insights.engagement_rate == pytest.approx(36.0, rel=0.1)


@pytest.mark.asyncio
async def test_fetch_insights_zero_reach(instagram_service):
    """Test insights with zero reach (engagement rate should be 0)."""
    # Arrange
    access_token = "test-token"
    post_id = "post-123"
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'data': [
            {'name': 'likes', 'values': [{'value': 100}]},
            {'name': 'comments', 'values': [{'value': 20}]},
            {'name': 'reach', 'values': [{'value': 0}]},
            {'name': 'impressions', 'values': [{'value': 0}]}
        ]
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        # Act
        insights = await instagram_service.fetch_insights(
            access_token=access_token,
            post_id=post_id
        )
    
    # Assert
    assert insights.reach == 0
    assert insights.engagement_rate == 0.0


@pytest.mark.asyncio
async def test_fetch_insights_missing_metrics(instagram_service):
    """Test insights with missing metrics (should default to 0)."""
    # Arrange
    access_token = "test-token"
    post_id = "post-123"
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'data': [
            {'name': 'likes', 'values': [{'value': 50}]},
            # Missing comments, reach, impressions
        ]
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        # Act
        insights = await instagram_service.fetch_insights(
            access_token=access_token,
            post_id=post_id
        )
    
    # Assert
    assert insights.likes == 50
    assert insights.comments == 0
    assert insights.reach == 0
    assert insights.impressions == 0
    assert insights.engagement_rate == 0.0


@pytest.mark.asyncio
async def test_fetch_insights_api_error(instagram_service):
    """Test insights fetching with API error."""
    # Arrange
    access_token = "test-token"
    post_id = "post-123"
    
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad Request",
        request=MagicMock(),
        response=mock_response
    )
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        # Act & Assert
        with pytest.raises(httpx.HTTPStatusError):
            await instagram_service.fetch_insights(
                access_token=access_token,
                post_id=post_id
            )


@pytest.mark.asyncio
async def test_fetch_insights_engagement_calculation(instagram_service):
    """Test engagement rate calculation formula."""
    # Arrange
    access_token = "test-token"
    post_id = "post-123"
    
    # Test case: 100 likes + 50 comments = 150 engagements
    # Reach: 1000 users
    # Expected engagement rate: (150 / 1000) * 100 = 15%
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'data': [
            {'name': 'likes', 'values': [{'value': 100}]},
            {'name': 'comments', 'values': [{'value': 50}]},
            {'name': 'reach', 'values': [{'value': 1000}]},
            {'name': 'impressions', 'values': [{'value': 1500}]}
        ]
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        # Act
        insights = await instagram_service.fetch_insights(
            access_token=access_token,
            post_id=post_id
        )
    
    # Assert
    assert insights.engagement_rate == pytest.approx(15.0, rel=0.01)


@pytest.mark.asyncio
async def test_fetch_insights_correct_api_call(instagram_service):
    """Test that insights API is called with correct parameters."""
    # Arrange
    access_token = "test-token"
    post_id = "post-123"
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'data': []}
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        # Act
        await instagram_service.fetch_insights(
            access_token=access_token,
            post_id=post_id
        )
        
        # Assert
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        
        # Verify URL
        assert f"/{post_id}/insights" in call_args[0][0]
        
        # Verify params
        params = call_args[1]['params']
        assert params['metric'] == 'likes,comments,reach,impressions'
        assert params['access_token'] == access_token
