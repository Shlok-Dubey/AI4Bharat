"""
Base class for SQLAlchemy models.

For AWS DynamoDB deployment:
- Replace with PynamoDB base model
- Import from pynamodb.models import Model
"""

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass
