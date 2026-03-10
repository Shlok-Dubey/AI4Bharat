# Lambda Function Setup Guide

Since your AWS user doesn't have IAM permissions, you'll need to create the Lambda function manually through the AWS Console.

## Step 1: Create Lambda Function via AWS Console

1. **Go to AWS Lambda Console**: https://console.aws.amazon.com/lambda/
2. **Click "Create function"**
3. **Choose "Author from scratch"**
4. **Function settings**:
   - **Function name**: `instagram-post-handler`
   - **Runtime**: `Python 3.11`
   - **Architecture**: `x86_64`
   - **Execution role**: Create a new role or use existing role with these permissions:
     - `AWSLambdaBasicExecutionRole`
     - DynamoDB read/write access to your tables
     - EventBridge permissions

## Step 2: Upload Lambda Code

1. **Download the Lambda handler**: Copy `lambda_handler.py` from your backend folder
2. **In Lambda Console**: 
   - Go to "Code" tab
   - Delete the default code
   - Paste the content from `lambda_handler.py`
   - Click "Deploy"

## Step 3: Configure Lambda Settings

1. **Configuration → General configuration**:
   - **Timeout**: 1 minute
   - **Memory**: 256 MB

2. **Configuration → Environment variables**:
   - Add: `AWS_REGION` = `us-east-1`

## Step 4: Add EventBridge Permission

1. **Configuration → Permissions**
2. **Resource-based policy statements**
3. **Add permissions**:
   - **Service**: EventBridge (CloudWatch Events)
   - **Statement ID**: `AllowEventBridgeInvoke`
   - **Principal**: `events.amazonaws.com`
   - **Action**: `lambda:InvokeFunction`

## Step 5: Get Lambda ARN

1. **In Lambda Console**: Copy the Function ARN from the top right
2. **Format**: `arn:aws:lambda:us-east-1:054579817571:function:instagram-post-handler`

## Step 6: Update Backend Configuration

1. **Update `.env` file** with the actual Lambda ARN:
   ```
   AWS_LAMBDA_POST_HANDLER_ARN=arn:aws:lambda:us-east-1:054579817571:function:instagram-post-handler
   ```

2. **Restart your backend server**

## Step 7: Test the Setup

1. **Create a campaign and schedule posts**
2. **Check backend logs** - should show EventBridge rules being created
3. **Check Lambda logs** in CloudWatch when posts are scheduled to publish

## Required IAM Permissions for Lambda Role

If creating a custom role, it needs these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:UpdateItem"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/ai_content_*",
                "arn:aws:dynamodb:*:*:table/ai_content_*/index/*"
            ]
        }
    ]
}
```

## Current Status

✅ **Backend**: Configured with placeholder Lambda ARN
✅ **EventBridge**: Will work once real Lambda ARN is provided
✅ **Manual Publishing**: Already working without Lambda
✅ **Automatic Publishing**: Will work once Lambda is created

## Alternative: Skip Automatic Publishing

If you prefer to keep using manual publishing only:

1. **Remove Lambda ARN** from `.env`:
   ```
   AWS_LAMBDA_POST_HANDLER_ARN=
   ```

2. **Use the "Publish Now" button** in the frontend to manually publish posts

The system works perfectly with manual publishing - automatic publishing via Lambda is optional!