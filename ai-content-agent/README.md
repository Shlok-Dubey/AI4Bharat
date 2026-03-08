# AI Content Agent

> AI-powered social media campaign management platform with AWS Bedrock integration

A comprehensive AI-driven social media campaign platform that automates content generation, scheduling, and publishing using AWS Bedrock (Claude 3) for real AI content generation.

## 🚀 Features

### ✅ Active Features
- **User Authentication**: JWT-based authentication with bcrypt password hashing
- **Instagram OAuth**: Connect Instagram Business Accounts via Meta Graph API
- **Campaign Management**: Create and manage multi-day marketing campaigns
- **AI Content Generation**: Real AI using AWS Bedrock Claude 3 Sonnet
- **File Upload System**: Upload product images for campaigns
- **Content Review**: Approve or regenerate AI-generated content
- **Smart Scheduling**: Automatic optimal time scheduling for posts
- **Campaign Planning**: Distribute content across campaign days
- **Analytics Dashboard**: Track views, likes, comments, shares, and engagement rates
- **Complete Workflow**: End-to-end campaign management

### 🤖 AI Agents
1. **Content Generator Agent** ✅ ACTIVE - AWS Bedrock Claude 3 integration
2. **Campaign Planner Agent** ⏳ READY - Algorithm-based, AI integration ready
3. **Post Scheduler Agent** ⏳ READY - Predefined times, AI integration ready
4. **Posting Agent** ⏳ READY - Mock posting, Instagram API integration ready
5. **Analytics Agent** ⏳ READY - Mock data, Instagram API integration ready

### ☁️ AWS Integration
- **Amazon Bedrock** ✅ ACTIVE - Claude 3 Sonnet for content generation
- **Amazon S3** ⏳ READY - Asset storage code ready
- **Amazon EventBridge** ⏳ READY - Post scheduling code ready
- **AWS Lambda** ⏳ READY - Serverless execution code ready

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite (local) / PostgreSQL (production)
- **AI**: AWS Bedrock (Claude 3 Sonnet)
- **Authentication**: JWT tokens with python-jose
- **Password Security**: bcrypt hashing
- **File Handling**: python-multipart
- **Server**: Uvicorn ASGI server
- **AWS SDK**: boto3

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Routing**: React Router DOM
- **HTTP Client**: Axios
- **Charts**: Recharts
- **Styling**: Custom CSS

### Database Schema
- **users**: User accounts and profiles
- **oauth_accounts**: Social media OAuth tokens
- **campaigns**: Marketing campaigns
- **campaign_assets**: Uploaded files
- **generated_content**: AI-generated content
- **scheduled_posts**: Scheduled post queue
- **post_analytics**: Engagement metrics

## 📋 Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 16 or higher
- **AWS Account**: For AI features (optional for local dev)
- **Meta Developer Account**: For Instagram OAuth
- **Operating System**: Windows, Linux, or Mac

## 🔧 Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd ai-content-agent
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements_sqlite.txt

# Initialize database
python init_db.py

# Start server
python -m uvicorn main:app --host 0.0.0.0 --port 8002
```

Backend runs on: **http://localhost:8002**

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: **http://localhost:5173**

### 4. Environment Configuration

Create `backend/.env`:

```env
# Database (SQLite for local development)
DATABASE_URL=sqlite:///./ai_content_agent.db

# JWT Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Meta OAuth (for Instagram)
META_APP_ID=your-meta-app-id
META_APP_SECRET=your-meta-app-secret
META_REDIRECT_URI=http://localhost:8002/auth/meta/callback
FRONTEND_URL=http://localhost:5173

# AWS Bedrock (for AI features)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

### 5. AWS Bedrock Setup (Optional)

For real AI content generation:

1. Create AWS account
2. Go to AWS Console → Bedrock → Model access
3. Request access to Anthropic Claude 3 Sonnet
4. Fill out use case form (approval takes ~15 minutes)
5. Add AWS credentials to `.env`

Test connection:
```bash
cd backend
python test_aws_connection.py
```

## 📁 Project Structure

```
ai-content-agent/
├── backend/
│   ├── agents/                      # AI agent modules
│   │   ├── analytics_agent.py       # Analytics fetching
│   │   ├── campaign_planner.py      # Campaign planning
│   │   ├── content_generator.py     # Content generation
│   │   ├── posting_agent.py         # Post publishing
│   │   └── scheduler_agent.py       # Time scheduling
│   ├── dependencies/                # FastAPI dependencies
│   │   └── auth.py                  # JWT authentication
│   ├── models/                      # SQLAlchemy models
│   │   ├── campaign.py              # Campaign & assets
│   │   ├── content.py               # Content & posts
│   │   └── user.py                  # Users & OAuth
│   ├── routes/                      # API endpoints
│   │   ├── auth.py                  # Authentication
│   │   ├── campaigns.py             # Campaign management
│   │   ├── content.py               # Content generation
│   │   ├── oauth.py                 # OAuth integration
│   │   └── schedule.py              # Post scheduling
│   ├── schemas/                     # Pydantic schemas
│   │   ├── asset.py                 # File upload schemas
│   │   ├── auth.py                  # Auth schemas
│   │   ├── campaign.py              # Campaign schemas
│   │   ├── content.py               # Content schemas
│   │   ├── oauth.py                 # OAuth schemas
│   │   └── schedule.py              # Schedule schemas
│   ├── services/                    # External services
│   │   ├── instagram_publisher.py   # Instagram API
│   │   └── meta_oauth.py            # Meta OAuth flow
│   ├── utils/                       # Utility modules
│   │   ├── aws_bedrock.py           # AWS Bedrock (commented)
│   │   ├── aws_dynamodb.py          # DynamoDB (commented)
│   │   ├── aws_eventbridge.py       # EventBridge (commented)
│   │   ├── aws_lambda.py            # Lambda (commented)
│   │   ├── aws_s3.py                # S3 storage (commented)
│   │   ├── file_upload.py           # File handling
│   │   └── security.py              # Password hashing
│   ├── .env.example                 # Environment template
│   ├── base.py                      # SQLAlchemy base
│   ├── config.py                    # Configuration
│   ├── database.py                  # Database connection
│   ├── init_db.py                   # Database initialization
│   ├── main.py                      # FastAPI application
│   ├── requirements.txt             # Python dependencies
│   ├── session.py                   # Database session
│   └── start.bat                    # Windows start script
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── axios.js             # Axios configuration
│   │   ├── components/
│   │   │   ├── FileUpload.jsx       # File upload component
│   │   │   └── InstagramConnect.jsx # Instagram connection
│   │   ├── pages/
│   │   │   ├── Analytics.jsx        # Analytics dashboard
│   │   │   ├── CampaignPlan.jsx     # Campaign planning
│   │   │   ├── CreateCampaign.jsx   # Campaign creation
│   │   │   ├── Dashboard.jsx        # Main dashboard
│   │   │   ├── Home.jsx             # Home page
│   │   │   ├── Login.jsx            # Login page
│   │   │   ├── OAuthError.jsx       # OAuth error
│   │   │   ├── OAuthSuccess.jsx     # OAuth success
│   │   │   ├── ReviewContent.jsx    # Content review
│   │   │   ├── SchedulePreview.jsx  # Schedule preview
│   │   │   └── Signup.jsx           # Signup page
│   │   ├── styles/
│   │   │   ├── Analytics.css        # Analytics styles
│   │   │   ├── Auth.css             # Auth styles
│   │   │   ├── Dashboard.css        # Dashboard styles
│   │   │   ├── FileUpload.css       # Upload styles
│   │   │   ├── ReviewContent.css    # Review styles
│   │   │   └── SchedulePreview.css  # Schedule styles
│   │   ├── utils/
│   │   │   └── auth.js              # Auth utilities
│   │   ├── App.jsx                  # Main app component
│   │   ├── index.css                # Global styles
│   │   └── main.jsx                 # Entry point
│   ├── index.html                   # HTML template
│   ├── package.json                 # NPM dependencies
│   ├── start.bat                    # Windows start script
│   └── vite.config.js               # Vite configuration
├── uploads/                         # Local file storage
│   └── campaign_assets/             # Campaign files
└── README.md                        # This file
```

## 🔄 Complete Workflow

### 1. User Registration & Authentication
```
User Signs Up → JWT Token Generated → User Logs In → Token Stored
```

### 2. Instagram Connection
```
Connect Instagram → OAuth Flow → Meta Authorization → Token Stored → Connected Status
```

### 3. Campaign Creation
```
Create Campaign → Upload Assets → Enter Product Details → Campaign Saved
```

### 4. Content Generation
```
Generate Content → AI Creates Captions/Hashtags/Scripts → Review Content → Approve/Regenerate
```

### 5. Campaign Planning
```
Plan Campaign → Distribute Content Across Days → Assign Platforms → Save Plan
```

### 6. Post Scheduling
```
Schedule Posts → Optimal Times Assigned → Schedule Saved → Posts Queued
```

### 7. Automated Publishing
```
Scheduled Time Reached → Posting Agent Executes → Post Published → Status Updated
```

### 8. Analytics Tracking
```
Posts Published → Metrics Collected → Analytics Dashboard → Performance Insights
```

## 🔌 API Endpoints

### Authentication
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user

### OAuth
- `GET /auth/meta/login` - Initiate Meta OAuth
- `GET /auth/meta/callback` - OAuth callback
- `GET /auth/meta/accounts` - Get connected accounts

### Campaigns
- `POST /campaigns` - Create campaign
- `GET /campaigns` - List campaigns
- `GET /campaigns/{id}` - Get campaign details
- `PUT /campaigns/{id}` - Update campaign
- `DELETE /campaigns/{id}` - Delete campaign
- `POST /campaigns/{id}/upload-assets` - Upload files
- `GET /campaigns/{id}/assets` - List assets
- `GET /campaigns/{id}/analytics` - Get analytics

### Content
- `GET /campaigns/{id}/content` - List content
- `POST /campaigns/{id}/generate-content` - Generate content
- `PUT /content/{id}/approve` - Approve content
- `POST /content/{id}/regenerate` - Regenerate content

### Scheduling
- `POST /campaigns/{id}/schedule` - Create schedule
- `GET /campaigns/{id}/schedule` - Get schedule
- `PUT /schedule/{id}` - Update schedule time
- `POST /schedule/{id}/approve` - Approve schedule

## 🤖 AI Agents Usage

### Content Generator Agent

```python
from agents.content_generator import ContentGeneratorAgent

agent = ContentGeneratorAgent()
content = agent.generate_social_content(
    product_name="EcoBottle",
    product_description="Sustainable water bottle",
    platform="instagram"
)
```

### Campaign Planner Agent

```python
from agents.campaign_planner import CampaignPlannerAgent

agent = CampaignPlannerAgent()
plan = agent.plan_campaign(
    content_list=[...],
    campaign_days=7
)
```

### Scheduler Agent

```python
from agents.scheduler_agent import SchedulerAgent

agent = SchedulerAgent()
schedule = agent.schedule_posts(posts=[...])
```

### Analytics Agent

```python
from agents.analytics_agent import AnalyticsAgent

agent = AnalyticsAgent()
analytics = agent.fetch_campaign_analytics(
    campaign_id="123",
    post_ids=["post1", "post2"]
)
```

## ☁️ AWS Deployment Guide

All AWS integration code is included but commented out. To deploy to AWS:

### 1. Amazon S3 Setup

Uncomment code in `utils/aws_s3.py` and update file upload routes:

```python
# In routes/campaigns.py
from utils.aws_s3 import upload_file_to_s3

# Replace save_file_locally with:
s3_url = upload_file_to_s3(file.file, unique_filename, str(campaign_id))
```

### 2. Amazon Bedrock Setup

Uncomment code in `utils/aws_bedrock.py` and update content generator:

```python
# In agents/content_generator.py
from utils.aws_bedrock import generate_social_media_content

content = generate_social_media_content(
    product_name=product_name,
    product_description=product_description,
    platform=platform
)
```

### 3. EventBridge + Lambda Setup

1. Create Lambda function using code from `utils/aws_lambda.py`
2. Uncomment EventBridge code in `utils/aws_eventbridge.py`
3. Update scheduler to use EventBridge:

```python
# In agents/posting_agent.py
from utils.aws_eventbridge import create_scheduled_post

create_scheduled_post(
    schedule_id=f"post-{post_id}",
    post_data=post_data,
    scheduled_time=scheduled_time
)
```

### 4. DynamoDB Setup (Optional)

To use DynamoDB instead of PostgreSQL:

1. Create DynamoDB tables with schema from `utils/aws_dynamodb.py`
2. Uncomment DynamoDB operations
3. Replace SQLAlchemy calls with DynamoDB operations

### 5. Environment Variables

Update `.env` with AWS credentials:

```env
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
LAMBDA_FUNCTION_ARN=arn:aws:lambda:region:account:function:name
EVENTBRIDGE_ROLE_ARN=arn:aws:iam::account:role/name
```

### 6. Install AWS SDK

```bash
pip install boto3
```

## 📖 Documentation

For complete documentation, see **[COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)**

Includes:
- Detailed installation instructions
- AWS Bedrock setup guide
- Instagram OAuth configuration
- Complete workflow guide
- Agent integration details
- Troubleshooting tips
- Production deployment guide

## ⚡ Quick Commands

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements_sqlite.txt
python init_db.py
python -m uvicorn main:app --host 0.0.0.0 --port 8002

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Visit **http://localhost:5173** to start!

## 🔐 Current Status

### ✅ Working
- User authentication and JWT tokens
- Instagram OAuth connection
- Campaign creation and management
- AWS Bedrock AI content generation (Claude 3)
- Content review and approval workflow
- Campaign planning with smart distribution
- Post scheduling with optimal times
- Analytics dashboard with mock data
- File upload for product images
- Complete end-to-end workflow

### ⚠️ Pending Activation
- **AWS Bedrock Full Access**: Submit use case form in AWS Console
- **Real Instagram Posting**: API code ready, needs activation
- **Real Analytics**: API code ready, needs activation
- **AI Campaign Planning**: Bedrock integration ready
- **AI Scheduling**: Bedrock integration ready

## 📝 Notes

- **Database**: Uses SQLite for local development (no PostgreSQL required)
- **Port**: Backend runs on port 8002 (not 8000)
- **AWS**: Bedrock integration active, other AWS services ready to activate
- **Instagram**: OAuth working with ngrok for HTTPS
- **Python**: Requires 3.10+ for bcrypt compatibility

---

**Built with ❤️ using AWS Bedrock, FastAPI, and React**
