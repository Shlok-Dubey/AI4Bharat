"""
Database session management utilities.

For AWS DynamoDB deployment:
- This module can be removed or replaced with DynamoDB session management
- DynamoDB uses direct client/resource connections instead of sessions
"""

from contextlib import contextmanager
from sqlalchemy.orm import Session
from database_sqlite import SessionLocal

@contextmanager
def get_db_context():
    """
    Context manager for database sessions.
    Use when you need a database session outside of FastAPI dependencies.
    
    Example:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def create_session() -> Session:
    """
    Create a new database session.
    Remember to close the session when done.
    
    For DynamoDB: Replace with DynamoDB client/resource creation
    """
    return SessionLocal()
