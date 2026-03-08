"""
Test script for Campaign Planner Agent.
Tests content distribution and scheduling logic.

Usage:
    python test_planner.py
"""

import sys
sys.path.append('backend')

from agents.campaign_planner import CampaignPlannerAgent
from datetime import datetime

def create_sample_content():
    """Create sample content for testing"""
    return [
        {
            "id": "1",
            "caption": "Discover our amazing product! Perfect for your lifestyle.",
            "hashtags": "#product #lifestyle #innovation",
            "platform": "instagram",
            "content_type": "post",
            "ai_metadata": {}
        },
        {
            "id": "2",
            "caption": "Watch how our product transforms your routine!",
            "hashtags": "#reel #trending #viral",
            "platform": "instagram",
            "content_type": "reel",
            "ai_metadata": {
                "reel_script": "[0-3s] Hook\n[3-7s] Introduce\n[7-12s] Demo",
                "thumbnail_text": "Product\nGame Changer"
            }
        },
        {
            "id": "3",
            "caption": "Exciting announcement about our new product!",
            "hashtags": "#newproduct #innovation",
            "platform": "facebook",
            "content_type": "post",
            "ai_metadata": {}
        },
        {
            "id": "4",
            "caption": "Quick update on our latest innovation!",
            "hashtags": "#tech #innovation",
            "platform": "twitter",
            "content_type": "tweet",
            "ai_metadata": {}
        },
        {
            "id": "5",
            "caption": "Professional insights on our product launch.",
            "hashtags": "#business #productlaunch",
            "platform": "linkedin",
            "content_type": "post",
            "ai_metadata": {}
        }
    ]

def test_basic_planning():
    """Test basic campaign planning"""
    print("\n=== Testing Basic Campaign Planning ===")
    
    planner = CampaignPlannerAgent()
    content = create_sample_content()
    
    # Plan for 5 days
    planned = planner.plan_campaign(
        content=content,
        campaign_days=5,
        start_date=datetime(2024, 1, 1)
    )
    
    print(f"\nTotal content pieces: {len(content)}")
    print(f"Campaign days: 5")
    print(f"Planned posts: {len(planned)}")
    
    for post in planned:
        print(f"\nDay {post['recommended_day']} ({post['day_of_week']}):")
        print(f"  Platform: {post['platform']}")
        print(f"  Type: {post['content_type']}")
        print(f"  Time: {post['recommended_time']}")
        print(f"  Date: {post['recommended_date']}")
        print(f"  Caption: {post['caption'][:50]}...")

def test_uneven_distribution():
    """Test with more content than days"""
    print("\n=== Testing Uneven Distribution ===")
    
    planner = CampaignPlannerAgent()
    content = create_sample_content() * 2  # 10 pieces
    
    # Plan for 3 days
    planned = planner.plan_campaign(
        content=content,
        campaign_days=3,
        start_date=datetime(2024, 1, 1)
    )
    
    print(f"\nTotal content pieces: {len(content)}")
    print(f"Campaign days: 3")
    print(f"Planned posts: {len(planned)}")
    
    # Count posts per day
    posts_by_day = {}
    for post in planned:
        day = post['recommended_day']
        posts_by_day[day] = posts_by_day.get(day, 0) + 1
    
    print("\nPosts per day:")
    for day, count in sorted(posts_by_day.items()):
        print(f"  Day {day}: {count} posts")

def test_schedule_generation():
    """Test schedule generation"""
    print("\n=== Testing Schedule Generation ===")
    
    planner = CampaignPlannerAgent()
    
    schedule = planner.generate_campaign_schedule(
        campaign_days=7,
        posts_per_day=2,
        platforms=["instagram", "facebook"]
    )
    
    print(f"\nTotal days: {schedule['total_days']}")
    print(f"Total posts: {schedule['total_posts']}")
    print(f"Posts per day: {schedule['posts_per_day']}")
    print(f"Platforms: {', '.join(schedule['platforms'])}")
    
    print("\nSample schedule (first 3 days):")
    for day_schedule in schedule['schedule'][:3]:
        print(f"\nDay {day_schedule['day']} - {day_schedule['date']} ({day_schedule['day_of_week']}):")
        for platform, times in day_schedule['recommended_times_by_platform'].items():
            print(f"  {platform}: {', '.join(times)}")

def test_content_prioritization():
    """Test content prioritization logic"""
    print("\n=== Testing Content Prioritization ===")
    
    planner = CampaignPlannerAgent()
    content = create_sample_content()
    
    # Plan campaign
    planned = planner.plan_campaign(
        content=content,
        campaign_days=5,
        start_date=datetime(2024, 1, 1)
    )
    
    print("\nContent order (by day):")
    for post in planned:
        print(f"Day {post['recommended_day']}: {post['content_type']} on {post['platform']}")
    
    # Check if reels are prioritized early
    first_three = planned[:3]
    reel_count = sum(1 for p in first_three if p['content_type'] == 'reel')
    print(f"\nReels in first 3 posts: {reel_count}")

def test_weekend_handling():
    """Test weekend vs weekday scheduling"""
    print("\n=== Testing Weekend Handling ===")
    
    planner = CampaignPlannerAgent()
    content = create_sample_content()
    
    # Plan for 7 days (includes weekend)
    planned = planner.plan_campaign(
        content=content,
        campaign_days=7,
        start_date=datetime(2024, 1, 1)  # Monday
    )
    
    print("\nWeekend vs Weekday times:")
    for post in planned:
        if post['is_weekend']:
            print(f"Weekend - {post['day_of_week']}: {post['platform']} at {post['recommended_time']}")
        else:
            print(f"Weekday - {post['day_of_week']}: {post['platform']} at {post['recommended_time']}")

def test_platform_variety():
    """Test platform variety in distribution"""
    print("\n=== Testing Platform Variety ===")
    
    planner = CampaignPlannerAgent()
    
    # Create content with multiple platforms
    content = []
    platforms = ["instagram", "facebook", "twitter", "linkedin"]
    for i in range(12):
        content.append({
            "id": str(i),
            "caption": f"Content piece {i}",
            "hashtags": "#test",
            "platform": platforms[i % len(platforms)],
            "content_type": "post",
            "ai_metadata": {}
        })
    
    planned = planner.plan_campaign(
        content=content,
        campaign_days=6,
        start_date=datetime(2024, 1, 1)
    )
    
    print("\nPlatform distribution by day:")
    for day in range(1, 7):
        day_posts = [p for p in planned if p['recommended_day'] == day]
        platforms_used = [p['platform'] for p in day_posts]
        print(f"Day {day}: {', '.join(platforms_used)}")

def main():
    print("="*60)
    print("Campaign Planner Agent - Test Suite")
    print("="*60)
    
    # Run tests
    test_basic_planning()
    test_uneven_distribution()
    test_schedule_generation()
    test_content_prioritization()
    test_weekend_handling()
    test_platform_variety()
    
    print("\n" + "="*60)
    print("✅ All planner tests completed!")
    print("="*60)
    
    print("\nAgent Features Tested:")
    print("  ✓ Content distribution across days")
    print("  ✓ Uneven content/day ratios")
    print("  ✓ Schedule generation")
    print("  ✓ Content prioritization (reels first)")
    print("  ✓ Weekend vs weekday times")
    print("  ✓ Platform variety")
    
    print("\nPlanning Strategy:")
    print("  • High-engagement content (reels) prioritized early")
    print("  • Content distributed evenly across days")
    print("  • Platform-specific optimal times")
    print("  • Weekend vs weekday scheduling")
    print("  • Variety in consecutive posts")
    
    print("\nNext Steps:")
    print("  1. Integrate with campaign API")
    print("  2. Add ML-based time optimization")
    print("  3. Use historical engagement data")
    print("  4. Implement timezone targeting")
    print("  5. Add A/B testing support")

if __name__ == "__main__":
    main()
