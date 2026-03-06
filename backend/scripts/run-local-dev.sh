#!/bin/bash
# Script to run local development environment

set -e

echo "🚀 Starting PostPilot AI Local Development Environment"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start Docker containers
echo "📦 Starting Docker containers (DynamoDB Local, LocalStack)..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Check if DynamoDB is ready
echo "🔍 Checking DynamoDB Local..."
until curl -s http://localhost:8000 > /dev/null 2>&1; do
    echo "   Waiting for DynamoDB Local..."
    sleep 2
done
echo "✅ DynamoDB Local is ready"

# Check if LocalStack is ready
echo "🔍 Checking LocalStack..."
until curl -s http://localhost:4566/_localstack/health > /dev/null 2>&1; do
    echo "   Waiting for LocalStack..."
    sleep 2
done
echo "✅ LocalStack is ready"

# Create DynamoDB tables
echo "📊 Creating DynamoDB tables..."
python3 scripts/setup-local-dynamodb.py

# Create S3 bucket in LocalStack
echo "🪣 Creating S3 bucket in LocalStack..."
aws --endpoint-url=http://localhost:4566 s3 mb s3://postpilot-dev-media --region us-east-1 2>/dev/null || echo "   Bucket already exists"

# Create SQS queue in LocalStack
echo "📬 Creating SQS queue in LocalStack..."
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name postpilot-dev-queue --region us-east-1 2>/dev/null || echo "   Queue already exists"

echo ""
echo "✅ Local development environment is ready!"
echo ""
echo "📍 Service URLs:"
echo "   - FastAPI Dev Server: http://localhost:8000"
echo "   - DynamoDB Local: http://localhost:8000"
echo "   - DynamoDB Admin UI: http://localhost:8001"
echo "   - LocalStack: http://localhost:4566"
echo ""
echo "🔧 To start the FastAPI server, run:"
echo "   cd backend && uvicorn dev_api.main:app --reload"
echo ""
echo "🛑 To stop all services, run:"
echo "   docker-compose down"
echo ""
