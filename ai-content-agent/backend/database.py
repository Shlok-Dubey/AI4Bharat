"""
Database connection module for PostgreSQL using SQLAlchemy.

For AWS deployment with DynamoDB:
- Replace this module with a DynamoDB client configuration
- Use boto3 for DynamoDB connections
- Implement PynamoDB models instead of SQLAlchemy models
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/ai_content_agent"
)

# Create SQLAlchemy engine
# For production, consider adding pool settings:
# pool_size=20, max_overflow=0, pool_pre_ping=True
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    future=True
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

def get_db():
    """
    Dependency function to get database session.
    Use this in FastAPI route dependencies.
    
    For DynamoDB: Replace with DynamoDB resource/client initialization
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
