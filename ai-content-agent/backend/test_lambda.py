#!/usr/bin/env python3
"""
Test Lambda function
"""

import boto3
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_lambda():
    """Test the Lambda function"""
    print("🧪 Testing Lambda function...")
    
    # Create Lambda client
    lambda_client = boto3.client(
        'lambda',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    # Test payload
    test_payload = {
        "post_id": "test-post-id"
    }
    
    try:
        print(f"📤 Invoking Lambda with payload: {test_payload}")
        
        response = lambda_client.invoke(
            FunctionName='instagram-post-handler',
            Payload=json.dumps(test_payload)
        )
        
        # Read response
        response_payload = response['Payload'].read().decode('utf-8')
        status_code = response['StatusCode']
        
        print(f"✅ Lambda invocation successful!")
        print(f"📋 Status Code: {status_code}")
        print(f"📋 Response: {response_payload}")
        
        # Parse response
        try:
            result = json.loads(response_payload)
            if result.get('statusCode') == 400:
                print("✅ Lambda is working correctly (expected error for test post)")
            else:
                print(f"📋 Lambda result: {result}")
        except json.JSONDecodeError:
            print(f"📋 Raw response: {response_payload}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lambda test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_lambda()
    exit(0 if success else 1)