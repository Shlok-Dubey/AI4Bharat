"""
Pytest configuration and fixtures for testing.
"""

import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set test environment variables before importing app
os.environ['JWT_SECRET'] = 'test-secret-key-for-testing-only'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['DYNAMODB_ENDPOINT'] = 'http://localhost:8000'  # DynamoDB Local

from dev_api.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing FastAPI endpoints.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user_data():
    """
    Provide test user data for registration/login tests.
    """
    return {
        "email": "test@example.com",
        "password": "TestPass123"
    }
