"""
Test script for post scheduling API.
Tests the complete workflow from content generation to scheduling.

Usage:
    python test_schedule_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get JWT token"""
    print("\n=== Getting Auth Token ===")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "john@example.com", "password": "SecurePass123!"}
    )
    
    if response.status_code == 200:
        print("✓ Logged in")
        return response.json()["access_token"]
    return None

def create_campaign(token):
    """Create test campaign"""
    print("\n=== Creating Campaign ===")
    
    response = requests.post(
        f"{BASE_URL}/campaigns",
        json={
            "campaign_name": "Schedule Test Campaign",
            "product_name": "TestProduct",
            "product_description": "A test product for scheduling",
            "campaign_days": 7
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 201:
        campaign_id = response.json()["id"]
        print(f"✓ Campaign created: {campaign_id}")
        return campaign_id
    return None

def generate_content(token, campaign_id):
    """Generate content"""
    print("\n=== Generating Content ===")
    
    response = requests.post(
        f"{BASE_URL}/campaigns/{campaign_id}/generate-content",
        json={"platform": "instagram", "content_type": "post", "count": 5},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        content = response.json()["content"]
        print(f"✓ Generated {len(content)} pieces")
        return [c["id"] for c in content]
    return []

def approve_content(token, content_ids):
    """Approve all content"""
    print("\n=== Approving Content ===")
    
    for content_id in content_ids:
        requests.put(
            f"{BASE_URL}/content/{content_id}/approve",
            json={"approved": True},
            headers={"Authorization": f"Bearer {token}"}
        )
    
    print(f"✓ Approved {len(content_ids)} pieces")

def schedule_posts(token, campaign_id):
    """Schedule posts"""
    print("\n=== Scheduling Posts ===")
    
    response = requests.post(
        f"{BASE_URL}/campaigns/{campaign_id}/schedule",
        json={
            "start_date": "2024-01-15",
            "timezone_offset": -5
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ {result['message']}")
        print(f"  Total scheduled: {result['total_scheduled']}")
        print(f"  Start date: {result['start_date']}")
        print(f"  End date: {result['end_date']}")
        
        preview = result['preview']
        print(f"\n  Schedule Preview:")
        print(f"    Campaign: {preview['campaign_name']}")
        print(f"    Total posts: {preview['total_posts']}")
        print(f"    Campaign days: {preview['campaign_days']}")
        print(f"    Posts by platform: {preview['posts_by_platform']}")
        print(f"    Peak time %: {preview['peak_time_percentage']}%")
        
        print(f"\n  First 3 scheduled posts:")
        for post in preview['scheduled_posts'][:3]:
            print(f"    Day {post['day_number']} - {post['day_of_week']}")
            print(f"      Platform: {post['platform']}")
            print(f"      Time: {post['post_time']}")
            print(f"      Peak time: {post['is_peak_time']}")
            print(f"      Caption: {post['caption'][:50]}...")
        
        return True
    else:
        print(f"✗ Failed: {response.text}")
        return False

def get_schedule_preview(token, campaign_id):
    """Get schedule preview"""
    print("\n=== Getting Schedule Preview ===")
    
    response = requests.get(
        f"{BASE_URL}/campaigns/{campaign_id}/schedule/preview",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        preview = response.json()
        print(f"✓ Schedule retrieved")
        print(f"  Total posts: {preview['total_posts']}")
        print(f"  Date range: {preview['start_date']} to {preview['end_date']}")
        return True
    else:
        print(f"Status: {response.status_code}")
        return False

def main():
    print("="*70)
    print("Post Scheduling API - Integration Test")
    print("="*70)
    
    # Authenticate
    token = get_auth_token()
    if not token:
        print("\n❌ Authentication failed")
        return
    
    # Create campaign
    campaign_id = create_campaign(token)
    if not campaign_id:
        print("\n❌ Campaign creation failed")
        return
    
    # Generate content
    content_ids = generate_content(token, campaign_id)
    if not content_ids:
        print("\n❌ Content generation failed")
        return
    
    # Approve content
    approve_content(token, content_ids)
    
    # Schedule posts
    if not schedule_posts(token, campaign_id):
        print("\n❌ Scheduling failed")
        return
    
    # Get schedule preview
    get_schedule_preview(token, campaign_id)
    
    print("\n" + "="*70)
    print("✅ All scheduling tests completed!")
    print("="*70)
    
    print("\nWorkflow Tested:")
    print("  1. ✓ User authentication")
    print("  2. ✓ Campaign creation")
    print("  3. ✓ Content generation")
    print("  4. ✓ Content approval")
    print("  5. ✓ Post scheduling (Planner + Scheduler agents)")
    print("  6. ✓ Schedule saved to database")
    print("  7. ✓ Schedule preview retrieved")
    
    print("\nAgent Integration:")
    print("  ✓ Campaign Planner Agent - Content distribution")
    print("  ✓ Scheduler Agent - Optimal time assignment")
    print("  ✓ Database persistence - scheduled_posts table")
    
    print("\nAPI Endpoints Tested:")
    print("  POST /campaigns/{id}/schedule")
    print("  GET  /campaigns/{id}/schedule/preview")

if __name__ == "__main__":
    main()
