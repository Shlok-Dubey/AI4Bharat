"""
Deploy Lambda Function for Scheduled Posts

This script packages and deploys the Lambda function to AWS.
"""

import boto3
import zipfile
import os
import io
from botocore.exceptions import ClientError


def create_lambda_package():
    """Create a deployment package with Lambda handler and dependencies"""
    print("📦 Creating Lambda deployment package...")
    
    # Create in-memory zip file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add lambda handler
        zip_file.write('lambda_handler.py', 'lambda_handler.py')
        print("  ✅ Added lambda_handler.py")
    
    zip_buffer.seek(0)
    return zip_buffer.read()


def create_or_update_lambda(function_name: str, role_arn: str):
    """Create or update Lambda function"""
    lambda_client = boto3.client(
        'lambda',
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    
    # Create deployment package
    zip_content = create_lambda_package()
    
    try:
        # Try to get existing function
        lambda_client.get_function(FunctionName=function_name)
        
        # Function exists, update it
        print(f"🔄 Updating existing Lambda function: {function_name}")
        
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"✅ Lambda function updated!")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Function doesn't exist, create it
            print(f"🆕 Creating new Lambda function: {function_name}")
            
            response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.11',
                Role=role_arn,
                Handler='lambda_handler.lambda_handler',
                Code={'ZipFile': zip_content},
                Timeout=60,
                MemorySize=256,
                Environment={
                    'Variables': {
                        'AWS_REGION': os.getenv('AWS_REGION', 'us-east-1')
                    }
                },
                Description='Handle scheduled Instagram posts'
            )
            
            print(f"✅ Lambda function created!")
        else:
            raise
    
    function_arn = response['FunctionArn']
    print(f"📋 Function ARN: {function_arn}")
    
    return function_arn


def add_eventbridge_permission(function_name: str):
    """Add permission for EventBridge to invoke Lambda"""
    lambda_client = boto3.client(
        'lambda',
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    
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


def deploy():
    """Main deployment function"""
    print("🚀 Deploying Lambda function for scheduled posts")
    print("=" * 60)
    
    # Configuration
    function_name = 'instagram-post-handler'
    role_arn = os.getenv('AWS_LAMBDA_ROLE_ARN')
    
    if not role_arn:
        print("❌ AWS_LAMBDA_ROLE_ARN environment variable not set")
        print("\nCreate an IAM role with these policies:")
        print("  - AWSLambdaBasicExecutionRole")
        print("  - DynamoDB read/write access")
        print("  - EventBridge access")
        return False
    
    try:
        # Deploy Lambda
        function_arn = create_or_update_lambda(function_name, role_arn)
        
        # Add EventBridge permission
        add_eventbridge_permission(function_name)
        
        print("\n" + "=" * 60)
        print("✅ Deployment complete!")
        print("\nNext steps:")
        print(f"1. Set AWS_LAMBDA_POST_HANDLER_ARN={function_arn}")
        print("2. Test the Lambda function")
        print("3. Schedule posts via API")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = deploy()
    exit(0 if success else 1)
