"""
Test script for OAuth endpoints.
This script demonstrates the OAuth flow for Meta (Instagram).

Usage:
    python test_oauth.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get JWT token by logging in"""
    print("\n=== Getting Auth Token ===")
    
    # First, try to login
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

def test_oauth_login(token):
    """Test OAuth login endpoint"""
    print("\n=== Testing OAuth Login ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # This will redirect to Meta OAuth page
    # In local testing with mock credentials, it will still work
    response = requests.get(f"{BASE_URL}/auth/meta/login", headers=headers, allow_redirects=False)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 307:
        redirect_url = response.headers.get("location")
        print(f"✓ Redirecting to: {redirect_url[:100]}...")
        return True
    else:
        print(f"Response: {response.text}")
        return False

def test_get_oauth_accounts(token):
    """Test getting OAuth accounts"""
    print("\n=== Testing Get OAuth Accounts ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/auth/meta/accounts", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def main():
    print("Starting OAuth Tests...")
    print(f"Base URL: {BASE_URL}")
    print("\nNote: This test demonstrates the OAuth flow.")
    print("In local testing mode, it uses mock credentials.")
    print("For production, set real META_APP_ID and META_APP_SECRET in .env\n")
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without auth token")
        return
    
    # Test OAuth login endpoint
    test_oauth_login(token)
    
    # Test getting OAuth accounts
    test_get_oauth_accounts(token)
    
    print("\n" + "="*60)
    print("OAuth Flow Information:")
    print("="*60)
    print("1. User visits /auth/meta/login with JWT token")
    print("2. System redirects to Meta OAuth page")
    print("3. User authorizes app on Meta")
    print("4. Meta redirects to /auth/meta/callback with code")
    print("5. System exchanges code for access token")
    print("6. System stores token in oauth_accounts table")
    print("7. User is redirected to frontend success page")
    print("="*60)
    
    print("\n✅ OAuth tests completed!")
    print("\nTo complete the full OAuth flow:")
    print("1. Set up a Meta App at https://developers.facebook.com/apps/")
    print("2. Update META_APP_ID and META_APP_SECRET in .env")
    print("3. Visit http://localhost:8000/auth/meta/login in browser")
    print("4. Complete OAuth authorization on Meta")

if __name__ == "__main__":
    main()
