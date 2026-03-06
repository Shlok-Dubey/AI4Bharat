"""Secrets Manager client wrapper for secure secret retrieval with caching."""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import aioboto3
from botocore.exceptions import ClientError


class SecretsManagerClient:
    """Async Secrets Manager client wrapper with in-memory caching."""
    
    def __init__(self):
        """Initialize Secrets Manager client with caching configuration."""
        self.session = aioboto3.Session()
        
        # In-memory cache for secrets
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Cache expiry duration: 1 hour
        self.cache_ttl = timedelta(hours=1)
    
    def _is_cache_valid(self, secret_id: str) -> bool:
        """
        Check if cached secret is still valid.
        
        Args:
            secret_id: Secret identifier
        
        Returns:
            True if cache is valid, False otherwise
        """
        if secret_id not in self._cache:
            return False
        
        cached_entry = self._cache[secret_id]
        expiry_time = cached_entry["cached_at"] + self.cache_ttl
        
        return datetime.utcnow() < expiry_time
    
    async def get_secret(self, secret_id: str) -> str:
        """
        Retrieve a secret from AWS Secrets Manager with caching.
        
        Secrets are cached in memory for 1 hour to reduce API calls and improve performance.
        
        Args:
            secret_id: Secret identifier (name or ARN)
        
        Returns:
            Secret value as string
        
        Raises:
            ClientError: If secret retrieval fails
        """
        # Check cache first
        if self._is_cache_valid(secret_id):
            return self._cache[secret_id]["value"]
        
        # Retrieve from Secrets Manager
        async with self.session.client("secretsmanager") as secrets_manager:
            response = await secrets_manager.get_secret_value(
                SecretId=secret_id
            )
            
            # Extract secret value
            if "SecretString" in response:
                secret_value = response["SecretString"]
            else:
                # Binary secret (base64 encoded)
                secret_value = response["SecretBinary"].decode("utf-8")
            
            # Cache the secret
            self._cache[secret_id] = {
                "value": secret_value,
                "cached_at": datetime.utcnow()
            }
            
            return secret_value
    
    async def get_secret_json(self, secret_id: str) -> Dict[str, Any]:
        """
        Retrieve a JSON secret from AWS Secrets Manager with caching.
        
        Args:
            secret_id: Secret identifier (name or ARN)
        
        Returns:
            Secret value as dictionary
        
        Raises:
            ClientError: If secret retrieval fails
            json.JSONDecodeError: If secret is not valid JSON
        """
        secret_string = await self.get_secret(secret_id)
        return json.loads(secret_string)
    
    def clear_cache(self, secret_id: Optional[str] = None) -> None:
        """
        Clear cached secrets.
        
        Args:
            secret_id: Optional specific secret to clear. If None, clears all cache.
        """
        if secret_id:
            self._cache.pop(secret_id, None)
        else:
            self._cache.clear()
    
    async def create_secret(
        self,
        secret_id: str,
        secret_value: str,
        description: Optional[str] = None
    ) -> str:
        """
        Create a new secret in AWS Secrets Manager.
        
        Args:
            secret_id: Secret name
            secret_value: Secret value as string
            description: Optional description
        
        Returns:
            Secret ARN
        
        Raises:
            ClientError: If secret creation fails
        """
        async with self.session.client("secretsmanager") as secrets_manager:
            params = {
                "Name": secret_id,
                "SecretString": secret_value
            }
            
            if description:
                params["Description"] = description
            
            response = await secrets_manager.create_secret(**params)
            return response["ARN"]
    
    async def update_secret(self, secret_id: str, secret_value: str) -> str:
        """
        Update an existing secret in AWS Secrets Manager.
        
        Args:
            secret_id: Secret identifier (name or ARN)
            secret_value: New secret value as string
        
        Returns:
            Secret ARN
        
        Raises:
            ClientError: If secret update fails
        """
        async with self.session.client("secretsmanager") as secrets_manager:
            response = await secrets_manager.update_secret(
                SecretId=secret_id,
                SecretString=secret_value
            )
            
            # Invalidate cache for this secret
            self.clear_cache(secret_id)
            
            return response["ARN"]
    
    async def delete_secret(
        self,
        secret_id: str,
        recovery_window_days: int = 30
    ) -> None:
        """
        Delete a secret from AWS Secrets Manager.
        
        Args:
            secret_id: Secret identifier (name or ARN)
            recovery_window_days: Recovery window in days (7-30)
        
        Raises:
            ClientError: If secret deletion fails
        """
        async with self.session.client("secretsmanager") as secrets_manager:
            await secrets_manager.delete_secret(
                SecretId=secret_id,
                RecoveryWindowInDays=recovery_window_days
            )
            
            # Invalidate cache for this secret
            self.clear_cache(secret_id)
