"""
Tests for Instagram OAuth integration.

Tests Requirements: 2.1, 2.2, 2.3, 2.4, 2.6
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from httpx import AsyncClient

from shared.schemas.instagram import (
    InstagramTokenResponse,
    InstagramLongLivedTokenResponse,
    InstagramRefreshTokenResponse,
    InstagramUserProfile,
)
from shared.services.instagram_service import InstagramService, refresh_instagram_token
from shared.models.domain import User
from repositories.user_repository import UserRepository


class TestInstagramAuthorizationUrl:
    """Test Instagram authorization URL generation (Requirement 2.1)."""
    
    @pytest.mark.asyncio
    async def test_get_authorization_url_authenticated(self, client: AsyncClient):
        """Test GET /api/v1/instagram/authorize returns authorization URL."""
        # Override the dependency
        from dev_api.main import app
        from dev_api.routes.instagram import get_current_user
        
        async def mock_get_current_user():
            return 'test-user-123'
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            with patch.dict('os.environ', {
                'INSTAGRAM_CLIENT_ID': 'test_client_id',
                'INSTAGRAM_REDIRECT_URI': 'http://localhost:8000/callback'
            }):
                response = await client.get('/api/v1/instagram/authorize')
                
                assert response.status_code == 200
                data = response.json()
                assert 'authorization_url' in data
                assert 'api.instagram.com/oauth/authorize' in data['authorization_url']
                assert 'test_client_id' in data['authorization_url']
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_get_authorization_url_unauthenticated(self, client: AsyncClient):
        """Test authorization URL endpoint requires authentication."""
        response = await client.get('/api/v1/instagram/authorize')
        assert response.status_code == 403  # HTTPBearer returns 403 when no auth header


class TestInstagramOAuthCallback:
    """Test Instagram OAuth callback handling (Requirements 2.2, 2.3, 2.6)."""
    
    @pytest.mark.asyncio
    async def test_oauth_callback_success(self, client: AsyncClient):
        """Test successful OAuth callback flow."""
        from dev_api.main import app
        from dev_api.routes.instagram import get_current_user
        
        # Mock user
        mock_user = User(
            user_id='test-user-123',
            email='test@example.com',
            password_hash='hashed'
        )
        
        # Override authentication dependency
        async def mock_get_current_user():
            return 'test-user-123'
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            # Mock Instagram service methods
            with patch('dev_api.routes.instagram.InstagramService') as MockInstagramService:
                mock_service = MockInstagramService.return_value
                
                # Mock token exchange
                mock_service.exchange_code_for_token = AsyncMock(return_value=InstagramTokenResponse(
                    access_token='short_lived_token',
                    user_id=123456789
                ))
                
                # Mock long-lived token exchange
                mock_service.exchange_for_long_lived_token = AsyncMock(
                    return_value=InstagramLongLivedTokenResponse(
                        access_token='long_lived_token',
                        token_type='bearer',
                        expires_in=5184000  # 60 days
                    )
                )
                
                # Mock user profile fetch
                mock_service.get_user_profile = AsyncMock(return_value=InstagramUserProfile(
                    id='123456789',
                    username='testuser',
                    account_type='BUSINESS',
                    media_count=50
                ))
                
                # Mock token expiry calculation
                mock_service.calculate_token_expiry = MagicMock(
                    return_value=datetime.utcnow() + timedelta(days=60)
                )
                
                # Mock encryption
                with patch('dev_api.routes.instagram.encrypt_token') as mock_encrypt:
                    mock_encrypt.return_value = 'encrypted_token_data'
                    
                    # Mock user repository
                    with patch('dev_api.routes.instagram.UserRepository') as MockUserRepo:
                        mock_repo = MockUserRepo.return_value
                        mock_repo.get_by_id = AsyncMock(return_value=mock_user)
                        mock_repo.update = AsyncMock(return_value=mock_user)
                        
                        # Make request
                        response = await client.get(
                            '/api/v1/instagram/callback',
                            params={
                                'code': 'test_auth_code',
                                'state': 'test-user-123'
                            }
                        )
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data['success'] is True
                        assert data['instagram_username'] == 'testuser'
                        assert data['instagram_user_id'] == '123456789'
                        assert 'Successfully connected' in data['message']
                        
                        # Verify encryption was called
                        mock_encrypt.assert_called_once_with('long_lived_token')
                        
                        # Verify user was updated
                        mock_repo.update.assert_called_once()
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_oauth_callback_state_mismatch(self, client: AsyncClient):
        """Test OAuth callback rejects mismatched state parameter."""
        from dev_api.main import app
        from dev_api.routes.instagram import get_current_user
        
        async def mock_get_current_user():
            return 'test-user-123'
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            response = await client.get(
                '/api/v1/instagram/callback',
                params={
                    'code': 'test_auth_code',
                    'state': 'different-user-id'  # Mismatch
                }
            )
            
            assert response.status_code == 400
            assert 'Invalid state parameter' in response.json()['detail']
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_oauth_callback_missing_code(self, client: AsyncClient):
        """Test OAuth callback requires authorization code."""
        from dev_api.main import app
        from dev_api.routes.instagram import get_current_user
        
        async def mock_get_current_user():
            return 'test-user-123'
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            response = await client.get('/api/v1/instagram/callback')
            
            assert response.status_code == 422  # Validation error
        finally:
            app.dependency_overrides.clear()


class TestInstagramService:
    """Test InstagramService methods."""
    
    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        with patch.dict('os.environ', {
            'INSTAGRAM_CLIENT_ID': 'test_client_id',
            'INSTAGRAM_REDIRECT_URI': 'http://localhost:8000/callback'
        }):
            service = InstagramService()
            url = service.get_authorization_url(state='test-state')
            
            assert 'api.instagram.com/oauth/authorize' in url
            assert 'client_id=test_client_id' in url
            assert 'redirect_uri=' in url
            assert 'state=test-state' in url
            assert 'scope=user_profile%2Cuser_media' in url
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self):
        """Test exchanging authorization code for token."""
        with patch.dict('os.environ', {
            'INSTAGRAM_CLIENT_ID': 'test_client_id',
            'INSTAGRAM_CLIENT_SECRET': 'test_secret',
            'INSTAGRAM_REDIRECT_URI': 'http://localhost:8000/callback'
        }):
            service = InstagramService()
            
            # Mock httpx client
            with patch('httpx.AsyncClient') as MockClient:
                mock_client = MockClient.return_value.__aenter__.return_value
                mock_response = MagicMock()
                mock_response.json = MagicMock(return_value={
                    'access_token': 'test_token',
                    'user_id': 123456789
                })
                mock_response.raise_for_status = MagicMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                
                result = await service.exchange_code_for_token('test_code')
                
                assert result.access_token == 'test_token'
                assert result.user_id == 123456789
    
    @pytest.mark.asyncio
    async def test_exchange_for_long_lived_token(self):
        """Test exchanging short-lived token for long-lived token."""
        with patch.dict('os.environ', {
            'INSTAGRAM_CLIENT_SECRET': 'test_secret'
        }):
            service = InstagramService()
            
            with patch('httpx.AsyncClient') as MockClient:
                mock_client = MockClient.return_value.__aenter__.return_value
                mock_response = MagicMock()
                mock_response.json = MagicMock(return_value={
                    'access_token': 'long_lived_token',
                    'token_type': 'bearer',
                    'expires_in': 5184000
                })
                mock_response.raise_for_status = MagicMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                
                result = await service.exchange_for_long_lived_token('short_token')
                
                assert result.access_token == 'long_lived_token'
                assert result.expires_in == 5184000
    
    @pytest.mark.asyncio
    async def test_refresh_access_token(self):
        """Test refreshing access token (Requirement 2.4)."""
        service = InstagramService()
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value={
                'access_token': 'refreshed_token',
                'token_type': 'bearer',
                'expires_in': 5184000
            })
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            
            result = await service.refresh_access_token('current_token')
            
            assert result.access_token == 'refreshed_token'
            assert result.expires_in == 5184000
    
    @pytest.mark.asyncio
    async def test_get_user_profile(self):
        """Test fetching Instagram user profile (Requirement 2.6)."""
        service = InstagramService()
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value={
                'id': '123456789',
                'username': 'testuser',
                'account_type': 'BUSINESS',
                'media_count': 50
            })
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            
            result = await service.get_user_profile('test_token')
            
            assert result.id == '123456789'
            assert result.username == 'testuser'
            assert result.account_type == 'BUSINESS'
            assert result.media_count == 50
    
    def test_calculate_token_expiry(self):
        """Test token expiry calculation."""
        service = InstagramService()
        
        expires_in = 5184000  # 60 days
        expiry = service.calculate_token_expiry(expires_in)
        
        expected = datetime.utcnow() + timedelta(seconds=expires_in)
        # Allow 1 second tolerance
        assert abs((expiry - expected).total_seconds()) < 1
    
    def test_is_token_expired(self):
        """Test token expiry check."""
        service = InstagramService()
        
        # Token expires in 10 days - should be considered expired (7 day buffer)
        expires_at = datetime.utcnow() + timedelta(days=10)
        assert service.is_token_expired(expires_at) is False
        
        # Token expires in 5 days - should be considered expired
        expires_at = datetime.utcnow() + timedelta(days=5)
        assert service.is_token_expired(expires_at) is True
        
        # Token already expired
        expires_at = datetime.utcnow() - timedelta(days=1)
        assert service.is_token_expired(expires_at) is True


class TestRefreshInstagramToken:
    """Test refresh_instagram_token function (Requirement 2.4)."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test successful token refresh."""
        # Mock user with encrypted token
        mock_user = User(
            user_id='test-user-123',
            email='test@example.com',
            password_hash='hashed',
            instagram_access_token='encrypted_token',
            instagram_token_expires_at=datetime.utcnow() + timedelta(days=5)
        )
        
        # Mock user repository
        mock_repo = AsyncMock(spec=UserRepository)
        mock_repo.get_by_id = AsyncMock(return_value=mock_user)
        mock_repo.update = AsyncMock(return_value=mock_user)
        
        # Mock decryption
        with patch('shared.services.encryption_service.decrypt_token') as mock_decrypt:
            mock_decrypt.return_value = 'decrypted_token'
            
            # Mock Instagram service
            with patch('shared.services.instagram_service.InstagramService') as MockService:
                mock_service = MockService.return_value
                mock_service.refresh_access_token = AsyncMock(
                    return_value=InstagramRefreshTokenResponse(
                        access_token='new_token',
                        token_type='bearer',
                        expires_in=5184000
                    )
                )
                mock_service.calculate_token_expiry = MagicMock(
                    return_value=datetime.utcnow() + timedelta(days=60)
                )
                
                # Mock encryption
                with patch('shared.services.encryption_service.encrypt_token') as mock_encrypt:
                    mock_encrypt.return_value = 'new_encrypted_token'
                    
                    # Call refresh function
                    result = await refresh_instagram_token('test-user-123', mock_repo)
                    
                    assert result is True
                    mock_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_token_user_not_found(self):
        """Test token refresh when user doesn't exist."""
        mock_repo = AsyncMock(spec=UserRepository)
        mock_repo.get_by_id = AsyncMock(return_value=None)
        
        result = await refresh_instagram_token('nonexistent-user', mock_repo)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_refresh_token_no_instagram_token(self):
        """Test token refresh when user has no Instagram token."""
        mock_user = User(
            user_id='test-user-123',
            email='test@example.com',
            password_hash='hashed'
        )
        
        mock_repo = AsyncMock(spec=UserRepository)
        mock_repo.get_by_id = AsyncMock(return_value=mock_user)
        
        result = await refresh_instagram_token('test-user-123', mock_repo)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_refresh_token_api_failure(self):
        """Test token refresh when Instagram API fails."""
        mock_user = User(
            user_id='test-user-123',
            email='test@example.com',
            password_hash='hashed',
            instagram_access_token='encrypted_token'
        )
        
        mock_repo = AsyncMock(spec=UserRepository)
        mock_repo.get_by_id = AsyncMock(return_value=mock_user)
        
        with patch('shared.services.encryption_service.decrypt_token') as mock_decrypt:
            mock_decrypt.return_value = 'decrypted_token'
            
            with patch('shared.services.instagram_service.InstagramService') as MockService:
                mock_service = MockService.return_value
                mock_service.refresh_access_token = AsyncMock(
                    side_effect=Exception('Instagram API error')
                )
                
                result = await refresh_instagram_token('test-user-123', mock_repo)
                
                assert result is False


class TestInstagramPublishing:
    """Test Instagram publishing methods (Requirements 7.1, 7.2, 7.3, 7.4, 19.1, 19.2, 30.1)."""
    
    @pytest.mark.asyncio
    async def test_publish_post_success(self):
        """Test successful post publishing."""
        service = InstagramService()
        
        with patch.object(service, '_create_media_container') as mock_create:
            with patch.object(service, '_poll_container_status') as mock_poll:
                with patch.object(service, '_publish_container') as mock_publish:
                    mock_create.return_value = 'container_123'
                    mock_poll.return_value = None
                    mock_publish.return_value = 'post_456'
                    
                    result = await service.publish_post(
                        access_token='test_token',
                        instagram_user_id='user_123',
                        image_url='https://example.com/image.jpg',
                        caption='Test caption #hashtag'
                    )
                    
                    assert result == 'post_456'
                    mock_create.assert_called_once()
                    mock_poll.assert_called_once_with('test_token', 'container_123')
                    mock_publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_media_container_success(self):
        """Test creating media container."""
        service = InstagramService()
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value={'id': 'container_123'})
            mock_response.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            
            result = await service._create_media_container(
                access_token='test_token',
                instagram_user_id='user_123',
                image_url='https://example.com/image.jpg',
                caption='Test caption'
            )
            
            assert result == 'container_123'
    
    @pytest.mark.asyncio
    async def test_create_media_container_retry_5xx(self):
        """Test retry logic for 5xx errors (Requirement 19.1)."""
        service = InstagramService()
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            # First two attempts return 500, third succeeds
            mock_response_500 = MagicMock()
            mock_response_500.status_code = 500
            
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json = MagicMock(return_value={'id': 'container_123'})
            mock_response_success.raise_for_status = MagicMock()
            
            mock_client.post = AsyncMock(
                side_effect=[mock_response_500, mock_response_500, mock_response_success]
            )
            
            with patch('asyncio.sleep') as mock_sleep:
                result = await service._create_media_container(
                    access_token='test_token',
                    instagram_user_id='user_123',
                    image_url='https://example.com/image.jpg',
                    caption='Test caption'
                )
                
                assert result == 'container_123'
                # Verify exponential backoff: 1s, 2s
                assert mock_sleep.call_count == 2
                mock_sleep.assert_any_call(1)
                mock_sleep.assert_any_call(2)
    
    @pytest.mark.asyncio
    async def test_create_media_container_retry_429(self):
        """Test retry logic for 429 rate limit (Requirement 19.2)."""
        service = InstagramService()
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            # First attempt returns 429, second succeeds
            mock_response_429 = MagicMock()
            mock_response_429.status_code = 429
            mock_response_429.headers = {'retry-after': '30'}
            
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json = MagicMock(return_value={'id': 'container_123'})
            mock_response_success.raise_for_status = MagicMock()
            
            mock_client.post = AsyncMock(
                side_effect=[mock_response_429, mock_response_success]
            )
            
            with patch('asyncio.sleep') as mock_sleep:
                result = await service._create_media_container(
                    access_token='test_token',
                    instagram_user_id='user_123',
                    image_url='https://example.com/image.jpg',
                    caption='Test caption'
                )
                
                assert result == 'container_123'
                # Verify retry-after header was respected
                mock_sleep.assert_called_once_with(30)
    
    @pytest.mark.asyncio
    async def test_poll_container_status_finished(self):
        """Test polling container status until finished."""
        service = InstagramService()
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            # First poll returns IN_PROGRESS, second returns FINISHED
            mock_response_progress = MagicMock()
            mock_response_progress.json = MagicMock(return_value={'status_code': 'IN_PROGRESS'})
            mock_response_progress.raise_for_status = MagicMock()
            
            mock_response_finished = MagicMock()
            mock_response_finished.json = MagicMock(return_value={'status_code': 'FINISHED'})
            mock_response_finished.raise_for_status = MagicMock()
            
            mock_client.get = AsyncMock(
                side_effect=[mock_response_progress, mock_response_finished]
            )
            
            with patch('asyncio.sleep') as mock_sleep:
                await service._poll_container_status('test_token', 'container_123')
                
                # Verify polling interval
                mock_sleep.assert_called_once_with(5)
    
    @pytest.mark.asyncio
    async def test_poll_container_status_timeout(self):
        """Test polling timeout (Requirement 30.1)."""
        service = InstagramService()
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            # Always return IN_PROGRESS
            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value={'status_code': 'IN_PROGRESS'})
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            
            with patch('asyncio.sleep'):
                with pytest.raises(TimeoutError) as exc_info:
                    await service._poll_container_status(
                        'test_token', 'container_123', max_wait_seconds=1
                    )
                
                assert 'not ready after 1s' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_poll_container_status_error(self):
        """Test polling when container processing fails."""
        service = InstagramService()
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            
            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value={'status_code': 'ERROR'})
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(RuntimeError) as exc_info:
                await service._poll_container_status('test_token', 'container_123')
            
            assert 'processing failed' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_publish_container_success(self):
        """Test publishing container to feed."""
        service = InstagramService()
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value={'id': 'post_456'})
            mock_response.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            
            result = await service._publish_container(
                access_token='test_token',
                instagram_user_id='user_123',
                container_id='container_123'
            )
            
            assert result == 'post_456'
    
    @pytest.mark.asyncio
    async def test_verify_post_exists_true(self):
        """Test verifying post exists (Requirement 18.1)."""
        service = InstagramService()
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get = AsyncMock(return_value=mock_response)
            
            result = await service.verify_post_exists('test_token', 'post_456')
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_post_exists_false(self):
        """Test verifying post doesn't exist (Requirement 18.1)."""
        service = InstagramService()
        
        with patch('httpx.AsyncClient') as MockClient:
            mock_client = MockClient.return_value.__aenter__.return_value
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.get = AsyncMock(return_value=mock_response)
            
            result = await service.verify_post_exists('test_token', 'post_456')
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_publish_with_idempotency_existing_post(self):
        """Test idempotent publishing with existing post (Requirement 18.3)."""
        service = InstagramService()
        
        with patch.object(service, 'verify_post_exists') as mock_verify:
            mock_verify.return_value = True
            
            result = await service.publish_with_idempotency_check(
                campaign_id='campaign_123',
                existing_post_id='post_456',
                access_token='test_token',
                instagram_user_id='user_123',
                image_url='https://example.com/image.jpg',
                caption='Test caption'
            )
            
            assert result == 'post_456'
            mock_verify.assert_called_once_with('test_token', 'post_456')
    
    @pytest.mark.asyncio
    async def test_publish_with_idempotency_post_not_found(self):
        """Test idempotent publishing when existing post not found (Requirement 18.3)."""
        service = InstagramService()
        
        with patch.object(service, 'verify_post_exists') as mock_verify:
            with patch.object(service, 'publish_post') as mock_publish:
                mock_verify.return_value = False
                mock_publish.return_value = 'post_789'
                
                result = await service.publish_with_idempotency_check(
                    campaign_id='campaign_123',
                    existing_post_id='post_456',
                    access_token='test_token',
                    instagram_user_id='user_123',
                    image_url='https://example.com/image.jpg',
                    caption='Test caption'
                )
                
                assert result == 'post_789'
                mock_verify.assert_called_once()
                mock_publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_with_idempotency_no_existing_post(self):
        """Test idempotent publishing with no existing post (Requirement 18.3)."""
        service = InstagramService()
        
        with patch.object(service, 'publish_post') as mock_publish:
            mock_publish.return_value = 'post_789'
            
            result = await service.publish_with_idempotency_check(
                campaign_id='campaign_123',
                existing_post_id=None,
                access_token='test_token',
                instagram_user_id='user_123',
                image_url='https://example.com/image.jpg',
                caption='Test caption'
            )
            
            assert result == 'post_789'
            mock_publish.assert_called_once()

