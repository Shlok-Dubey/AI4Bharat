#!/usr/bin/env python3
"""
Test Instagram Business Account connectivity
"""

import requests
import sys
import os
sys.path.append('.')
import dynamodb_client as dynamodb

def test_instagram_account():
    """Test if the Instagram Business Account is accessible"""
    
    # Get OAuth account
    campaign_id = 'b24d3135-795a-42d4-a117-42100273d9ad'
    campaign = dynamodb.get_campaign(campaign_id)
    user_id = campaign.get('user_id')
    
    oauth_account = dynamodb.get_oauth_account_by_provider(user_id, 'meta')
    
    if not oauth_account:
        print("❌ No OAuth account found")
        return False
    
    access_token = oauth_account.get('access_token')
    instagram_account_id = oauth_account.get('provider_account_id')
    
    print(f"🔍 Testing Instagram Business Account: {instagram_account_id}")
    print(f"🔑 Access Token Length: {len(access_token)}")
    
    # Test 1: Check if the Instagram account exists and is accessible
    print("\n📋 Test 1: Check Instagram Business Account")
    url = f"https://graph.facebook.com/v18.0/{instagram_account_id}"
    params = {
        "fields": "id,name",
        "access_token": access_token
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Instagram account accessible!")
            print(f"   ID: {data.get('id')}")
            print(f"   Name: {data.get('name')}")
            print(f"   Username: {data.get('username')}")
            print(f"   Account Type: {data.get('account_type')}")
            print(f"   Media Count: {data.get('media_count')}")
        else:
            print("❌ Instagram account not accessible!")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Instagram account: {e}")
        return False
    
    # Test 2: Check permissions
    print("\n📋 Test 2: Check Token Permissions")
    url = f"https://graph.facebook.com/v18.0/me/permissions"
    params = {"access_token": access_token}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            permissions = response.json().get('data', [])
            print("✅ Token permissions:")
            for perm in permissions:
                status = perm.get('status')
                permission = perm.get('permission')
                print(f"   {permission}: {status}")
        else:
            print(f"❌ Could not check permissions: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking permissions: {e}")
    
    # Test 3: Try to access the media endpoint (without creating)
    print("\n📋 Test 3: Check Media Endpoint Access")
    url = f"https://graph.facebook.com/v18.0/{instagram_account_id}/media"
    params = {
        "limit": 1,
        "access_token": access_token
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Media endpoint accessible!")
            data = response.json()
            media_count = len(data.get('data', []))
            print(f"   Recent media count: {media_count}")
        else:
            print("❌ Media endpoint not accessible!")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking media endpoint: {e}")
    
    # Test 4: Check if this is a Business Account
    print("\n📋 Test 4: Check Account Type via Facebook Page")
    
    # First, get the Facebook Pages associated with this token
    url = "https://graph.facebook.com/v18.0/me/accounts"
    params = {
        "fields": "id,name,instagram_business_account",
        "access_token": access_token
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            pages = data.get('data', [])
            print(f"✅ Found {len(pages)} Facebook Pages")
            
            instagram_business_found = False
            for page in pages:
                page_id = page.get('id')
                page_name = page.get('name')
                instagram_account = page.get('instagram_business_account')
                
                print(f"   Page: {page_name} (ID: {page_id})")
                if instagram_account:
                    ig_id = instagram_account.get('id')
                    print(f"     → Instagram Business Account: {ig_id}")
                    if ig_id == instagram_account_id:
                        print("     ✅ This matches our Instagram account!")
                        instagram_business_found = True
                else:
                    print("     → No Instagram Business Account connected")
            
            if not instagram_business_found:
                print("❌ Instagram account not found as Business Account on any Facebook Page!")
                print("   This is likely the root cause of the publishing issue.")
                print("   The Instagram account needs to be:")
                print("   1. Converted to a Business Account")
                print("   2. Connected to a Facebook Page")
                
        else:
            print(f"❌ Could not check Facebook Pages: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking Facebook Pages: {e}")
    
    # Test 5: Test the actual media creation endpoint (dry run)
    print("\n📋 Test 5: Test Media Creation Endpoint (Dry Run)")
    url = f"https://graph.facebook.com/v18.0/{instagram_account_id}/media"
    
    # Use a test image URL
    test_image_url = "https://via.placeholder.com/1080x1080.jpg"
    
    params = {
        "image_url": test_image_url,
        "caption": "Test post - this will not be published",
        "access_token": access_token
    }
    
    try:
        print(f"   Testing with image URL: {test_image_url}")
        response = requests.post(url, params=params, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Media creation endpoint works!")
            data = response.json()
            container_id = data.get('id')
            print(f"   Container ID: {container_id}")
            print("   Note: This is just a container, not published")
        else:
            print("❌ Media creation failed!")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing media creation: {e}")
    
    return True

if __name__ == "__main__":
    test_instagram_account()