"""
Unit tests for encryption service.

Tests AES-256-GCM encryption/decryption and AWS Secrets Manager integration.
"""

import pytest
import base64
import os
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from shared.services.encryption_service import (
    encrypt_token,
    decrypt_token,
    get_encryption_key,
    clear_encryption_key_cache,
)


# Test encryption key (32 bytes for AES-256)
TEST_ENCRYPTION_KEY = base64.b64encode(os.urandom(32)).decode('utf-8')


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear encryption key cache before and after each test."""
    import shared.services.encryption_service as enc_service
    enc_service._encryption_key_cache = None
    enc_service._secrets_client = None
    yield
    enc_service._encryption_key_cache = None
    enc_service._secrets_client = None


@pytest.fixture
def mock_secrets_manager():
    """Mock AWS Secrets Manager client."""
    with patch('shared.services.encryption_service.boto3.client') as mock_client:
        mock_sm = MagicMock()
        mock_client.return_value = mock_sm
        
        # Default successful response
        mock_sm.get_secret_value.return_value = {
            'SecretString': TEST_ENCRYPTION_KEY
        }
        
        yield mock_sm


@pytest.mark.asyncio
async def test_get_encryption_key_success(mock_secrets_manager):
    """Test successful encryption key retrieval from Secrets Manager."""
    key = await get_encryption_key()
    
    assert key is not None
    assert len(key) == 32  # AES-256 requires 32 bytes
    assert isinstance(key, bytes)
    
    # Verify Secrets Manager was called
    mock_secrets_manager.get_secret_value.assert_called_once()


@pytest.mark.asyncio
async def test_get_encryption_key_caching(mock_secrets_manager):
    """Test that encryption key is cached after first retrieval."""
    # First call
    key1 = await get_encryption_key()
    
    # Second call
    key2 = await get_encryption_key()
    
    # Should be the same key
    assert key1 == key2
    
    # Secrets Manager should only be called once (cached)
    assert mock_secrets_manager.get_secret_value.call_count == 1


@pytest.mark.asyncio
async def test_get_encryption_key_not_found(mock_secrets_manager):
    """Test error handling when encryption key not found."""
    mock_secrets_manager.get_secret_value.side_effect = ClientError(
        {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
        'GetSecretValue'
    )
    
    with pytest.raises(RuntimeError, match="Encryption key not found"):
        await get_encryption_key()


@pytest.mark.asyncio
async def test_get_encryption_key_access_denied(mock_secrets_manager):
    """Test error handling when access denied to encryption key."""
    mock_secrets_manager.get_secret_value.side_effect = ClientError(
        {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access denied'}},
        'GetSecretValue'
    )
    
    with pytest.raises(RuntimeError, match="Access denied"):
        await get_encryption_key()


@pytest.mark.asyncio
async def test_get_encryption_key_invalid_length(mock_secrets_manager):
    """Test error handling when encryption key has invalid length."""
    # Return a key that's not 32 bytes
    invalid_key = base64.b64encode(b'short').decode('utf-8')
    mock_secrets_manager.get_secret_value.return_value = {
        'SecretString': invalid_key
    }
    
    with pytest.raises(RuntimeError, match="Invalid encryption key length"):
        await get_encryption_key()


@pytest.mark.asyncio
async def test_encrypt_token_success(mock_secrets_manager):
    """Test successful token encryption."""
    plaintext = "instagram_access_token_12345"
    
    encrypted = await encrypt_token(plaintext)
    
    # Should return base64-encoded string
    assert isinstance(encrypted, str)
    assert len(encrypted) > 0
    
    # Should be valid base64
    decoded = base64.b64decode(encrypted)
    assert len(decoded) > 12  # At least nonce (12 bytes) + some ciphertext


@pytest.mark.asyncio
async def test_encrypt_token_empty_string(mock_secrets_manager):
    """Test that encrypting empty string raises error."""
    with pytest.raises(ValueError, match="Cannot encrypt empty token"):
        await encrypt_token("")


@pytest.mark.asyncio
async def test_decrypt_token_success(mock_secrets_manager):
    """Test successful token decryption."""
    plaintext = "instagram_access_token_12345"
    
    # Encrypt
    encrypted = await encrypt_token(plaintext)
    
    # Decrypt
    decrypted = await decrypt_token(encrypted)
    
    # Should match original
    assert decrypted == plaintext


@pytest.mark.asyncio
async def test_encrypt_decrypt_round_trip(mock_secrets_manager):
    """Test encryption and decryption round trip with various tokens."""
    test_tokens = [
        "short",
        "instagram_access_token_with_special_chars_!@#$%",
        "very_long_token_" + "x" * 1000,
        "token_with_unicode_émojis_🔐",
    ]
    
    for token in test_tokens:
        encrypted = await encrypt_token(token)
        decrypted = await decrypt_token(encrypted)
        assert decrypted == token, f"Round trip failed for token: {token}"


@pytest.mark.asyncio
async def test_decrypt_token_invalid_base64(mock_secrets_manager):
    """Test error handling when decrypting invalid base64."""
    with pytest.raises(ValueError, match="not valid base64"):
        await decrypt_token("not_valid_base64!!!")


@pytest.mark.asyncio
async def test_decrypt_token_too_short(mock_secrets_manager):
    """Test error handling when encrypted data is too short."""
    # Create data shorter than nonce size (12 bytes)
    short_data = base64.b64encode(b"short").decode('utf-8')
    
    with pytest.raises(ValueError, match="too short"):
        await decrypt_token(short_data)


@pytest.mark.asyncio
async def test_decrypt_token_empty_string(mock_secrets_manager):
    """Test that decrypting empty string raises error."""
    with pytest.raises(ValueError, match="Cannot decrypt empty data"):
        await decrypt_token("")


@pytest.mark.asyncio
async def test_decrypt_token_tampered_data(mock_secrets_manager):
    """Test that tampering with encrypted data is detected."""
    plaintext = "instagram_access_token_12345"
    
    # Encrypt
    encrypted = await encrypt_token(plaintext)
    
    # Tamper with the encrypted data
    encrypted_bytes = base64.b64decode(encrypted)
    tampered_bytes = encrypted_bytes[:-1] + b'X'  # Change last byte
    tampered_encrypted = base64.b64encode(tampered_bytes).decode('utf-8')
    
    # Decryption should fail with authentication error
    with pytest.raises(RuntimeError, match="authentication tag verification failed"):
        await decrypt_token(tampered_encrypted)


@pytest.mark.asyncio
async def test_different_encryptions_produce_different_ciphertext(mock_secrets_manager):
    """Test that encrypting the same plaintext twice produces different ciphertext."""
    plaintext = "instagram_access_token_12345"
    
    encrypted1 = await encrypt_token(plaintext)
    encrypted2 = await encrypt_token(plaintext)
    
    # Should be different due to random nonce
    assert encrypted1 != encrypted2
    
    # But both should decrypt to same plaintext
    decrypted1 = await decrypt_token(encrypted1)
    decrypted2 = await decrypt_token(encrypted2)
    assert decrypted1 == plaintext
    assert decrypted2 == plaintext
