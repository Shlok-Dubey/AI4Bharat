# PostPilot AI

AI-driven autonomous content orchestration platform for social media automation.

## Overview

PostPilot AI uses multiple specialized AI agents powered by Amazon Bedrock to automate Instagram content creation, scheduling, and publishing. The platform learns from campaign performance and continuously improves content quality through a shared Campaign Intelligence Memory.

## Architecture

- **Frontend**: React 18 + Vite
- **Backend**: AWS Lambda (Python 3.11) + API Gateway
- **Database**: Amazon DynamoDB
- **Storage**: Amazon S3
- **Queue**: Amazon SQS
- **AI**: Amazon Bedrock (Claude 3.5 Sonnet) + Amazon Rekognition
- **Scheduling**: Amazon EventBridge

## Project Structure

```
├── backend/
│   ├── lambdas/
│   │   ├── orchestrator/       # Agent orchestrator
│   │   ├── agents/             # AI agent Lambdas
│   │   └── workers/            # Background workers
│   ├── shared/
│   │   ├── models/             # Domain models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Service layer
│   │   └── utils/              # Utilities
│   ├── dev_api/                # FastAPI for local dev
│   ├── template.yaml           # AWS SAM template
│   └── requirements.txt        # Python dependencies
├── frontend/
│   └── src/
│       ├── components/         # React components
│       ├── pages/              # Page components
│       ├── services/           # API clients
│       ├── hooks/              # Custom hooks
│       ├── auth/               # Auth context
│       └── utils/              # Utilities
└── environment.example         # Environment variables template
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- AWS CLI configured
- AWS SAM CLI (for deployment)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Environment Configuration

Copy `environment.example` to `.env` and configure:

```bash
cp environment.example .env
# Edit .env with your AWS credentials and configuration
```

### Local Development

Start the FastAPI development server:

```bash
cd backend
uvicorn dev_api.main:app --reload
```

Start the React development server:

```bash
cd frontend
npm run dev
```

## Deployment

Deploy to AWS using SAM:

```bash
cd backend
sam build
sam deploy --guided
```

## Testing

Run tests:

```bash
cd backend
pytest
```

## License

Proprietary
