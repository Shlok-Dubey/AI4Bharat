"""
Integration tests for Publishing Worker Lambda.

Tests campaign publishing workflow including:
- Message processing with scheduled campaigns
- Atomic status updates
- Retry logic
- Dead-letter queue placement
"""
import pytest
import json
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock environment variables before importing modules
os.environ['AWS_S3_BUCKET_NAME'] = 'test-bucket'
os.environ['AWS_SQS_QUEUE_URL'] = 'https://sqs.us-east-1.amazonaws.com/123456789/test-queue'
os.environ['INSTAGRAM_CLIENT_ID'] = 'test-client-id'
os.environ['INSTAGRAM_CLIENT_SECRET'] = 'test-client-secret'
os.environ['INSTAGRAM_REDIRECT_URI'] = 'https://test.com/callback'

from lambdas.workers.publishing_worker import (
    process_campaign_publish_with_user_id,
    lambda_handler
)
from shared.models.domain import Campaign, User, Product, ImageAnalysis


@pytest.fixture
def mock_campaign():
    """Create a mock campaign for testing."""
    return Campaign(
        campaign_id="test-campaign-123",
        user_id="test-user-456",
        product_id="test-product-789",
        caption="Test caption",
        hashtags=["#test", "#automation"],
        status="scheduled",
        scheduled_time=datetime.utcnow() - timedelta(minutes=5),  # Past time
        publish_attempts=0
    )


@pytest.fixture
def mock_user():
    """Create a mock user with Instagram connection."""
    return User(
        user_id="test-user-456",
        email="test@example.com",
        password_hash="hashed",
        instagram_access_token="encrypted_token",
        instagram_user_id="instagram_123",
        instagram_username="testuser",
        instagram_token_expires_at=datetime.utcnow() + timedelta(days=30)  # Token not expired
    )


@pytest.fixture
def mock_product():
    """Create a mock product with image."""
    return Product(
        product_id="test-product-789",
        user_id="test-user-456",
        name="Test Product",
        description="Test description",
        image_url="https://s3.amazonaws.com/bucket/image.jpg",
        image_s3_key="test-user-456/products/test-product-789",
        image_analysis=ImageAnalysis(
            labels=["product", "item"],
            confidence_scores={"product": 0.95, "item": 0.90},
            has_faces=False,
            is_safe=True,
            dominant_colors=["#FFFFFF"]
        )
    )


@pytest.fixture
def sqs_event():
    """Create a mock SQS event."""
    return {
        "Records": [
            {
                "messageId": "msg-123",
                "receiptHandle": "receipt-handle-123",
                "body": json.dumps({
                    "user_id": "test-user-456",
                    "campaign_id": "test-campaign-123",
                    "scheduled_time": int((datetime.utcnow() - timedelta(minutes=5)).timestamp())
                }),
                "attributes": {
                    "ApproximateReceiveCount": "1"
                }
            }
        ]
    }


@pytest.mark.asyncio
async def test_process_campaign_not_ready():
    """Test that campaigns not ready for publishing are skipped."""
    future_time = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
    
    result = await process_campaign_publish_with_user_id(
        user_id="test-user",
        campaign_id="test-campaign",
        scheduled_time=future_time
    )
    
    assert result["status"] == "not_ready"
    assert "not ready" in result["message"].lower()


@pytest.mark.asyncio
@patch('lambdas.workers.publishing_worker.CampaignRepository')
async def test_atomic_status_update_already_processed(mock_campaign_repo_class):
    """Test that already processed campaigns are detected via atomic update."""
    # Mock repository to return False for atomic update (already processed)
    mock_repo = AsyncMock()
    mock_repo.atomic_status_update.return_value = False
    mock_campaign_repo_class.return_value = mock_repo
    
    past_time = int((datetime.utcnow() - timedelta(minutes=5)).timestamp())
    
    result = await process_campaign_publish_with_user_id(
        user_id="test-user",
        campaign_id="test-campaign",
        scheduled_time=past_time
    )
    
    assert result["status"] == "already_processed"
    
    # Verify atomic update was attempted
    mock_repo.atomic_status_update.assert_called_once_with(
        user_id="test-user",
        campaign_id="test-campaign",
        old_status="scheduled",
        new_status="publishing"
    )


@pytest.mark.asyncio
@patch('lambdas.workers.publishing_worker.S3Client')
@patch('lambdas.workers.publishing_worker.InstagramService')
@patch('lambdas.workers.publishing_worker.ProductRepository')
@patch('lambdas.workers.publishing_worker.UserRepository')
@patch('lambdas.workers.publishing_worker.CampaignRepository')
@patch('lambdas.workers.publishing_worker.decrypt_token')
async def test_successful_campaign_publish(
    mock_decrypt,
    mock_campaign_repo_class,
    mock_user_repo_class,
    mock_product_repo_class,
    mock_instagram_service_class,
    mock_s3_client_class,
    mock_campaign,
    mock_user,
    mock_product
):
    """Test successful campaign publishing workflow."""
    # Setup mocks
    mock_decrypt.return_value = "decrypted_token"
    
    mock_campaign_repo = AsyncMock()
    mock_campaign_repo.atomic_status_update.return_value = True
    mock_campaign_repo.get_by_id.return_value = mock_campaign
    mock_campaign_repo.update.return_value = mock_campaign
    mock_campaign_repo_class.return_value = mock_campaign_repo
    
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_id.return_value = mock_user
    mock_user_repo_class.return_value = mock_user_repo
    
    mock_product_repo = AsyncMock()
    mock_product_repo.get_by_id.return_value = mock_product
    mock_product_repo_class.return_value = mock_product_repo
    
    # Create mock Instagram service instance
    mock_instagram = MagicMock()
    mock_instagram.is_token_expired = MagicMock(return_value=False)  # Token not expired
    mock_instagram.publish_with_idempotency_check = AsyncMock(return_value="instagram_post_123")
    mock_instagram_service_class.return_value = mock_instagram
    
    mock_s3 = AsyncMock()
    mock_s3.generate_presigned_url.return_value = "https://presigned-url.com/image.jpg"
    mock_s3_client_class.return_value = mock_s3
    
    past_time = int((datetime.utcnow() - timedelta(minutes=5)).timestamp())
    
    # Execute
    result = await process_campaign_publish_with_user_id(
        user_id="test-user-456",
        campaign_id="test-campaign-123",
        scheduled_time=past_time
    )
    
    # Verify
    assert result["status"] == "success"
    assert result["instagram_post_id"] == "instagram_post_123"
    
    # Verify atomic update was called
    mock_campaign_repo.atomic_status_update.assert_called_once()
    
    # Verify Instagram publish was called
    mock_instagram.publish_with_idempotency_check.assert_called_once()
    
    # Verify campaign was updated with post_id
    mock_campaign_repo.update.assert_called_once()
    updated_campaign = mock_campaign_repo.update.call_args[0][0]
    assert updated_campaign.status == "published"
    assert updated_campaign.instagram_post_id == "instagram_post_123"


@pytest.mark.asyncio
@patch('lambdas.workers.publishing_worker.S3Client')
@patch('lambdas.workers.publishing_worker.InstagramService')
@patch('lambdas.workers.publishing_worker.ProductRepository')
@patch('lambdas.workers.publishing_worker.UserRepository')
@patch('lambdas.workers.publishing_worker.CampaignRepository')
@patch('lambdas.workers.publishing_worker.decrypt_token')
async def test_publish_failure_retry_logic(
    mock_decrypt,
    mock_campaign_repo_class,
    mock_user_repo_class,
    mock_product_repo_class,
    mock_instagram_service_class,
    mock_s3_client_class,
    mock_campaign,
    mock_user,
    mock_product
):
    """Test retry logic when publishing fails."""
    # Setup mocks
    mock_decrypt.return_value = "decrypted_token"
    
    mock_campaign_repo = AsyncMock()
    mock_campaign_repo.atomic_status_update.return_value = True
    mock_campaign_repo.get_by_id.return_value = mock_campaign
    mock_campaign_repo.update.return_value = mock_campaign
    mock_campaign_repo_class.return_value = mock_campaign_repo
    
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_id.return_value = mock_user
    mock_user_repo_class.return_value = mock_user_repo
    
    mock_product_repo = AsyncMock()
    mock_product_repo.get_by_id.return_value = mock_product
    mock_product_repo_class.return_value = mock_product_repo
    
    mock_instagram = AsyncMock()
    mock_instagram.is_token_expired.return_value = False
    mock_instagram.publish_with_idempotency_check.side_effect = Exception("Instagram API error")
    mock_instagram_service_class.return_value = mock_instagram
    
    mock_s3 = AsyncMock()
    mock_s3.generate_presigned_url.return_value = "https://presigned-url.com/image.jpg"
    mock_s3_client_class.return_value = mock_s3
    
    past_time = int((datetime.utcnow() - timedelta(minutes=5)).timestamp())
    
    # Execute - should raise exception for SQS retry
    with pytest.raises(Exception):
        await process_campaign_publish_with_user_id(
            user_id="test-user-456",
            campaign_id="test-campaign-123",
            scheduled_time=past_time
        )
    
    # Verify campaign was updated with error and incremented attempts
    mock_campaign_repo.update.assert_called_once()
    updated_campaign = mock_campaign_repo.update.call_args[0][0]
    assert updated_campaign.publish_attempts == 1
    assert updated_campaign.status == "scheduled"  # Reset for retry
    assert updated_campaign.last_error is not None


@pytest.mark.asyncio
@patch('lambdas.workers.publishing_worker.S3Client')
@patch('lambdas.workers.publishing_worker.InstagramService')
@patch('lambdas.workers.publishing_worker.ProductRepository')
@patch('lambdas.workers.publishing_worker.UserRepository')
@patch('lambdas.workers.publishing_worker.CampaignRepository')
@patch('lambdas.workers.publishing_worker.decrypt_token')
async def test_publish_failure_max_attempts(
    mock_decrypt,
    mock_campaign_repo_class,
    mock_user_repo_class,
    mock_product_repo_class,
    mock_instagram_service_class,
    mock_s3_client_class,
    mock_user,
    mock_product
):
    """Test that campaigns are marked failed after max attempts."""
    # Create campaign with 2 attempts already
    campaign = Campaign(
        campaign_id="test-campaign-123",
        user_id="test-user-456",
        product_id="test-product-789",
        caption="Test caption",
        hashtags=["#test"],
        status="scheduled",
        scheduled_time=datetime.utcnow() - timedelta(minutes=5),
        publish_attempts=2  # Already tried twice
    )
    
    # Setup mocks
    mock_decrypt.return_value = "decrypted_token"
    
    mock_campaign_repo = AsyncMock()
    mock_campaign_repo.atomic_status_update.return_value = True
    mock_campaign_repo.get_by_id.return_value = campaign
    mock_campaign_repo.update.return_value = campaign
    mock_campaign_repo_class.return_value = mock_campaign_repo
    
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_id.return_value = mock_user
    mock_user_repo_class.return_value = mock_user_repo
    
    mock_product_repo = AsyncMock()
    mock_product_repo.get_by_id.return_value = mock_product
    mock_product_repo_class.return_value = mock_product_repo
    
    mock_instagram = AsyncMock()
    mock_instagram.is_token_expired.return_value = False
    mock_instagram.publish_with_idempotency_check.side_effect = Exception("Instagram API error")
    mock_instagram_service_class.return_value = mock_instagram
    
    mock_s3 = AsyncMock()
    mock_s3.generate_presigned_url.return_value = "https://presigned-url.com/image.jpg"
    mock_s3_client_class.return_value = mock_s3
    
    past_time = int((datetime.utcnow() - timedelta(minutes=5)).timestamp())
    
    # Execute
    result = await process_campaign_publish_with_user_id(
        user_id="test-user-456",
        campaign_id="test-campaign-123",
        scheduled_time=past_time
    )
    
    # Verify campaign was marked as failed
    assert result["status"] == "failed"
    mock_campaign_repo.update.assert_called_once()
    updated_campaign = mock_campaign_repo.update.call_args[0][0]
    assert updated_campaign.publish_attempts == 3
    assert updated_campaign.status == "failed"


def test_lambda_handler_success(sqs_event):
    """Test Lambda handler with successful message processing."""
    with patch('lambdas.workers.publishing_worker.asyncio.run') as mock_run:
        mock_run.return_value = {
            "status": "success",
            "campaign_id": "test-campaign-123",
            "instagram_post_id": "instagram_post_123"
        }
        
        response = lambda_handler(sqs_event, None)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["processed"] == 1
        assert body["failed"] == 0


def test_lambda_handler_invalid_message():
    """Test Lambda handler with invalid message format."""
    invalid_event = {
        "Records": [
            {
                "messageId": "msg-123",
                "receiptHandle": "receipt-handle-123",
                "body": json.dumps({
                    "campaign_id": "test-campaign-123"
                    # Missing user_id and scheduled_time
                }),
                "attributes": {
                    "ApproximateReceiveCount": "1"
                }
            }
        ]
    }
    
    response = lambda_handler(invalid_event, None)
    
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["processed"] == 0
    assert body["failed"] == 1


def test_lambda_handler_dlq_logging(sqs_event):
    """Test that DLQ logging occurs on max retries."""
    # Modify event to simulate 3rd retry
    sqs_event["Records"][0]["attributes"]["ApproximateReceiveCount"] = "3"
    
    with patch('lambdas.workers.publishing_worker.asyncio.run') as mock_run:
        mock_run.side_effect = Exception("Persistent failure")
        
        with patch('lambdas.workers.publishing_worker.logger') as mock_logger:
            with pytest.raises(Exception):
                lambda_handler(sqs_event, None)
            
            # Verify critical log was called for DLQ
            critical_calls = [
                call for call in mock_logger.critical.call_args_list
                if "message_moving_to_dlq" in str(call)
            ]
            assert len(critical_calls) > 0
