"""
Test script for content generation endpoints.
Run this after starting the backend server to test content management.

Usage:
    python test_content.py
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

def create_test_campaign(token):
    """Create a test campaign"""
    print("\n=== Creating Test Campaign ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    campaign_data = {
        "campaign_name": "Content Generation Test",
        "product_name": "SmartWatch Pro",
        "product_description": "A cutting-edge smartwatch with health tracking, GPS, and 7-day battery life. Perfect for fitness enthusiasts and busy professionals.",
        "campaign_days": 30
    }
    
    response = requests.post(f"{BASE_URL}/campaigns", json=campaign_data, headers=headers)
    
    if response.status_code == 201:
        campaign_id = response.json()["id"]
        print(f"✓ Campaign created: {campaign_id}")
        return campaign_id
    
    print("❌ Failed to create campaign")
    return None

def test_generate_content(token, campaign_id):
    """Test content generation"""
    print(f"\n=== Testing Generate Content ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Generate Instagram posts
    generate_data = {
        "platform": "instagram",
        "content_type": "post",
        "count": 3
    }
    
    response = requests.post(
        f"{BASE_URL}/campaigns/{campaign_id}/generate-content",
        json=generate_data,
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
    
    if response.status_code == 200:
        content_list = response.json()["content"]
        return content_list[0]["id"] if content_list else None
    return None

def test_get_campaign_content(token, campaign_id):
    """Test getting campaign content"""
    print(f"\n=== Testing Get Campaign Content ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/campaigns/{campaign_id}/content",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")

def test_get_content_detail(token, content_id):
    """Test getting content detail"""
    print(f"\n=== Testing Get Content Detail ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/content/{content_id}",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")

def test_approve_content(token, content_id, approved=True):
    """Test approving content"""
    print(f"\n=== Testing {'Approve' if approved else 'Reject'} Content ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    approve_data = {
        "approved": approved,
        "feedback": "Needs more emojis" if not approved else None
    }
    
    response = requests.put(
        f"{BASE_URL}/content/{content_id}/approve",
        json=approve_data,
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")

def test_filter_content(token, campaign_id):
    """Test filtering content"""
    print(f"\n=== Testing Filter Content by Status ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/campaigns/{campaign_id}/content?status_filter=approved",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Approved Content Count: {response.json()['total']}")

def main():
    print("Starting Content Generation Tests...")
    print(f"Base URL: {BASE_URL}")
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without auth token")
        return
    
    # Create test campaign
    campaign_id = create_test_campaign(token)
    if not campaign_id:
        print("\n❌ Cannot proceed without campaign")
        return
    
    # Test generate content (Instagram posts)
    content_id = test_generate_content(token, campaign_id)
    
    # Test get campaign content
    test_get_campaign_content(token, campaign_id)
    
    # Test get content detail
    if content_id:
        test_get_content_detail(token, content_id)
        
        # Test approve content
        test_approve_content(token, content_id, approved=True)
        
        # Get content detail again to see updated status
        test_get_content_detail(token, content_id)
    
    # Generate more content for different platforms
    print("\n=== Generating Content for Multiple Platforms ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Facebook posts
    requests.post(
        f"{BASE_URL}/campaigns/{campaign_id}/generate-content",
        json={"platform": "facebook", "content_type": "post", "count": 2},
        headers=headers
    )
    
    # Instagram reels
    requests.post(
        f"{BASE_URL}/campaigns/{campaign_id}/generate-content",
        json={"platform": "instagram", "content_type": "reel", "count": 2},
        headers=headers
    )
    
    # Get all content with statistics
    test_get_campaign_content(token, campaign_id)
    
    # Test filtering
    test_filter_content(token, campaign_id)
    
    print("\n✅ All content generation tests completed!")
    print("\nAPI Endpoints Tested:")
    print("  POST   /campaigns/{id}/generate-content  - Generate AI content")
    print("  GET    /campaigns/{id}/content           - List campaign content")
    print("  GET    /content/{id}                     - Get content details")
    print("  PUT    /content/{id}/approve             - Approve/reject content")
    print("\nNote: Currently using placeholder content.")
    print("AI integration will be added in future updates.")

if __name__ == "__main__":
    main()
