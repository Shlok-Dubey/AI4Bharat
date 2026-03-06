# PostPilot AI - Deployment Configuration

This directory contains all deployment-related configurations for the PostPilot AI platform.

## Files Overview

### Lambda Packaging
- **`package.sh`**: Script to package all Lambda functions into deployment zips
- **`lambda-config.yaml`**: Configuration documentation for Lambda function settings (memory, timeout, concurrency)

### Environment Configurations
- **`env.dev.yaml`**: Development environment configuration
- **`env.staging.yaml`**: Staging environment configuration  
- **`env.prod.yaml`**: Production environment configuration

### Deployment Guide
- **`DEPLOYMENT_GUIDE.md`**: Complete guide for deploying to AWS

## Quick Reference

### Build Lambda Layer
```bash
cd ../layers
./build.sh
```

### Package Lambda Functions
```bash
./package.sh
```

### Deploy to AWS
```bash
cd ..
sam build
sam deploy --guided  # First time
sam deploy           # Subsequent deployments
```

### Environment Selection

Set the environment before deployment:
```bash
export ENV=dev      # Development
export ENV=staging  # Staging
export ENV=prod     # Production
```

## Lambda Functions

The platform includes these Lambda functions:

1. **Agent Orchestrator** - Coordinates multi-agent workflow
2. **Business Profiling** - AI agent for business identity reasoning
3. **Campaign Strategy** - AI agent for campaign strategy decisions
4. **Content Generation** - AI agent for caption and hashtag generation
5. **Scheduling Intelligence** - AI agent for optimal timing
6. **Publishing Worker** - Publishes campaigns to Instagram (SQS trigger)
7. **Analytics Collector** - Fetches Instagram insights (EventBridge trigger)
8. **Performance Learning** - AI agent for learning from analytics

## Resource Configuration

### Memory Allocation
- Orchestrator: 1024 MB (orchestrates multiple agents)
- AI Agents: 512 MB (Bedrock calls)
- Scheduling: 256 MB (lightweight)
- Publishing Worker: 512 MB (Instagram API)
- Analytics: 512 MB (batch processing)

### Timeout Settings
- Orchestrator: 60s (multiple agent invocations)
- AI Agents: 30s (Bedrock response time)
- Publishing Worker: 120s (Instagram API can be slow)
- Analytics Collector: 300s (processes multiple campaigns)

### Reserved Concurrency
- Orchestrator: 50 (cost control)
- Publishing Worker: 10 (Instagram rate limits)
- Analytics Collector: 1 (single instance)
- Other functions: No limit

## Monitoring

CloudWatch alarms are configured for:
- Lambda error rate > 5%
- SQS queue depth > 1000 messages
- Lambda duration approaching timeout
- Publish failure rate > 10%
- Messages in dead letter queue

All alarms send notifications to SNS topic.

## Next Steps

1. Review [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions
2. Configure AWS credentials
3. Build and deploy using SAM
4. Configure Secrets Manager with sensitive data
5. Subscribe to SNS alarm notifications
6. Test the deployment

## Support

For issues or questions:
- Check CloudWatch Logs for Lambda execution logs
- Review CloudWatch Alarms for system health
- Check SQS Dead Letter Queue for failed jobs
- Review [../README.dev.md](../README.dev.md) for local development
