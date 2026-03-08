"""
Database initialization script.
Run this script to create all tables in the database.

Usage:
    python init_db.py

For AWS DynamoDB deployment:
- Replace with DynamoDB table creation script
- Use boto3 to create tables with proper indexes
- Define provisioned throughput or on-demand billing
"""

from database_sqlite import engine
from base import Base
from models import (
    User,
    OAuthAccount,
    Campaign,
    CampaignAsset,
    GeneratedContent,
    ScheduledPost,
    PostAnalytics
)

def init_database():
    """
    Create all tables in the database.
    
    For DynamoDB: Create tables using boto3 with proper GSI definitions
    """
    print("Creating database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully!")
        
        # Print created tables
        print("\nCreated tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
            
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        raise

if __name__ == "__main__":
    init_database()
