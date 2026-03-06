"""
Integration tests for campaign scheduling and cancellation endpoints.

Tests the complete flow from HTTP request to database and SQS.

Requirements: 6.1, 6.2, 6.5, 6.6
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from shared.models.domain import Campaign
from shared.services.jwt_service import generate_access_token


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user ID."""
    return "test-user-456"


@pytest.fixture
def auth_headers(mock_auth_user):
    """Generate authentication headers with valid JWT."""
    token = generate_access_token(mock_auth_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_campaign(mock_auth_user):
    """Create a mock campaign for testing."""
    return Campaign(
        campaign_id="test-campaign-123",
        user_id=mock_auth_user,
        product_id="test-product-789",
        caption="Test caption",
        hashtags=["#test", "#campaign"],
        status="draft",
    )


@pytest.fixture
def mock_scheduled_campaign(mock_auth_user):
    """Create a mock scheduled campaign for testing."""
    return Campaign(
        campaign_id="test-campaign-123",
        user_id=mock_auth_user,
        product_id="test-product-789",
        caption="Test caption",
        hashtags=["#test", "#campaign"],
        status="scheduled",
        scheduled_time=datetime.utcnow() + timedelta(hours=1),
    )


@pytest.mark.asyncio
async def test_schedule_campaign_success(client: AsyncClient, auth_headers, mock_auth_user, mock_campaign):
    """Test successful campaign scheduling. Requirements: 6.1, 6.2"""
    scheduled_time = datetime.utcnow() + timedelta(hours=1)
    
    with patch('dev_api.routes.campaigns.CampaignRepository') as mock_repo_class, \
         patch('dev_api.routes.campaigns.SchedulerService') as mock_scheduler_class:
        
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id = AsyncMock(return_value=mock_campaign)
        
        updated_campaign = Campaign(**mock_campaign.model_dump())
        updated_campaign.status = "scheduled"
        updated_campaign.scheduled_time = scheduled_time
        mock_repo.update = AsyncMock(return_value=updated_campaign)
        
        mock_scheduler = AsyncMock()
        mock_scheduler_class.return_value = mock_scheduler
        mock_scheduler.schedule_campaign = AsyncMock(return_value="msg-123")
        
        response = await client.post(
            f"/api/v1/campaigns/{mock_campaign.campaign_id}/schedule",
            json={"scheduled_time": scheduled_time.isoformat()},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['campaign_id'] == mock_campaign.campaign_id
        assert data['status'] == "scheduled"
        mock_repo.get_by_id.assert_called_once_with(mock_auth_user, mock_campaign.campaign_id)


@pytest.mark.asyncio
async def test_schedule_campaign_not_found(client: AsyncClient, auth_headers):
    """Test scheduling non-existent campaign. Requirements: 6.1"""
    scheduled_time = datetime.utcnow() + timedelta(hours=1)
    
    with patch('dev_api.routes.campaigns.CampaignRepository') as mock_repo_class, \
         patch('dev_api.routes.campaigns.SchedulerService') as mock_scheduler_class:
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id = AsyncMock(return_value=None)
        
        response = await client.post(
            "/api/v1/campaigns/nonexistent-id/schedule",
            json={"scheduled_time": scheduled_time.isoformat()},
            headers=auth_headers
        )
        
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_schedule_campaign_past_time(client: AsyncClient, auth_headers):
    """Test scheduling with past time. Requirements: 6.1"""
    past_time = datetime.utcnow() - timedelta(hours=1)
    
    response = await client.post(
        "/api/v1/campaigns/test-campaign-123/schedule",
        json={"scheduled_time": past_time.isoformat()},
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_cancel_campaign_success(client: AsyncClient, auth_headers, mock_auth_user, mock_scheduled_campaign):
    """Test successful campaign cancellation. Requirements: 6.5"""
    with patch('dev_api.routes.campaigns.CampaignRepository') as mock_repo_class, \
         patch('dev_api.routes.campaigns.SchedulerService') as mock_scheduler_class:
        
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id = AsyncMock(return_value=mock_scheduled_campaign)
        
        cancelled_campaign = Campaign(**mock_scheduled_campaign.model_dump())
        cancelled_campaign.status = "cancelled"
        mock_repo.update = AsyncMock(return_value=cancelled_campaign)
        
        mock_scheduler = AsyncMock()
        mock_scheduler_class.return_value = mock_scheduler
        mock_scheduler.cancel_campaign = AsyncMock(return_value=True)
        
        response = await client.post(
            f"/api/v1/campaigns/{mock_scheduled_campaign.campaign_id}/cancel",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == "cancelled"


@pytest.mark.asyncio
async def test_list_campaigns(client: AsyncClient, auth_headers, mock_auth_user):
    """Test listing campaigns with pagination. Requirements: 6.6"""
    campaigns = [
        Campaign(
            campaign_id=f"campaign-{i}",
            user_id=mock_auth_user,
            product_id="test-product-789",
            caption=f"Caption {i}",
            hashtags=["#test"],
            status="draft",
        )
        for i in range(5)
    ]
    
    with patch('dev_api.routes.campaigns.CampaignRepository') as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_user = AsyncMock(return_value=campaigns)
        
        response = await client.get(
            "/api/v1/campaigns?page=1&page_size=3",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 5
        assert len(data['campaigns']) == 3
