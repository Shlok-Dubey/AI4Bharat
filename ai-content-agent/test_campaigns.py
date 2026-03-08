"""
Test script for campaign management endpoints.
Run this after starting the backend server to test campaign CRUD operations.

Usage:
    python test_campaigns.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get JWT token by logging in"""
    print("\n=== Getting Auth Token ===")
    
    # Try to login
    login_data = {
        "email": "john@example.com",
        "password": "SecurePass123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✓ Logged in successfully")
        return token
    
    # If login fails, try signup
    print("Login failed, trying signup...")
    signup_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "SecurePass123!",
        "business_name": "Acme Corp",
        "business_type": "Technology"
    }
    
    response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
    if response.status_code == 201:
        token = response.json()["access_token"]
        print(f"✓ Signed up successfully")
        return token
    
    print("❌ Failed to get auth token")
    return None

def test_create_campaign(token):
    """Test campaign creation"""
    print("\n=== Testing Create Campaign ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    campaign_data = {
        "campaign_name": "Summer Product Launch",
        "product_name": "EcoBottle Pro",
        "product_description": "A sustainable, insulated water bottle made from recycled materials. Keeps drinks cold for 24 hours and hot for 12 hours. Perfect for outdoor enthusiasts and eco-conscious consumers.",
        "campaign_days": 30
    }
    
    response = requests.post(f"{BASE_URL}/campaigns", json=campaign_data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
    
    if response.status_code == 201:
        return response.json()["id"]
    return None

def test_get_campaigns(token):
    """Test getting all campaigns"""
    print("\n=== Testing Get All Campaigns ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/campaigns", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")

def test_get_campaign(token, campaign_id):
    """Test getting a specific campaign"""
    print(f"\n=== Testing Get Campaign {campaign_id} ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/campaigns/{campaign_id}", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")

def test_update_campaign(token, campaign_id):
    """Test updating a campaign"""
    print(f"\n=== Testing Update Campaign {campaign_id} ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    update_data = {
        "campaign_name": "Updated Summer Launch",
        "status": "active"
    }
    
    response = requests.put(f"{BASE_URL}/campaigns/{campaign_id}", json=update_data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")

def test_delete_campaign(token, campaign_id):
    """Test deleting a campaign"""
    print(f"\n=== Testing Delete Campaign {campaign_id} ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.delete(f"{BASE_URL}/campaigns/{campaign_id}", headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 204:
        print("✓ Campaign deleted successfully")

def main():
    print("Starting Campaign Management Tests...")
    print(f"Base URL: {BASE_URL}")
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without auth token")
        return
    
    # Test create campaign
    campaign_id = test_create_campaign(token)
    if not campaign_id:
        print("\n❌ Failed to create campaign")
        return
    
    # Test get all campaigns
    test_get_campaigns(token)
    
    # Test get specific campaign
    test_get_campaign(token, campaign_id)
    
    # Test update campaign
    test_update_campaign(token, campaign_id)
    
    # Test get updated campaign
    test_get_campaign(token, campaign_id)
    
    # Create another campaign for list testing
    campaign_id_2 = test_create_campaign(token)
    
    # Test get all campaigns again
    test_get_campaigns(token)
    
    # Test delete campaign
    if campaign_id_2:
        test_delete_campaign(token, campaign_id_2)
    
    # Verify deletion
    test_get_campaigns(token)
    
    print("\n✅ All campaign tests completed!")
    print("\nAPI Endpoints Tested:")
    print("  POST   /campaigns          - Create campaign")
    print("  GET    /campaigns          - List campaigns")
    print("  GET    /campaigns/{id}     - Get campaign details")
    print("  PUT    /campaigns/{id}     - Update campaign")
    print("  DELETE /campaigns/{id}     - Delete campaign")

if __name__ == "__main__":
    main()
