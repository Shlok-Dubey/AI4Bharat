"""
Seed Historical Data for Testing

This script creates fake historical post data to test the live analytics-based scheduling.
Run this once to populate the database with sample historical performance data.
"""

from database_sqlite import get_db
from models.content import ScheduledPost, PostAnalytics, GeneratedContent
from models.campaign import Campaign
from models.user import User
from datetime import datetime, timedelta
import random
import uuid

def seed_historical_data():
    """Create sample historical posts with analytics"""
    
    db = next(get_db())
    
    print("=" * 60)
    print("SEEDING HISTORICAL DATA")
    print("=" * 60)
    
    # Get or create a test user
    user = db.query(User).first()
    if not user:
        print("❌ No users found. Please create a user first.")
        return
    
    print(f"✅ Using user: {user.email}")
    
    # Get or create a test campaign
    campaign = db.query(Campaign).filter(Campaign.user_id == user.id).first()
    if not campaign:
        campaign = Campaign(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Historical Test Campaign",
            product_name="Test Product",
            product_description="Test product for historical data",
            campaign_settings={"campaign_days": 30}
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
    
    print(f"✅ Using campaign: {campaign.name}")
    
    # Create historical posts over last 30 days
    num_posts = 20
    print(f"\n📊 Creating {num_posts} historical posts...")
    
    # Define engagement patterns by time of day
    time_engagement = {
        "06:00": 0.5,  # Low engagement
        "07:00": 0.7,
        "08:00": 1.0,
        "09:00": 1.5,  # Morning peak
        "10:00": 1.3,
        "11:00": 1.2,
        "12:00": 1.8,  # Lunch peak
        "13:00": 1.6,
        "14:00": 1.4,  # Afternoon
        "15:00": 1.3,
        "16:00": 1.2,
        "17:00": 1.5,
        "18:00": 2.0,  # Evening peak
        "19:00": 2.2,  # Best time
        "20:00": 2.1,
        "21:00": 1.8,
        "22:00": 1.2,
        "23:00": 0.8,
    }
    
    times = list(time_engagement.keys())
    
    for i in range(num_posts):
        # Random date in last 30 days
        days_ago = random.randint(1, 30)
        published_date = datetime.utcnow() - timedelta(days=days_ago)
        
        # Random time
        time_str = random.choice(times)
        hour, minute = map(int, time_str.split(':'))
        published_date = published_date.replace(hour=hour, minute=minute, second=0)
        
        # Create content
        content = GeneratedContent(
            id=uuid.uuid4(),
            campaign_id=campaign.id,
            platform="instagram",
            content_type=random.choice(["post", "reel"]),
            content_text=f"Historical test post {i+1}",
            hashtags="#test #historical",
            status="approved"
        )
        db.add(content)
        db.flush()
        
        # Create scheduled post
        scheduled_post = ScheduledPost(
            id=uuid.uuid4(),
            content_id=content.id,
            scheduled_for=published_date,
            status="published",
            platform_post_id=f"test_media_{uuid.uuid4().hex[:12]}",
            published_at=published_date
        )
        db.add(scheduled_post)
        db.flush()
        
        # Create analytics with engagement based on time
        base_engagement = time_engagement[time_str]
        
        # Add some randomness
        engagement_multiplier = base_engagement * random.uniform(0.8, 1.2)
        
        # Generate metrics
        views = random.randint(500, 2000)
        likes = int(views * 0.05 * engagement_multiplier)
        comments = int(views * 0.01 * engagement_multiplier)
        shares = int(views * 0.005 * engagement_multiplier)
        saves = int(views * 0.02 * engagement_multiplier)
        
        analytics = PostAnalytics(
            id=uuid.uuid4(),
            post_id=scheduled_post.id,
            views=views,
            likes=likes,
            comments=comments,
            shares=shares,
            saves=saves,
            reach=int(views * 0.9),
            impressions=int(views * 1.1),
            engagement_rate=round((likes + comments + shares) / views * 100, 2),
            fetched_at=published_date + timedelta(hours=24)
        )
        db.add(analytics)
        
        print(f"  ✅ Post {i+1}: {time_str} - {likes} likes, {comments} comments ({analytics.engagement_rate}% engagement)")
    
    db.commit()
    
    print("\n" + "=" * 60)
    print("✅ HISTORICAL DATA SEEDED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\nCreated {num_posts} historical posts with analytics")
    print("\nBest performing times based on seeded data:")
    print("  🌟 19:00 (Evening peak)")
    print("  🌟 20:00 (Evening)")
    print("  🌟 18:00 (Evening start)")
    print("  🌟 12:00 (Lunch peak)")
    print("  🌟 09:00 (Morning peak)")
    print("\nNow when you schedule posts, the AI will use this data!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        seed_historical_data()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
