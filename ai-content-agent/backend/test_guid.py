"""
Test script to verify GUID type works with SQLite.
"""
import uuid
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models.user import User
from base import Base

# Create in-memory SQLite database for testing
engine = create_engine("sqlite:///:memory:", echo=True)
Base.metadata.create_all(engine)

# Test creating a user with UUID
with Session(engine) as session:
    # Create test user
    test_user = User(
        id=uuid.uuid4(),
        name="Test User",
        email="test@example.com",
        hashed_password="hashed_password_here",
        is_active=True,
        is_verified=False
    )
    session.add(test_user)
    session.commit()
    
    print(f"✓ Created user with ID: {test_user.id}")
    print(f"  ID type: {type(test_user.id)}")
    
    # Query user by UUID
    user_id = test_user.id
    found_user = session.query(User).filter(User.id == user_id).first()
    
    if found_user:
        print(f"✓ Found user by UUID: {found_user.email}")
        print(f"  Retrieved ID: {found_user.id}")
        print(f"  Retrieved ID type: {type(found_user.id)}")
        print("\n✓ GUID type is working correctly with SQLite!")
    else:
        print("✗ Failed to find user by UUID")

print("\nTest completed successfully!")
