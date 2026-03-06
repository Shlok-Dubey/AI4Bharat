# PostPilot AI - Local Development Guide

This guide explains how to set up and run the PostPilot AI backend locally for development and testing.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- AWS CLI (for LocalStack interaction)
- Node.js 18+ (for frontend)

## Quick Start

### 1. Start Local AWS Services

```bash
# Make the script executable
chmod +x scripts/run-local-dev.sh

# Run the setup script
./scripts/run-local-dev.sh
```

This script will:
- Start DynamoDB Local on port 8000
- Start LocalStack (S3, SQS) on port 4566
- Start DynamoDB Admin UI on port 8001
- Create all required DynamoDB tables
- Create S3 bucket and SQS queue

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and set local development values
# Key settings for local dev:
# - DYNAMODB_ENDPOINT=http://localhost:8000
# - S3_ENDPOINT=http://localhost:4566
# - SQS_ENDPOINT=http://localhost:4566
```

### 4. Run the FastAPI Development Server

```bash
# From the backend directory
uvicorn dev_api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health/liveness

## Local Services

### DynamoDB Local
- **Endpoint**: http://localhost:8000
- **Admin UI**: http://localhost:8001
- **Purpose**: Local DynamoDB for testing

### LocalStack
- **Endpoint**: http://localhost:4566
- **Services**: S3, SQS, Secrets Manager
- **Purpose**: Mock AWS services locally

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth_integration.py

# Run with verbose output
pytest -v
```

## Project Structure

```
backend/
├── dev_api/              # FastAPI app for local development
│   ├── main.py          # FastAPI application entry point
│   └── routes/          # API route handlers
├── lambdas/             # Lambda function handlers
│   ├── orchestrator/    # Agent orchestrator
│   ├── agents/          # AI agent functions
│   └── workers/         # Background workers
├── shared/              # Shared code across Lambdas
│   ├── models/          # Domain models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic services
│   └── utils/           # Utility functions
├── repositories/        # Data access layer
├── tests/               # Test suite
├── scripts/             # Development scripts
├── deploy/              # Deployment configurations
└── docker-compose.yml   # Local services
```

## Development Workflow

### 1. Local Development (FastAPI)

For rapid development and testing, use the FastAPI dev server:

```bash
uvicorn dev_api.main:app --reload
```

This allows you to:
- Test API endpoints quickly
- Use hot reload for code changes
- Debug with breakpoints
- Test with local DynamoDB

### 2. Lambda Testing (SAM Local)

To test Lambda functions locally:

```bash
# Build Lambda functions
sam build

# Invoke a specific Lambda function
sam local invoke AgentOrchestratorFunction --event events/test-event.json

# Start API Gateway locally
sam local start-api
```

### 3. Integration Testing

Run integration tests against local services:

```bash
# Ensure local services are running
docker-compose up -d

# Run integration tests
pytest tests/ -m integration
```

## Common Tasks

### Reset Local Database

```bash
# Stop containers
docker-compose down

# Remove volumes
docker volume rm backend_dynamodb-data backend_localstack-data

# Restart and recreate tables
./scripts/run-local-dev.sh
```

### View DynamoDB Tables

Open http://localhost:8001 in your browser to use the DynamoDB Admin UI.

### Test S3 Operations

```bash
# List buckets
aws --endpoint-url=http://localhost:4566 s3 ls

# Upload a file
aws --endpoint-url=http://localhost:4566 s3 cp test.jpg s3://postpilot-dev-media/

# List objects
aws --endpoint-url=http://localhost:4566 s3 ls s3://postpilot-dev-media/
```

### Test SQS Operations

```bash
# Send a message
aws --endpoint-url=http://localhost:4566 sqs send-message \
  --queue-url http://localhost:4566/000000000000/postpilot-dev-queue \
  --message-body '{"campaign_id": "test-123"}'

# Receive messages
aws --endpoint-url=http://localhost:4566 sqs receive-message \
  --queue-url http://localhost:4566/000000000000/postpilot-dev-queue
```

## Troubleshooting

### DynamoDB Connection Issues

If you get connection errors:
1. Check Docker is running: `docker ps`
2. Check DynamoDB is accessible: `curl http://localhost:8000`
3. Verify environment variable: `DYNAMODB_ENDPOINT=http://localhost:8000`

### LocalStack Issues

If S3 or SQS operations fail:
1. Check LocalStack health: `curl http://localhost:4566/_localstack/health`
2. Check logs: `docker-compose logs localstack`
3. Restart LocalStack: `docker-compose restart localstack`

### Port Conflicts

If ports are already in use:
1. Check what's using the port: `lsof -i :8000` (Mac/Linux) or `netstat -ano | findstr :8000` (Windows)
2. Stop the conflicting service or change ports in docker-compose.yml

## Production vs Development

**Important**: The FastAPI dev server is ONLY for local development. Production uses:
- AWS Lambda for compute
- API Gateway for HTTP endpoints
- DynamoDB (managed) for database
- S3 (managed) for storage
- SQS (managed) for queues

Never deploy the FastAPI server to production!

## Next Steps

- Read [ARCHITECTURE_GUIDE.md](../ARCHITECTURE_GUIDE.md) for system architecture
- Read [template.yaml](template.yaml) for AWS infrastructure
- Check [tests/](tests/) for test examples
- Review [deploy/](deploy/) for deployment configurations
