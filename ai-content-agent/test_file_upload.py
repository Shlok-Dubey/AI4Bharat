"""
Test script for file upload endpoints.
Run this after starting the backend server to test asset uploads.

Usage:
    python test_file_upload.py
"""

import requests
import json
import io
from PIL import Image

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
        "campaign_name": "File Upload Test Campaign",
        "product_name": "Test Product",
        "product_description": "This is a test product for file upload testing",
        "campaign_days": 30
    }
    
    response = requests.post(f"{BASE_URL}/campaigns", json=campaign_data, headers=headers)
    
    if response.status_code == 201:
        campaign_id = response.json()["id"]
        print(f"✓ Campaign created: {campaign_id}")
        return campaign_id
    
    print("❌ Failed to create campaign")
    return None

def create_test_image():
    """Create a test image in memory"""
    img = Image.new('RGB', (800, 600), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

def test_upload_assets(token, campaign_id):
    """Test uploading assets"""
    print(f"\n=== Testing Upload Assets ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Create test image
    test_image = create_test_image()
    
    files = [
        ('files', ('test_image_1.jpg', test_image, 'image/jpeg')),
        ('files', ('test_image_2.jpg', create_test_image(), 'image/jpeg'))
    ]
    
    response = requests.post(
        f"{BASE_URL}/campaigns/{campaign_id}/upload-assets",
        headers=headers,
        files=files
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_get_assets(token, campaign_id):
    """Test getting campaign assets"""
    print(f"\n=== Testing Get Assets ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/campaigns/{campaign_id}/assets",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
    
    if response.status_code == 200:
        assets = response.json()["assets"]
        return assets[0]["id"] if assets else None
    return None

def test_delete_asset(token, campaign_id, asset_id):
    """Test deleting an asset"""
    print(f"\n=== Testing Delete Asset ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.delete(
        f"{BASE_URL}/campaigns/{campaign_id}/assets/{asset_id}",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")

def main():
    print("Starting File Upload Tests...")
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
    
    # Test upload assets
    if not test_upload_assets(token, campaign_id):
        print("\n❌ Asset upload failed")
        return
    
    # Test get assets
    asset_id = test_get_assets(token, campaign_id)
    
    # Test delete asset
    if asset_id:
        test_delete_asset(token, campaign_id, asset_id)
    
    # Get assets again to verify deletion
    test_get_assets(token, campaign_id)
    
    print("\n✅ All file upload tests completed!")
    print("\nAPI Endpoints Tested:")
    print("  POST   /campaigns/{id}/upload-assets  - Upload files")
    print("  GET    /campaigns/{id}/assets         - List assets")
    print("  DELETE /campaigns/{id}/assets/{id}    - Delete asset")
    print("\nFiles are stored in: uploads/campaign_assets/{campaign_id}/")

if __name__ == "__main__":
    main()
