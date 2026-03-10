#!/bin/bash

# Deploy Lambda Function for Instagram Post Handler
# This script creates IAM role, deploys Lambda, and configures EventBridge permissions

set -e

echo "🚀 Deploying Instagram Post Handler Lambda Function"
echo "=================================================="

# Configuration
FUNCTION_NAME="instagram-post-handler"
ROLE_NAME="instagram-post-handler-role"
POLICY_NAME="instagram-post-handler-policy"
REGION="us-east-1"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account ID: $ACCOUNT_ID"

# Step 1: Create IAM policy
echo "📝 Creating IAM policy..."
POLICY_ARN="arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME"

# Check if policy exists
if aws iam get-policy --policy-arn $POLICY_ARN >/dev/null 2>&1; then
    echo "✅ Policy already exists: $POLICY_ARN"
else
    aws iam create-policy \
        --policy-name $POLICY_NAME \
        --policy-document file://lambda_iam_policy.json \
        --description "Policy for Instagram post handler Lambda function"
    echo "✅ Policy created: $POLICY_ARN"
fi

# Step 2: Create IAM role
echo "📝 Creating IAM role..."
ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"

# Trust policy for Lambda
cat > trust-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Check if role exists
if aws iam get-role --role-name $ROLE_NAME >/dev/null 2>&1; then
    echo "✅ Role already exists: $ROLE_ARN"
else
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file://trust-policy.json \
        --description "Role for Instagram post handler Lambda function"
    echo "✅ Role created: $ROLE_ARN"
fi

# Step 3: Attach policies to role
echo "📎 Attaching policies to role..."

# Attach basic execution role
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Attach custom policy
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn $POLICY_ARN

echo "✅ Policies attached"

# Step 4: Wait for role propagation
echo "⏳ Waiting for IAM role propagation..."
sleep 10

# Step 5: Create Lambda deployment package
echo "📦 Creating Lambda deployment package..."
zip -j lambda-deployment.zip lambda_handler.py
echo "✅ Package created: lambda-deployment.zip"

# Step 6: Deploy Lambda function
echo "🚀 Deploying Lambda function..."

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME >/dev/null 2>&1; then
    echo "🔄 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://lambda-deployment.zip
    
    # Update configuration
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --handler lambda_handler.lambda_handler \
        --timeout 60 \
        --memory-size 256 \
        --environment Variables="{AWS_REGION=$REGION}"
else
    echo "🆕 Creating new Lambda function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler lambda_handler.lambda_handler \
        --zip-file fileb://lambda-deployment.zip \
        --timeout 60 \
        --memory-size 256 \
        --environment Variables="{AWS_REGION=$REGION}" \
        --description "Handle scheduled Instagram posts"
fi

# Step 7: Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function --function-name $FUNCTION_NAME --query Configuration.FunctionArn --output text)
echo "✅ Lambda function deployed!"
echo "📋 Function ARN: $LAMBDA_ARN"

# Step 8: Add EventBridge permission
echo "🔐 Adding EventBridge permission..."
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id AllowEventBridgeInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --region $REGION \
    >/dev/null 2>&1 || echo "✅ Permission already exists"

echo "✅ EventBridge permission configured"

# Step 9: Update .env file
echo "📝 Updating .env file..."
if grep -q "AWS_LAMBDA_POST_HANDLER_ARN=" .env; then
    # Replace existing line
    sed -i "s|AWS_LAMBDA_POST_HANDLER_ARN=.*|AWS_LAMBDA_POST_HANDLER_ARN=$LAMBDA_ARN|" .env
else
    # Add new line
    echo "AWS_LAMBDA_POST_HANDLER_ARN=$LAMBDA_ARN" >> .env
fi
echo "✅ .env file updated"

# Cleanup
rm -f trust-policy.json lambda-deployment.zip

echo ""
echo "=================================================="
echo "✅ Deployment Complete!"
echo "=================================================="
echo ""
echo "📋 Lambda Function: $FUNCTION_NAME"
echo "📋 Function ARN: $LAMBDA_ARN"
echo "📋 IAM Role: $ROLE_NAME"
echo "📋 Region: $REGION"
echo ""
echo "🎯 Next Steps:"
echo "1. Restart your backend server to pick up the new ARN"
echo "2. Test scheduling posts - EventBridge should now work"
echo "3. Check CloudWatch logs for Lambda execution"
echo ""
echo "🔍 Useful Commands:"
echo "  aws logs describe-log-groups --log-group-name-prefix /aws/lambda/$FUNCTION_NAME"
echo "  aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"post_id\":\"test\"}' response.json"
echo ""