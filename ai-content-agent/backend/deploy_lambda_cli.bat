@echo off
REM Deploy Lambda Function for Instagram Post Handler
REM This script creates IAM role, deploys Lambda, and configures EventBridge permissions

echo 🚀 Deploying Instagram Post Handler Lambda Function
echo ==================================================

REM Configuration
set FUNCTION_NAME=instagram-post-handler
set ROLE_NAME=instagram-post-handler-role
set POLICY_NAME=instagram-post-handler-policy
set REGION=us-east-1

REM Get AWS account ID
for /f %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i
echo 📋 AWS Account ID: %ACCOUNT_ID%

REM Step 1: Create IAM policy
echo 📝 Creating IAM policy...
set POLICY_ARN=arn:aws:iam::%ACCOUNT_ID%:policy/%POLICY_NAME%

REM Check if policy exists
aws iam get-policy --policy-arn %POLICY_ARN% >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Policy already exists: %POLICY_ARN%
) else (
    aws iam create-policy --policy-name %POLICY_NAME% --policy-document file://lambda_iam_policy.json --description "Policy for Instagram post handler Lambda function"
    echo ✅ Policy created: %POLICY_ARN%
)

REM Step 2: Create IAM role
echo 📝 Creating IAM role...
set ROLE_ARN=arn:aws:iam::%ACCOUNT_ID%:role/%ROLE_NAME%

REM Trust policy for Lambda
echo {> trust-policy.json
echo     "Version": "2012-10-17",>> trust-policy.json
echo     "Statement": [>> trust-policy.json
echo         {>> trust-policy.json
echo             "Effect": "Allow",>> trust-policy.json
echo             "Principal": {>> trust-policy.json
echo                 "Service": "lambda.amazonaws.com">> trust-policy.json
echo             },>> trust-policy.json
echo             "Action": "sts:AssumeRole">> trust-policy.json
echo         }>> trust-policy.json
echo     ]>> trust-policy.json
echo }>> trust-policy.json

REM Check if role exists
aws iam get-role --role-name %ROLE_NAME% >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Role already exists: %ROLE_ARN%
) else (
    aws iam create-role --role-name %ROLE_NAME% --assume-role-policy-document file://trust-policy.json --description "Role for Instagram post handler Lambda function"
    echo ✅ Role created: %ROLE_ARN%
)

REM Step 3: Attach policies to role
echo 📎 Attaching policies to role...

REM Attach basic execution role
aws iam attach-role-policy --role-name %ROLE_NAME% --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

REM Attach custom policy
aws iam attach-role-policy --role-name %ROLE_NAME% --policy-arn %POLICY_ARN%

echo ✅ Policies attached

REM Step 4: Wait for role propagation
echo ⏳ Waiting for IAM role propagation...
timeout /t 10 /nobreak >nul

REM Step 5: Create Lambda deployment package
echo 📦 Creating Lambda deployment package...
powershell -Command "Compress-Archive -Path lambda_handler.py -DestinationPath lambda-deployment.zip -Force"
echo ✅ Package created: lambda-deployment.zip

REM Step 6: Deploy Lambda function
echo 🚀 Deploying Lambda function...

REM Check if function exists
aws lambda get-function --function-name %FUNCTION_NAME% >nul 2>&1
if %errorlevel% equ 0 (
    echo 🔄 Updating existing Lambda function...
    aws lambda update-function-code --function-name %FUNCTION_NAME% --zip-file fileb://lambda-deployment.zip
    
    REM Update configuration
    aws lambda update-function-configuration --function-name %FUNCTION_NAME% --runtime python3.11 --handler lambda_handler.lambda_handler --timeout 60 --memory-size 256 --environment Variables="{AWS_REGION=%REGION%}"
) else (
    echo 🆕 Creating new Lambda function...
    aws lambda create-function --function-name %FUNCTION_NAME% --runtime python3.11 --role %ROLE_ARN% --handler lambda_handler.lambda_handler --zip-file fileb://lambda-deployment.zip --timeout 60 --memory-size 256 --environment Variables="{AWS_REGION=%REGION%}" --description "Handle scheduled Instagram posts"
)

REM Step 7: Get Lambda ARN
for /f %%i in ('aws lambda get-function --function-name %FUNCTION_NAME% --query Configuration.FunctionArn --output text') do set LAMBDA_ARN=%%i
echo ✅ Lambda function deployed!
echo 📋 Function ARN: %LAMBDA_ARN%

REM Step 8: Add EventBridge permission
echo 🔐 Adding EventBridge permission...
aws lambda add-permission --function-name %FUNCTION_NAME% --statement-id AllowEventBridgeInvoke --action lambda:InvokeFunction --principal events.amazonaws.com --region %REGION% >nul 2>&1
echo ✅ EventBridge permission configured

REM Step 9: Update .env file
echo 📝 Updating .env file...
powershell -Command "(Get-Content .env) -replace 'AWS_LAMBDA_POST_HANDLER_ARN=.*', 'AWS_LAMBDA_POST_HANDLER_ARN=%LAMBDA_ARN%' | Set-Content .env"

REM If the line doesn't exist, add it
findstr /C:"AWS_LAMBDA_POST_HANDLER_ARN=" .env >nul
if %errorlevel% neq 0 (
    echo AWS_LAMBDA_POST_HANDLER_ARN=%LAMBDA_ARN%>> .env
)
echo ✅ .env file updated

REM Cleanup
del trust-policy.json lambda-deployment.zip 2>nul

echo.
echo ==================================================
echo ✅ Deployment Complete!
echo ==================================================
echo.
echo 📋 Lambda Function: %FUNCTION_NAME%
echo 📋 Function ARN: %LAMBDA_ARN%
echo 📋 IAM Role: %ROLE_NAME%
echo 📋 Region: %REGION%
echo.
echo 🎯 Next Steps:
echo 1. Restart your backend server to pick up the new ARN
echo 2. Test scheduling posts - EventBridge should now work
echo 3. Check CloudWatch logs for Lambda execution
echo.
echo 🔍 Useful Commands:
echo   aws logs describe-log-groups --log-group-name-prefix /aws/lambda/%FUNCTION_NAME%
echo   aws lambda invoke --function-name %FUNCTION_NAME% --payload "{\"post_id\":\"test\"}" response.json
echo.

pause