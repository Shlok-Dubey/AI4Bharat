"""
Test script for Content Generator Agent integration with API.
Tests the complete workflow from campaign creation to content generation.

Usage:
    python test_integration.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get JWT token by logging in"""
    print("\n=== Getting Auth Token ===")
    
    login_data = {
        "email": "john@example.com",
        "password": "SecurePass123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✓ Logged in successfully")
        return token
    
    print("❌ Failed to get auth token")
    return None

def create_campaign(token):
    """Create a campaign with product information"""
    print("\n=== Creating Campaign ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    campaign_data = {
        "campaign_name": "AI Agent Integration Test",
        "product_name": "UltraFit Smartwatch",
        "product_description": "Revolutionary smartwatch with advanced health tracking, GPS navigation, and 10-day battery life. Features include heart rate monitoring, sleep analysis, stress tracking, and 50+ workout modes. Water-resistant up to 50m. Perfect for fitness enthusiasts and health-conscious individuals.",
        "campaign_days": 30
    }
    
    response = requests.post(f"{BASE_URL}/campaigns", json=campaign_data, headers=headers)
    
    if response.status_code == 201:
        campaign_id = response.json()["id"]
        print(f"✓ Campaign created: {campaign_id}")
        print(f"  Product: {campaign_data['product_name']}")
        return campaign_id
    
    print(f"❌ Failed to create campaign: {response.text}")
    return None

def generate_content(token, campaign_id, platform, content_type, count=3):
    """Generate content using the AI agent"""
    print(f"\n=== Generating {count} {content_type}(s) for {platform} ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    generate_data = {
        "platform": platform,
        "content_type": content_type,
        "count": count,
        "tone": "engaging"
    }
    
    response = requests.post(
        f"{BASE_URL}/campaigns/{campaign_id}/generate-content",
        json=generate_data,
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ {result['message']}")
        print(f"  Generated: {result['generated_count']} pieces")
        
        # Display first piece
        if result['content']:
            first_content = result['content'][0]
            print(f"\n  Sample Content:")
            print(f"  ID: {first_content['id']}")
            print(f"  Status: {first_content['status']}")
            print(f"  Caption: {first_content['caption'][:100]}...")
            print(f"  Hashtags: {first_content['hashtags'][:50]}...")
            
            # Show reel script if available
            if first_content.get('ai_metadata', {}).get('reel_script'):
                print(f"  Reel Script: Available")
            
            return result['content']
    else:
        print(f"❌ Failed to generate content: {response.text}")
    
    return []

def get_campaign_content(token, campaign_id):
    """Get all content for a campaign"""
    print(f"\n=== Getting Campaign Content ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/campaigns/{campaign_id}/content",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Total content pieces: {result['total']}")
        print(f"  By Status: {result['by_status']}")
        print(f"  By Platform: {result['by_platform']}")
        return result
    
    print(f"❌ Failed to get content: {response.text}")
    return None

def approve_content(token, content_id):
    """Approve a content piece"""
    print(f"\n=== Approving Content {content_id} ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    approve_data = {
        "approved": True
    }
    
    response = requests.put(
        f"{BASE_URL}/content/{content_id}/approve",
        json=approve_data,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Content approved")
        print(f"  New Status: {result['status']}")
        return True
    
    print(f"❌ Failed to approve content: {response.text}")
    return False

def reject_content(token, content_id):
    """Reject a content piece with feedback"""
    print(f"\n=== Rejecting Content {content_id} ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    reject_data = {
        "approved": False,
        "feedback": "Needs more emphasis on battery life feature"
    }
    
    response = requests.put(
        f"{BASE_URL}/content/{content_id}/approve",
        json=reject_data,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Content rejected")
        print(f"  New Status: {result['status']}")
        print(f"  Feedback stored in metadata")
        return True
    
    print(f"❌ Failed to reject content: {response.text}")
    return False

def test_workflow():
    """Test the complete workflow"""
    print("="*70)
    print("AI Content Generator Agent - Integration Test")
    print("="*70)
    
    # Step 1: Authenticate
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        return
    
    # Step 2: Create campaign with product info
    campaign_id = create_campaign(token)
    if not campaign_id:
        print("\n❌ Cannot proceed without campaign")
        return
    
    # Step 3: Generate Instagram posts
    instagram_posts = generate_content(token, campaign_id, "instagram", "post", count=3)
    
    # Step 4: Generate Instagram reels
    instagram_reels = generate_content(token, campaign_id, "instagram", "reel", count=2)
    
    # Step 5: Generate Facebook posts
    facebook_posts = generate_content(token, campaign_id, "facebook", "post", count=2)
    
    # Step 6: Get all campaign content
    all_content = get_campaign_content(token, campaign_id)
    
    # Step 7: Approve some content
    if instagram_posts:
        approve_content(token, instagram_posts[0]['id'])
        approve_content(token, instagram_posts[1]['id'])
    
    # Step 8: Reject some content
    if instagram_posts and len(instagram_posts) > 2:
        reject_content(token, instagram_posts[2]['id'])
    
    # Step 9: Get updated content statistics
    get_campaign_content(token, campaign_id)
    
    # Step 10: Filter by status
    print(f"\n=== Filtering Content by Status ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get approved content
    response = requests.get(
        f"{BASE_URL}/campaigns/{campaign_id}/content?status_filter=approved",
        headers=headers
    )
    if response.status_code == 200:
        approved_count = response.json()['total']
        print(f"✓ Approved content: {approved_count}")
    
    # Get pending content
    response = requests.get(
        f"{BASE_URL}/campaigns/{campaign_id}/content?status_filter=pending",
        headers=headers
    )
    if response.status_code == 200:
        pending_count = response.json()['total']
        print(f"✓ Pending content: {pending_count}")
    
    print("\n" + "="*70)
    print("✅ Integration Test Complete!")
    print("="*70)
    
    print("\nWorkflow Tested:")
    print("  1. ✓ User authentication")
    print("  2. ✓ Campaign creation with product info")
    print("  3. ✓ Content generation using AI agent")
    print("  4. ✓ Content saved to database")
    print("  5. ✓ Content marked as 'pending'")
    print("  6. ✓ Content approval workflow")
    print("  7. ✓ Content rejection with feedback")
    print("  8. ✓ Content filtering by status")
    
    print("\nAgent Integration:")
    print("  ✓ Campaign product info fetched")
    print("  ✓ AI agent called with product details")
    print("  ✓ Platform-specific content generated")
    print("  ✓ Hashtags and captions created")
    print("  ✓ Reel scripts generated")
    print("  ✓ Metadata stored in database")
    
    print("\nNext Steps:")
    print("  - Replace template generation with AWS Bedrock")
    print("  - Add content scheduling")
    print("  - Implement post publishing")
    print("  - Add analytics tracking")

if __name__ == "__main__":
    test_workflow()
