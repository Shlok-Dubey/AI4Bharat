# PostPilot AI - AWS Lambda Deployment Guide

This guide covers deploying the PostPilot AI platform to AWS using AWS SAM (Serverless Application Model).

## Prerequisites

- AWS CLI configured with appropriate credentials
- AWS SAM CLI installed
- Python 3.11+
- Docker (for building Lambda layers)

## Deployment Architecture

PostPilot AI uses a serverless architecture on AWS:

- **Compute**: AWS Lambda functions (Python 3.11)
- **API**: Amazon API Gateway
- **Database**: Amazon DynamoDB
- **Storage**: Amazon S3
- **Queue**: Amazon SQS with Dead Letter Queue
- **AI Services**: Amazon Bedrock (Claude 3.5 Sonnet), Amazon Rekognition
- **Scheduling**: Amazon EventBridge
- **Monitoring**: Amazon CloudWatch Logs, Metrics, and Alarms
- **Notifications**: Amazon SNS

## Deployment Steps

### 1. Build Lambda Layer

Lambda layers contain shared dependencies used by all Lambda functions.

```bash
cd backend/layers

# Build the layer
./build.sh

# This creates lambda-layer.zip
```

### 2. Package Lambda Functions

Package each Lambda function with its code and shared modules.

```bash
cd backend/deploy

# Package all Lambda functions
./package.sh

# This creates deployment packages in dist/
```

### 3. Configure Environment

Choose your environment configuration:

```bash
# Development
export ENV=dev

# Staging
export ENV=staging

# Production
export ENV=prod
```

### 4. Deploy with SAM

```bash
cd backend

# Build the SAM application
sam build

# Deploy to AWS (first time - guided)
sam deploy --guided

# Subsequent deployments
sam deploy
```

During guided deployment, you'll be prompted for:
- Stack name (e.g., postpilot-prod)
- AWS Region (e.g., us-east-1)
- Parameter values (if any)
- Confirmation before deployment

### 5. Upload Lambda Layer

After deployment, upload the Lambda layer:

```bash
# Upload layer to AWS
aws lambda publish-layer-version \
  --layer-name postpilot-dependencies \
  --description "Shared dependencies for PostPilot AI" \
  --zip-file fileb://layers/lambda-layer.zip \
  --compatible-runtimes python3.11

# Note the LayerVersionArn from the output
```

### 6. Update Lambda Functions to Use Layer

Update each Lambda function to use the layer:

```bash
# Get the layer ARN from previous step
LAYER_ARN="arn:aws:lambda:us-east-1:123456789012:layer:postpilot-dependencies:1"

# Update each function
for func in postpilot-agent-orchestrator postpilot-business-profiling postpilot-campaign-strategy postpilot-content-generation postpilot-scheduling-intelligence postpilot-publishing-worker postpilot-analytics-collector postpilot-performance-learning; do
  aws lambda update-function-configuration \
    --function-name $func \
    --layers $LAYER_ARN
done
```

### 7. Configure Secrets

Store sensitive data in AWS Secrets Manager:

```bash
# Instagram OAuth credentials
aws secretsmanager create-secret \
  --name postpilot/instagram-credentials \
  --secret-string '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET"}'

# JWT secret key
aws secretsmanager create-secret \
  --name postpilot/jwt-secret \
  --secret-string '{"secret_key":"YOUR_JWT_SECRET"}'

# Encryption key
aws secretsmanager create-secret \
  --name postpilot/encryption-key \
  --secret-string '{"key":"YOUR_ENCRYPTION_KEY"}'
```

### 8. Configure SNS Notifications

Subscribe to alarm notifications:

```bash
# Get the SNS topic ARN from CloudFormation outputs
TOPIC_ARN=$(aws cloudformation describe-stacks \
  --stack-name postpilot-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`AlarmNotificationTopicArn`].OutputValue' \
  --output text)

# Subscribe your email
aws sns subscribe \
  --topic-arn $TOPIC_ARN \
  --protocol email \
  --notification-endpoint ops@postpilot.ai

# Confirm the subscription via email
```

### 9. Verify Deployment

Check that all resources are created:

```bash
# List Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `postpilot`)].FunctionName'

# List DynamoDB tables
aws dynamodb list-tables --query 'TableNames[?starts_with(@, `postpilot`)]'

# Check S3 bucket
aws s3 ls | grep postpilot

# Check SQS queues
aws sqs list-queues --query 'QueueUrls[?contains(@, `postpilot`)]'
```

### 10. Test the Deployment

```bash
# Invoke a Lambda function
aws lambda invoke \
  --function-name postpilot-agent-orchestrator \
  --payload '{"test": true}' \
  response.json

# Check the response
cat response.json
```

## Environment-Specific Configurations

### Development
- Uses dev environment configuration
- Lower resource limits
- More verbose logging
- Shorter retention periods

### Staging
- Mirrors production configuration
- Used for pre-production testing
- Separate AWS account recommended

### Production
- Full resource allocation
- Production-grade monitoring
- Longer retention periods
- High availability configuration

## Monitoring and Alarms

CloudWatch alarms are automatically configured for:

1. **Lambda Error Rate**: Alerts when error rate > 5%
2. **Queue Depth**: Alerts when SQS queue > 1000 messages
3. **Worker Duration**: Alerts when Lambda approaches timeout
4. **Publish Failure Rate**: Alerts when publish failures > 10%
5. **Dead Letter Queue**: Alerts when messages enter DLQ

All alarms send notifications to the SNS topic.

## Rollback

If deployment fails or issues arise:

```bash
# Rollback to previous version
sam deploy --no-confirm-changeset --stack-name postpilot-prod

# Or delete the stack entirely
aws cloudformation delete-stack --stack-name postpilot-prod
```

## Cost Optimization

- Use on-demand billing for DynamoDB (included in template)
- Set appropriate Lambda memory sizes (configured per function)
- Use reserved concurrency to limit costs
- Monitor CloudWatch costs (30-day retention)
- Use S3 lifecycle policies for old media

## Security Best Practices

1. **IAM Roles**: Each Lambda has least-privilege IAM role
2. **Secrets**: All sensitive data in Secrets Manager
3. **Encryption**: Data encrypted at rest and in transit
4. **VPC**: Optional VPC configuration for private resources
5. **API Gateway**: Use API keys and throttling in production

## Troubleshooting

### Lambda Function Errors

```bash
# View logs
aws logs tail /aws/lambda/postpilot-agent-orchestrator --follow

# Check recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/postpilot-agent-orchestrator \
  --filter-pattern "ERROR"
```

### DynamoDB Issues

```bash
# Check table status
aws dynamodb describe-table --table-name postpilot-campaigns

# Check for throttling
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name UserErrors \
  --dimensions Name=TableName,Value=postpilot-campaigns \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

### SQS Queue Issues

```bash
# Check queue attributes
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/postpilot-publishing-queue \
  --attribute-names All

# Check dead letter queue
aws sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/postpilot-dlq
```

## Updating the Deployment

To update Lambda code or infrastructure:

```bash
# Make your changes to code or template.yaml

# Rebuild
sam build

# Deploy changes
sam deploy

# SAM will show a changeset - review and confirm
```

## CI/CD Integration

For automated deployments, integrate with CI/CD:

```yaml
# Example GitHub Actions workflow
name: Deploy to AWS
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: aws-actions/setup-sam@v2
      - run: sam build
      - run: sam deploy --no-confirm-changeset
```

## Additional Resources

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [CloudWatch Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)
