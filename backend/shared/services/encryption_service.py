"""
Encryption service for sensitive data (Instagram tokens).

Uses AES-256-GCM encryption with keys stored in AWS Secrets Manager.
Implements key caching for Lambda execution duration.
"""

import os
import base64
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
import boto3
from botocore.exceptions import ClientError


# Module-level cache for encryption key (persists for Lambda execution duration)
_encryption_key_cache: Optional[bytes] = None
_secrets_client = None


def _get_secrets_client():
    """Get or create Secrets Manager client (singleton pattern)."""
    global _secrets_client
    if _secrets_client is None:
        region = os.getenv('AWS_REGION', 'us-east-1')
        _secrets_client = boto3.client('secretsmanager', region_name=region)
    return _secrets_client


async def get_encryption_key() -> bytes:
    """
    Retrieve encryption key from AWS Secrets Manager.
    
    Caches the key in Lambda memory for the duration of execution
    to avoid repeated Secrets Manager API calls.
    
    Returns:
        bytes: 32-byte encryption key for AES-256
        
    Raises:
        RuntimeError: If key retrieval fails or key is invalid
    """
    global _encryption_key_cache
    
    # Return cached key if available
    if _encryption_key_cache is not None:
        return _encryption_key_cache
    
    # Retrieve key from Secrets Manager
    secret_name = os.getenv('ENCRYPTION_KEY_SECRET_NAME', 'postpilot/encryption-key')
    
    try:
        client = _get_secrets_client()
        response = client.get_secret_value(SecretId=secret_name)
        
        # Extract secret string
        if 'SecretString' in response:
            secret_value = response['SecretString']
        else:
            # Binary secret
            secret_value = base64.b64decode(response['SecretBinary']).decode('utf-8')
        
        # Convert to bytes (expect base64-encoded key)
        try:
            key_bytes = base64.b64decode(secret_value)
        except Exception:
            # If not base64, use raw bytes
            key_bytes = secret_value.encode('utf-8')
        
        # Validate key length (must be 32 bytes for AES-256)
        if len(key_bytes) != 32:
            raise RuntimeError(
                f"Invalid encryption key length: {len(key_bytes)} bytes. "
                "Expected 32 bytes for AES-256."
            )
        
        # Cache the key
        _encryption_key_cache = key_bytes
        return key_bytes
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            raise RuntimeError(
                f"Encryption key not found in Secrets Manager: {secret_name}"
            ) from e
        elif error_code == 'AccessDeniedException':
            raise RuntimeError(
                f"Access denied to encryption key in Secrets Manager: {secret_name}"
            ) from e
        else:
            raise RuntimeError(
                f"Failed to retrieve encryption key from Secrets Manager: {str(e)}"
            ) from e
    except Exception as e:
        raise RuntimeError(
            f"Unexpected error retrieving encryption key: {str(e)}"
        ) from e


async def encrypt_token(plaintext: str) -> str:
    """
    Encrypt a token using AES-256-GCM.
    
    Args:
        plaintext: The token to encrypt (e.g., Instagram access token)
        
    Returns:
        str: Base64-encoded encrypted data in format: nonce||ciphertext||tag
             Components are concatenated and base64-encoded together
             
    Raises:
        RuntimeError: If encryption fails
    """
    if not plaintext:
        raise ValueError("Cannot encrypt empty token")
    
    try:
        # Get encryption key
        key = await get_encryption_key()
        
        # Create AESGCM cipher
        aesgcm = AESGCM(key)
        
        # Generate random nonce (12 bytes is standard for GCM)
        nonce = os.urandom(12)
        
        # Encrypt the plaintext
        # AESGCM.encrypt returns ciphertext with authentication tag appended
        plaintext_bytes = plaintext.encode('utf-8')
        ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext_bytes, None)
        
        # Combine nonce + ciphertext_with_tag
        encrypted_data = nonce + ciphertext_with_tag
        
        # Base64 encode for storage
        encoded = base64.b64encode(encrypted_data).decode('utf-8')
        
        return encoded
        
    except Exception as e:
        raise RuntimeError(f"Token encryption failed: {str(e)}") from e


async def decrypt_token(encrypted_data: str) -> str:
    """
    Decrypt a token using AES-256-GCM.
    
    Args:
        encrypted_data: Base64-encoded encrypted data (nonce||ciphertext||tag)
        
    Returns:
        str: Decrypted plaintext token
        
    Raises:
        RuntimeError: If decryption fails
        ValueError: If encrypted data format is invalid
    """
    if not encrypted_data:
        raise ValueError("Cannot decrypt empty data")
    
    try:
        # Base64 decode
        encrypted_bytes = base64.b64decode(encrypted_data)
        
        # Extract nonce (first 12 bytes)
        if len(encrypted_bytes) < 12:
            raise ValueError("Invalid encrypted data: too short")
        
        nonce = encrypted_bytes[:12]
        ciphertext_with_tag = encrypted_bytes[12:]
        
        # Get encryption key
        key = await get_encryption_key()
        
        # Create AESGCM cipher
        aesgcm = AESGCM(key)
        
        # Decrypt
        try:
            plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
        except InvalidTag:
            raise RuntimeError(
                "Token decryption failed: authentication tag verification failed. "
                "Data may have been tampered with or key is incorrect."
            )
        
        # Convert to string
        plaintext = plaintext_bytes.decode('utf-8')
        
        return plaintext
        
    except base64.binascii.Error as e:
        raise ValueError(f"Invalid encrypted data format: not valid base64") from e
    except UnicodeDecodeError as e:
        raise RuntimeError(f"Decrypted data is not valid UTF-8") from e
    except Exception as e:
        if isinstance(e, (RuntimeError, ValueError)):
            raise
        raise RuntimeError(f"Token decryption failed: {str(e)}") from e


def clear_encryption_key_cache():
    """
    Clear the cached encryption key.
    
    Useful for testing or when key rotation occurs.
    In production Lambda, the cache persists for the execution environment lifetime.
    """
    global _encryption_key_cache
    _encryption_key_cache = None
