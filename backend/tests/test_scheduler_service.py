"""
Unit tests for SchedulerService.

Tests campaign scheduling logic including delay calculation and SQS integration.

Requirements: 6.2, 6.5
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from shared.services.scheduler_service import SchedulerService


@pytest.fixture
def scheduler_service():
    """Create SchedulerService instance with mocked SQS client."""
    with patch('shared.services.scheduler_service.SQSClient') as mock_sqs_class:
        mock_sqs = AsyncMock()
        mock_sqs_class.return_value = mock_sqs
        service = SchedulerService()
        service.sqs_client = mock_sqs
        yield service


@pytest.mark.asyncio
async def test_schedule_campaign_short_delay(scheduler_service):
    """
    Test scheduling campaign with delay < 15 minutes.
    
    Should use calculated delay_seconds.
    
    Requirements: 6.2
    """
    # Arrange
    campaign_id = "test-campaign-123"
    user_id = "test-user-456"
    scheduled_time = datetime.utcnow() + timedelta(minutes=10)
    
    scheduler_service.sqs_client.send_message = AsyncMock(return_value="msg-123")
    
    # Act
    message_id = await scheduler_service.schedule_campaign(
        campaign_id=campaign_id,
        user_id=user_id,
        scheduled_time=scheduled_time
    )
    
    # Assert
    assert message_id == "msg-123"
    
    # Verify SQS send_message was called
    scheduler_service.sqs_client.send_message.assert_called_once()
    call_args = scheduler_service.sqs_client.send_message.call_args
    
    # Check message body
    message_body = call_args.kwargs['message_body']
    assert message_body['campaign_id'] == campaign_id
    assert message_body['user_id'] == user_id
    assert message_body['scheduled_time'] == scheduled_time.isoformat()
    
    # Check deduplication ID
    assert call_args.kwargs['deduplication_id'] == campaign_id
    
    # Check delay is between 0 and 900 seconds
    delay = call_args.kwargs['delay_seconds']
    assert 0 <= delay <= 900


@pytest.mark.asyncio
async def test_schedule_campaign_long_delay(scheduler_service):
    """
    Test scheduling campaign with delay > 15 minutes.
    
    Should set delay_seconds to 0 and worker will check time.
    
    Requirements: 6.2
    """
    # Arrange
    campaign_id = "test-campaign-123"
    user_id = "test-user-456"
    scheduled_time = datetime.utcnow() + timedelta(hours=2)
    
    scheduler_service.sqs_client.send_message = AsyncMock(return_value="msg-123")
    
    # Act
    message_id = await scheduler_service.schedule_campaign(
        campaign_id=campaign_id,
        user_id=user_id,
        scheduled_time=scheduled_time
    )
    
    # Assert
    assert message_id == "msg-123"
    
    # Verify delay is 0 for long delays
    call_args = scheduler_service.sqs_client.send_message.call_args
    assert call_args.kwargs['delay_seconds'] == 0


@pytest.mark.asyncio
async def test_schedule_campaign_past_time(scheduler_service):
    """
    Test scheduling campaign with time in the past.
    
    Should set delay_seconds to 0 and send immediately.
    
    Requirements: 6.2
    """
    # Arrange
    campaign_id = "test-campaign-123"
    user_id = "test-user-456"
    scheduled_time = datetime.utcnow() - timedelta(minutes=5)
    
    scheduler_service.sqs_client.send_message = AsyncMock(return_value="msg-123")
    
    # Act
    message_id = await scheduler_service.schedule_campaign(
        campaign_id=campaign_id,
        user_id=user_id,
        scheduled_time=scheduled_time
    )
    
    # Assert
    assert message_id == "msg-123"
    
    # Verify delay is 0 for past times
    call_args = scheduler_service.sqs_client.send_message.call_args
    assert call_args.kwargs['delay_seconds'] == 0


@pytest.mark.asyncio
async def test_schedule_campaign_exactly_15_minutes(scheduler_service):
    """
    Test scheduling campaign with delay exactly 15 minutes (900 seconds).
    
    Should use delay_seconds = 900.
    
    Requirements: 6.2
    """
    # Arrange
    campaign_id = "test-campaign-123"
    user_id = "test-user-456"
    scheduled_time = datetime.utcnow() + timedelta(seconds=900)
    
    scheduler_service.sqs_client.send_message = AsyncMock(return_value="msg-123")
    
    # Act
    message_id = await scheduler_service.schedule_campaign(
        campaign_id=campaign_id,
        user_id=user_id,
        scheduled_time=scheduled_time
    )
    
    # Assert
    assert message_id == "msg-123"
    
    # Verify delay is <= 900
    call_args = scheduler_service.sqs_client.send_message.call_args
    assert call_args.kwargs['delay_seconds'] <= 900


@pytest.mark.asyncio
async def test_schedule_campaign_deduplication(scheduler_service):
    """
    Test that campaign_id is used for message deduplication.
    
    Requirements: 6.2
    """
    # Arrange
    campaign_id = "test-campaign-123"
    user_id = "test-user-456"
    scheduled_time = datetime.utcnow() + timedelta(minutes=5)
    
    scheduler_service.sqs_client.send_message = AsyncMock(return_value="msg-123")
    
    # Act
    await scheduler_service.schedule_campaign(
        campaign_id=campaign_id,
        user_id=user_id,
        scheduled_time=scheduled_time
    )
    
    # Assert
    call_args = scheduler_service.sqs_client.send_message.call_args
    assert call_args.kwargs['deduplication_id'] == campaign_id


@pytest.mark.asyncio
async def test_cancel_campaign(scheduler_service):
    """
    Test campaign cancellation (best effort).
    
    Should return True indicating cancellation was attempted.
    
    Requirements: 6.5
    """
    # Arrange
    campaign_id = "test-campaign-123"
    
    # Act
    result = await scheduler_service.cancel_campaign(campaign_id)
    
    # Assert
    assert result is True


@pytest.mark.asyncio
async def test_schedule_campaign_sqs_error(scheduler_service):
    """
    Test error handling when SQS send_message fails.
    
    Should propagate the exception.
    """
    # Arrange
    campaign_id = "test-campaign-123"
    user_id = "test-user-456"
    scheduled_time = datetime.utcnow() + timedelta(minutes=5)
    
    scheduler_service.sqs_client.send_message = AsyncMock(
        side_effect=Exception("SQS error")
    )
    
    # Act & Assert
    with pytest.raises(Exception, match="SQS error"):
        await scheduler_service.schedule_campaign(
            campaign_id=campaign_id,
            user_id=user_id,
            scheduled_time=scheduled_time
        )
