"""
Test AWS connection and Bedrock access
"""
import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

print("Testing AWS Connection...")
print("=" * 50)

# Get credentials from .env
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION', 'us-east-1')

print(f"AWS Region: {aws_region}")
print(f"Access Key: {aws_access_key[:10]}..." if aws_access_key else "Access Key: Not found")
print()

# Test 1: Check AWS credentials
print("Test 1: Checking AWS credentials...")
try:
    sts_client = boto3.client(
        'sts',
        region_name=aws_region,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    identity = sts_client.get_caller_identity()
    print(f"✅ AWS credentials valid!")
    print(f"   Account: {identity['Account']}")
    print(f"   User ARN: {identity['Arn']}")
except ClientError as e:
    print(f"❌ AWS credentials invalid: {e}")
    exit(1)

print()

# Test 2: Check Bedrock access
print("Test 2: Checking Bedrock access...")
try:
    bedrock_client = boto3.client(
        'bedrock',
        region_name=aws_region,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    
    # List available models
    response = bedrock_client.list_foundation_models()
    models = response.get('modelSummaries', [])
    
    print(f"✅ Bedrock access granted!")
    print(f"   Available models: {len(models)}")
    
    # Check for Claude models
    claude_models = [m for m in models if 'claude' in m['modelId'].lower()]
    if claude_models:
        print(f"   Claude models available: {len(claude_models)}")
        for model in claude_models[:3]:
            print(f"      - {model['modelId']}")
    else:
        print("   ⚠️  No Claude models found. You may need to request model access.")
        
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'AccessDeniedException':
        print(f"❌ Bedrock access denied. You need to:")
        print(f"   1. Go to AWS Console → Bedrock")
        print(f"   2. Click 'Model access'")
        print(f"   3. Request access to Claude models")
    else:
        print(f"❌ Bedrock error: {e}")

print()

# Test 3: Check S3 access
print("Test 3: Checking S3 access...")
try:
    s3_client = boto3.client(
        's3',
        region_name=aws_region,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    
    # List buckets
    response = s3_client.list_buckets()
    buckets = response.get('Buckets', [])
    
    print(f"✅ S3 access granted!")
    print(f"   Existing buckets: {len(buckets)}")
    
    if buckets:
        for bucket in buckets[:5]:
            print(f"      - {bucket['Name']}")
    else:
        print("   No buckets found. You can create one for asset storage.")
        
except ClientError as e:
    print(f"❌ S3 error: {e}")

print()
print("=" * 50)
print("AWS Connection Test Complete!")
