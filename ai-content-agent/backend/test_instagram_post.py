"""
Test Instagram Posting

This script tests the Instagram posting functionality directly.
"""

import os
from dotenv import load_dotenv
from agents.posting_agent import get_posting_agent

# Load environment variables
load_dotenv()

def test_instagram_posting():
    """Test Instagram posting with a sample post"""
    
    print("=" * 60)
    print("INSTAGRAM POSTING TEST")
    print("=" * 60)
    
    # Get posting agent
    posting_agent = get_posting_agent()
    
    # Test data - YOU NEED TO UPDATE THESE
    print("\n⚠️  IMPORTANT: Update these values before testing:")
    print("-" * 60)
    
    # Get from your Instagram OAuth connection
    access_token = input("Enter your Instagram access token: ").strip()
    if not access_token:
        print("❌ Access token is required!")
        return
    
    instagram_account_id = input("Enter your Instagram Business Account ID: ").strip()
    if not instagram_account_id:
        print("❌ Instagram account ID is required!")
        return
    
    # Test post data
    caption = "🌟 Testing AI Content Agent! This is an automated post from our new platform. #AI #SocialMedia #Testing"
    
    # Image URL - MUST be publicly accessible
    image_url = input("Enter publicly accessible image URL (or press Enter for default): ").strip()
    if not image_url:
        # Default test image (publicly accessible)
        image_url = "https://picsum.photos/1080/1080"
    
    hashtags = "#automation #tech #innovation"
    
    print("\n" + "=" * 60)
    print("TEST CONFIGURATION")
    print("=" * 60)
    print(f"Instagram Account ID: {instagram_account_id}")
    print(f"Caption: {caption[:50]}...")
    print(f"Image URL: {image_url}")
    print(f"Hashtags: {hashtags}")
    
    confirm = input("\n⚠️  This will post to your REAL Instagram account. Continue? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ Test cancelled.")
        return
    
    print("\n" + "=" * 60)
    print("POSTING TO INSTAGRAM...")
    print("=" * 60)
    
    # Attempt to post
    success, media_id, error = posting_agent.post_to_instagram(
        access_token=access_token,
        instagram_account_id=instagram_account_id,
        caption=caption,
        image_url=image_url,
        hashtags=hashtags
    )
    
    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    
    if success:
        print("✅ SUCCESS!")
        print(f"Media ID: {media_id}")
        print("\n🎉 Post published to Instagram!")
        print("Check your Instagram Business Account to see the post.")
    else:
        print("❌ FAILED!")
        print(f"Error: {error}")
        print("\nCommon issues:")
        print("1. Access token expired - Reconnect Instagram in the app")
        print("2. Image URL not publicly accessible - Use a public URL")
        print("3. Rate limit exceeded - Wait before posting again")
        print("4. Invalid account ID - Check your Instagram Business Account ID")
    
    print("=" * 60)


def get_instagram_credentials():
    """Helper to get Instagram credentials from database"""
    print("\n💡 TIP: To get your credentials:")
    print("1. Log in to the app")
    print("2. Connect Instagram Business Account")
    print("3. Check the database for oauth_accounts table")
    print("4. Or use the app's Analytics page to see your account ID")
    print()


if __name__ == "__main__":
    print("\n🚀 Instagram Posting Test Script")
    print("=" * 60)
    
    get_instagram_credentials()
    
    try:
        test_instagram_posting()
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
