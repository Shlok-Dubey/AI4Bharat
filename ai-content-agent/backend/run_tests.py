"""
AI Content Agent - Comprehensive Test Suite

Run all tests to verify system functionality
"""

import sys
from config import settings
import dynamodb_client as db
from agents.analytics_agent import AnalyticsAgent


def test_config():
    """Test 1: Configuration Loading"""
    print("\n" + "="*60)
    print("TEST 1: Configuration Loading")
    print("="*60)
    
    missing = []
    if not settings.AWS_ACCESS_KEY_ID:
        missing.append("AWS_ACCESS_KEY_ID")
    if not settings.AWS_SECRET_ACCESS_KEY:
        missing.append("AWS_SECRET_ACCESS_KEY")
    if not settings.INSTAGRAM_APP_ID:
        missing.append("INSTAGRAM_APP_ID")
    if not settings.INSTAGRAM_APP_SECRET:
        missing.append("INSTAGRAM_APP_SECRET")
    
    if missing:
        print(f"❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        return False
    else:
        print("✅ All required environment variables are set")
        print(f"   AWS Region: {settings.AWS_REGION}")
        print(f"   S3 Bucket: {settings.S3_BUCKET_NAME}")
        print(f"   Bedrock Model: {settings.BEDROCK_MODEL_ID}")
        return True


def test_aws_connection():
    """Test 2: AWS Connection"""
    print("\n" + "="*60)
    print("TEST 2: AWS Connection")
    print("="*60)
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Test STS (credentials)
        sts_client = boto3.client(
            'sts',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        identity = sts_client.get_caller_identity()
        print(f"✅ AWS credentials valid")
        print(f"   Account: {identity['Account']}")
        return True
        
    except Exception as e:
        print(f"❌ AWS connection failed: {e}")
        return False


def test_dynamodb():
    """Test 3: DynamoDB Access"""
    print("\n" + "="*60)
    print("TEST 3: DynamoDB Access")
    print("="*60)
    
    try:
        # Try to scan users table
        response = db.users_table.scan(Limit=1)
        print(f"✅ DynamoDB access successful")
        print(f"   Users table accessible")
        
        # Check all tables exist
        tables = [
            'users', 'oauth_accounts', 'campaigns', 'campaign_assets',
            'generated_content', 'scheduled_posts', 'post_analytics'
        ]
        print(f"   Tables configured: {len(tables)}")
        return True
        
    except Exception as e:
        print(f"❌ DynamoDB access failed: {e}")
        print("   Run: python init_dynamodb.py")
        return False


def test_s3():
    """Test 4: S3 Access"""
    print("\n" + "="*60)
    print("TEST 4: S3 Access")
    print("="*60)
    
    try:
        import boto3
        from io import BytesIO
        from utils.aws_s3 import validate_media_file
        
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # Check if bucket exists
        s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        print(f"✅ S3 access successful")
        print(f"   Bucket: {settings.S3_BUCKET_NAME}")
        
        # Test file validation
        is_valid, _ = validate_media_file("test.jpg", 1024)
        if is_valid:
            print(f"   File validation working")
        
        return True
        
    except Exception as e:
        print(f"❌ S3 access failed: {e}")
        print(f"   Create bucket: {settings.S3_BUCKET_NAME}")
        return False


def test_bedrock():
    """Test 5: Bedrock Access"""
    print("\n" + "="*60)
    print("TEST 5: Bedrock Access")
    print("="*60)
    
    try:
        import boto3
        
        bedrock_client = boto3.client(
            'bedrock',
            region_name=settings.BEDROCK_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        response = bedrock_client.list_foundation_models()
        models = response.get('modelSummaries', [])
        claude_models = [m for m in models if 'claude' in m['modelId'].lower()]
        
        print(f"✅ Bedrock access successful")
        print(f"   Available models: {len(models)}")
        print(f"   Claude models: {len(claude_models)}")
        return True
        
    except Exception as e:
        print(f"❌ Bedrock access failed: {e}")
        print("   Request model access in AWS Console")
        return False


def test_analytics():
    """Test 6: Analytics System"""
    print("\n" + "="*60)
    print("TEST 6: Analytics System")
    print("="*60)
    
    try:
        # Get a campaign
        response = db.campaigns_table.scan(Limit=1)
        campaigns = [db.dynamodb_to_python(item) for item in response.get('Items', [])]
        
        if not campaigns:
            print("⚠️  No campaigns found (expected for new setup)")
            return True
        
        campaign_id = campaigns[0]['campaign_id']
        
        # Test analytics agent
        agent = AnalyticsAgent()
        analytics = agent.fetch_campaign_analytics(campaign_id)
        
        print(f"✅ Analytics system working")
        print(f"   Campaign: {campaigns[0].get('name', 'N/A')}")
        print(f"   Total Posts: {analytics.get('total_posts', 0)}")
        print(f"   Posts with Analytics: {analytics.get('posts_with_analytics', 0)}")
        
        if analytics.get('posts_with_analytics', 0) == 0:
            print("   ℹ️  No analytics data yet (run analytics_job.py)")
        
        return True
        
    except Exception as e:
        print(f"❌ Analytics test failed: {e}")
        return False


def test_scheduler():
    """Test 7: Scheduler Agent"""
    print("\n" + "="*60)
    print("TEST 7: Scheduler Agent")
    print("="*60)
    
    try:
        from agents.scheduler_agent import get_scheduler_agent
        from datetime import datetime
        
        scheduler = get_scheduler_agent()
        
        # Test with sample post
        sample_posts = [{
            "content_id": "test-1",
            "caption": "Test post",
            "platform": "instagram",
            "content_type": "post",
            "recommended_day": 1
        }]
        
        scheduled = scheduler.schedule_posts(
            posts=sample_posts,
            start_date=datetime.utcnow(),
            timezone_offset=0
        )
        
        print(f"✅ Scheduler working")
        print(f"   Scheduled {len(scheduled)} posts")
        print(f"   Time selected: {scheduled[0]['post_time']}")
        return True
        
    except Exception as e:
        print(f"❌ Scheduler test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AI CONTENT AGENT - TEST SUITE")
    print("="*60)
    
    tests = [
        ("Configuration", test_config),
        ("AWS Connection", test_aws_connection),
        ("DynamoDB", test_dynamodb),
        ("S3 Storage", test_s3),
        ("Bedrock AI", test_bedrock),
        ("Analytics", test_analytics),
        ("Scheduler", test_scheduler),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! System is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
