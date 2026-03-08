"""
SQLite Database Configuration (Alternative to PostgreSQL)

This is a temporary solution for local development without PostgreSQL.
For production, use PostgreSQL.

To use SQLite instead of PostgreSQL:
1. Update .env: DATABASE_URL=sqlite:///./ai_content_agent.db
2. Replace 'import database' with 'import database_sqlite as database' in main.py
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./ai_content_agent.db"

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
