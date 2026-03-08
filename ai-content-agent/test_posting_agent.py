"""
Test script for Posting Agent.
Tests posting logic and status updates.

Usage:
    python test_posting_agent.py
"""

import sys
sys.path.append('backend')

from agents.posting_agent import PostingAgent

def test_instagram_posting():
    """Test Instagram posting"""
    print("\n=== Testing Instagram Posting ===")
    
    agent = PostingAgent()
    
    success, post_id, error = agent.post_to_instagram(
        access_token="test_token",
        instagram_account_id="test_account_123",
        caption="Check out our amazing product! Perfect for your lifestyle.",
        hashtags="#product #lifestyle #innovation"
    )
    
    print(f"Success: {success}")
    print(f"Post ID: {post_id}")
    print(f"Error: {error}")
    
    assert success == True, "Instagram posting should succeed"
    assert post_id is not None, "Should return post ID"
    print("✓ Instagram posting test passed")

def test_facebook_posting():
    """Test Facebook posting"""
    print("\n=== Testing Facebook Posting ===")
    
    agent = PostingAgent()
    
    success, post_id, error = agent.post_to_facebook(
        access_token="test_token",
        page_id="test_page_123",
        message="Exciting announcement about our new product!",
        image_url="https://example.com/image.jpg"
    )
    
    print(f"Success: {success}")
    print(f"Post ID: {post_id}")
    print(f"Error: {error}")
    
    assert success == True, "Facebook posting should succeed"
    print("✓ Facebook posting test passed")

def test_twitter_posting():
    """Test Twitter posting"""
    print("\n=== Testing Twitter Posting ===")
    
    agent = PostingAgent()
    
    success, tweet_id, error = agent.post_to_twitter(
        access_token="test_token",
        access_token_secret="test_secret",
        tweet_text="Quick update on our latest innovation! #tech #innovation"
    )
    
    print(f"Success: {success}")
    print(f"Tweet ID: {tweet_id}")
    print(f"Error: {error}")
    
    assert success == True, "Twitter posting should succeed"
    print("✓ Twitter posting test passed")

def test_linkedin_posting():
    """Test LinkedIn posting"""
    print("\n=== Testing LinkedIn Posting ===")
    
    agent = PostingAgent()
    
    success, post_id, error = agent.post_to_linkedin(
        access_token="test_token",
        person_urn="urn:li:person:123",
        text="Professional insights on our product launch."
    )
    
    print(f"Success: {success}")
    print(f"Post ID: {post_id}")
    print(f"Error: {error}")
    
    assert success == True, "LinkedIn posting should succeed"
    print("✓ LinkedIn posting test passed")

def test_error_handling():
    """Test error handling"""
    print("\n=== Testing Error Handling ===")
    
    agent = PostingAgent()
    
    # Test with missing credentials
    success, post_id, error = agent.post_to_instagram(
        access_token="",
        instagram_account_id="",
        caption="Test"
    )
    
    print(f"Success: {success}")
    print(f"Error: {error}")
    
    assert success == False, "Should fail with missing credentials"
    assert error is not None, "Should return error message"
    print("✓ Error handling test passed")

def main():
    print("="*60)
    print("Posting Agent - Test Suite")
    print("="*60)
    
    # Run tests
    test_instagram_posting()
    test_facebook_posting()
    test_twitter_posting()
    test_linkedin_posting()
    test_error_handling()
    
    print("\n" + "="*60)
    print("✅ All posting agent tests completed!")
    print("="*60)
    
    print("\nAgent Features Tested:")
    print("  ✓ Instagram posting (placeholder)")
    print("  ✓ Facebook posting (placeholder)")
    print("  ✓ Twitter posting (placeholder)")
    print("  ✓ LinkedIn posting (placeholder)")
    print("  ✓ Error handling")
    
    print("\nProduction Integration:")
    print("  • Meta Graph API for Instagram/Facebook")
    print("  • Twitter API v2 for Twitter/X")
    print("  • LinkedIn API for LinkedIn")
    print("  • OAuth token management")
    print("  • Rate limit handling")
    print("  • Retry logic")
    print("  • Status tracking in database")
    
    print("\nMeta Graph API Workflow:")
    print("  1. Create media container")
    print("  2. Check container status")
    print("  3. Publish media container")
    print("  4. Store platform post ID")
    print("  5. Update scheduled_posts table")
    
    print("\nNext Steps:")
    print("  1. Implement Meta Graph API integration")
    print("  2. Add OAuth token refresh")
    print("  3. Implement background job queue")
    print("  4. Add webhook handlers")
    print("  5. Implement retry logic")
    print("  6. Add rate limit tracking")

if __name__ == "__main__":
    main()
