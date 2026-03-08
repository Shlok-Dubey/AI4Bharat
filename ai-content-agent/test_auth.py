"""
Test script for authentication endpoints.
Run this after starting the backend server to test signup and login.

Usage:
    python test_auth.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_signup():
    """Test user signup"""
    print("\n=== Testing Signup ===")
    
    signup_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "SecurePass123!",
        "business_name": "Acme Corp",
        "business_type": "Technology"
    }
    
    response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        return response.json()["access_token"]
    return None

def test_login():
    """Test user login"""
    print("\n=== Testing Login ===")
    
    login_data = {
        "email": "john@example.com",
        "password": "SecurePass123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_protected_route(token):
    """Test protected route with JWT token"""
    print("\n=== Testing Protected Route ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/protected/me", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def main():
    print("Starting Authentication Tests...")
    print(f"Base URL: {BASE_URL}")
    
    # Test signup
    token = test_signup()
    
    # Test login
    if not token:
        token = test_login()
    
    # Test protected route
    if token:
        test_protected_route(token)
    else:
        print("\n❌ Could not obtain token. Tests failed.")
        return
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
