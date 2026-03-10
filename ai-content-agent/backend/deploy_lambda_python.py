#!/usr/bin/env python3
"""
Deploy Lambda Function using Python and boto3 with existing IAM role
"""

import boto3
import json
import zipfile
import io
import os
import time
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_aws_clients():
    """Get AWS clients"""
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    
    return {
        'lambda': session.client('lambda'),
        'sts': session.client('sts')
    }

def get_account_id(sts_client):
    """Get AWS account ID"""
    response = sts_client.get_caller_identity()
    return response['Account']

def create_lambda_package():
    """Create Lambda deployment package"""
    print("📦 Creating Lambda deployment package...")
    
    # Create zip file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write('lambda_handler.py', 'lambda_handler.py')
    
    zip_buffer.seek(0)
    return zip_buffer.read()

def deploy_lambda_function(lambda_client, role_arn):
    """Deploy Lambda function"""
    function_name = 'instagram-post-handler'
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    # Create deployment package
    zip_content = create_lambda_package()
    
    try:
        # Check if function exists
        lambda_client.get_function(FunctionName=function_name)
        
        # Update existing function
        print("🔄 Updating existing Lambda function...")
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        # Update configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Runtime='python3.11',
            Handler='lambda_handler.lambda_handler',
            Role=role_arn,
            Timeout=60,
            MemorySize=256
        )
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Create new function
            print("🆕 Creating new Lambda function...")
            response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.11',
                Role=role_arn,
                Handler='lambda_handler.lambda_handler',
                Code={'ZipFile': zip_content},
                Timeout=60,
                MemorySize=256,
                Description='Handle scheduled Instagram posts'
            )
        else:
            raise
    
    function_arn = response['FunctionArn']
    print(f"✅ Lambda function deployed!")
    print(f"📋 Function ARN: {function_arn}")
    
    return function_arn

def add_eventbridge_permission(lambda_client):
    """Add EventBridge permission to Lambda"""
    function_name = 'instagram-post-handler'
    
    try:
        lambda_client.add_permission(
            FunctionName=function_name,
            StatementId='AllowEventBridgeInvoke',
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com'
        )
        print("✅ EventBridge permission added")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print("✅ EventBridge permission already exists")
        else:
            raise

def update_env_file(lambda_arn):
    """Update .env file with Lambda ARN"""
    print("📝 Updating .env file...")
    
    # Read current .env file
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    # Update or add Lambda ARN
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('AWS_LAMBDA_POST_HANDLER_ARN='):
            lines[i] = f'AWS_LAMBDA_POST_HANDLER_ARN={lambda_arn}\n'
            updated = True
            break
    
    if not updated:
        lines.append(f'AWS_LAMBDA_POST_HANDLER_ARN={lambda_arn}\n')
    
    # Write back to file
    with open('.env', 'w') as f:
        f.writelines(lines)
    
    print("✅ .env file updated")

def main():
    """Main deployment function"""
    print("🚀 Deploying Instagram Post Handler Lambda Function")
    print("=" * 60)
    
    # Use existing IAM role
    role_arn = "arn:aws:iam::054579817571:role/PostPilotRole"
    
    try:
        # Get AWS clients
        clients = get_aws_clients()
        
        # Get account ID
        account_id = get_account_id(clients['sts'])
        print(f"📋 AWS Account ID: {account_id}")
        print(f"📋 Using existing IAM role: {role_arn}")
        
        # Deploy Lambda function
        function_arn = deploy_lambda_function(clients['lambda'], role_arn)
        
        # Add EventBridge permission
        add_eventbridge_permission(clients['lambda'])
        
        # Update .env file
        update_env_file(function_arn)
        
        print("\n" + "=" * 60)
        print("✅ Deployment Complete!")
        print("=" * 60)
        print(f"\n📋 Lambda Function: instagram-post-handler")
        print(f"📋 Function ARN: {function_arn}")
        print(f"📋 IAM Role: {role_arn}")
        print(f"📋 Region: {os.getenv('AWS_REGION', 'us-east-1')}")
        print("\n🎯 Next Steps:")
        print("1. Restart your backend server to pick up the new ARN")
        print("2. Test scheduling posts - EventBridge should now work")
        print("3. Check CloudWatch logs for Lambda execution")
        print("\n🔍 Test Commands:")
        print(f"  aws lambda invoke --function-name instagram-post-handler --payload '{{\"post_id\":\"test\"}}' response.json")
        print(f"  aws logs describe-log-groups --log-group-name-prefix /aws/lambda/instagram-post-handler")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)