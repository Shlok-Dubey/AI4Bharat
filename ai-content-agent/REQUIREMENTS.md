# AI Content Agent - Requirements Document

**Project Name:** AI Content Agent  
**Version:** 2.0.0  
**Status:** Production Ready  
**Last Updated:** March 8, 2026

---

## 📋 PROJECT OVERVIEW

### Purpose
An AI-powered social media campaign management platform that automates content generation, scheduling, and publishing using AWS Bedrock (Claude 3) and Instagram Graph API.

### Target Users
- Social media managers
- Marketing teams
- Content creators
- Small businesses
- Digital agencies

### Key Value Proposition
Automate social media campaigns with AI-generated content, intelligent scheduling based on historical performance, and real Instagram integration.

---

## 🎯 FUNCTIONAL REQUIREMENTS

### 1. User Management

#### 1.1 User Registration
- **FR-1.1.1:** Users can create accounts with email and password
- **FR-1.1.2:** Passwords must be hashed using bcrypt
- **FR-1.1.3:** Email must be unique
- **FR-1.1.4:** User data stored in database

#### 1.2 User Authentication
- **FR-1.2.1:** Users can log in with email and password
- **FR-1.2.2:** System generates JWT tokens on successful login
- **FR-1.2.3:** JWT tokens expire after 30 minutes
- **FR-1.2.4:** Protected routes require valid JWT token

#### 1.3 User Profile
- **FR-1.3.1:** Users can view their profile information
- **FR-1.3.2:** System tracks user creation date

---

### 2. Instagram OAuth Integration

#### 2.1 OAuth Connection
- **FR-2.1.1:** Users can connect Instagram Business Account via OAuth
- **FR-2.1.2:** System stores access token securely
- **FR-2.1.3:** System stores Instagram account ID
- **FR-2.1.4:** OAuth uses Meta Graph API v19.0
- **FR-2.1.5:** Supports HTTPS redirect via ngrok

#### 2.2 OAuth Management
- **FR-2.2.1:** Users can view connected accounts
- **FR-2.2.2:** System displays connection status
- **FR-2.2.3:** Users can disconnect accounts

---

### 3. Campaign Management

#### 3.1 Campaign Creation
- **FR-3.1.1:** Users can create marketing campaigns
- **FR-3.1.2:** Campaign requires: name, product name, description, duration
- **FR-3.1.3:** Campaign duration specified in days
- **FR-3.1.4:** Each campaign belongs to one user

#### 3.2 Campaign Listing
- **FR-3.2.1:** Users can view all their campaigns
- **FR-3.2.2:** Dashboard shows campaign count
- **FR-3.2.3:** Campaign cards show: name, status, product, duration
- **FR-3.2.4:** Campaign cards show content counts

#### 3.3 Campaign Details
- **FR-3.3.1:** Users can view campaign details
- **FR-3.3.2:** Details include all campaign information
- **FR-3.3.3:** Details show associated content

#### 3.4 File Upload
- **FR-3.4.1:** Users can upload product images
- **FR-3.4.2:** Supports PNG, JPG, JPEG formats
- **FR-3.4.3:** Files stored in campaign_assets folder
- **FR-3.4.4:** Each file has unique UUID filename

---

### 4. AI Content Generation

#### 4.1 Content Generation
- **FR-4.1.1:** System generates 5 Instagram posts per campaign
- **FR-4.1.2:** Uses AWS Bedrock Claude 3 Sonnet for generation
- **FR-4.1.3:** Generates engaging captions with emojis
- **FR-4.1.4:** Generates 15-20 relevant hashtags
- **FR-4.1.5:** Generates reel scripts with timing
- **FR-4.1.6:** Generates thumbnail text
- **FR-4.1.7:** Falls back to templates if Bedrock unavailable

#### 4.2 Content Review
- **FR-4.2.1:** Users can review generated content
- **FR-4.2.2:** Users can approve individual posts
- **FR-4.2.3:** Users can reject individual posts
- **FR-4.2.4:** Users can regenerate individual posts
- **FR-4.2.5:** Users can approve all posts at once
- **FR-4.2.6:** Only approved content can be scheduled

#### 4.3 Content Storage
- **FR-4.3.1:** Content stored with status (pending, approved, rejected)
- **FR-4.3.2:** Content includes: caption, hashtags, script, thumbnail text
- **FR-4.3.3:** Content tracks AI model used
- **FR-4.3.4:** Content tracks creation and update timestamps

---

### 5. AI Campaign Planning

#### 5.1 Content Distribution
- **FR-5.1.1:** System distributes content across campaign days
- **FR-5.1.2:** Uses AWS Bedrock AI for strategic ordering
- **FR-5.1.3:** Balances content types throughout campaign
- **FR-5.1.4:** Places high-engagement content strategically
- **FR-5.1.5:** Ensures variety in content distribution
- **FR-5.1.6:** Falls back to algorithm if AI unavailable

#### 5.2 Campaign Plan View
- **FR-5.2.1:** Users can view campaign plan
- **FR-5.2.2:** Plan shows content distribution across days
- **FR-5.2.3:** Plan shows recommended posting days

---

### 6. AI Scheduling

#### 6.1 Time Selection
- **FR-6.1.1:** System assigns optimal posting times
- **FR-6.1.2:** Uses AWS Bedrock AI for time selection
- **FR-6.1.3:** Analyzes historical performance data (last 30 days)
- **FR-6.1.4:** Considers content type (reels vs posts)
- **FR-6.1.5:** Considers platform algorithms
- **FR-6.1.6:** Avoids scheduling conflicts (4-hour minimum gap)
- **FR-6.1.7:** Falls back to predefined peak times if no data

#### 6.2 Historical Analysis
- **FR-6.2.1:** System fetches published posts from last 30 days
- **FR-6.2.2:** Calculates engagement by time of day
- **FR-6.2.3:** Identifies top 10 best performing times
- **FR-6.2.4:** Identifies peak days of week
- **FR-6.2.5:** Analyzes content type performance
- **FR-6.2.6:** Caches analysis for 5 minutes

#### 6.3 Schedule Preview
- **FR-6.3.1:** Users can preview schedule before approval
- **FR-6.3.2:** Preview shows: date, time, day of week
- **FR-6.3.3:** Preview shows content caption preview
- **FR-6.3.4:** Preview shows platform and content type
- **FR-6.3.5:** Users can approve schedule

---

### 7. Instagram Posting

#### 7.1 Post Publishing
- **FR-7.1.1:** System publishes posts to Instagram
- **FR-7.1.2:** Uses Instagram Graph API v19.0
- **FR-7.1.3:** Creates media container with image and caption
- **FR-7.1.4:** Checks container status before publishing
- **FR-7.1.5:** Publishes container to Instagram feed
- **FR-7.1.6:** Stores Instagram media ID
- **FR-7.1.7:** Updates post status to "published"

#### 7.2 Manual Publishing
- **FR-7.2.1:** Users can manually publish posts
- **FR-7.2.2:** Manual publish endpoint available via API
- **FR-7.2.3:** Test script available for testing

#### 7.3 Error Handling
- **FR-7.3.1:** System handles expired access tokens
- **FR-7.3.2:** System handles rate limits (25 posts/24hrs)
- **FR-7.3.3:** System handles network errors
- **FR-7.3.4:** System stores error messages
- **FR-7.3.5:** System tracks retry count

---

### 8. Instagram Analytics

#### 8.1 Analytics Fetching
- **FR-8.1.1:** System fetches real engagement metrics
- **FR-8.1.2:** Uses Instagram Graph API insights endpoint
- **FR-8.1.3:** Fetches: likes, comments, saves, impressions, reach
- **FR-8.1.4:** Calculates engagement rate
- **FR-8.1.5:** Falls back to mock data if insights unavailable
- **FR-8.1.6:** Handles 24-48 hour delay for insights

#### 8.2 Analytics Display
- **FR-8.2.1:** Dashboard shows campaign analytics
- **FR-8.2.2:** Charts show: views, likes, comments, engagement
- **FR-8.2.3:** Table shows detailed post metrics
- **FR-8.2.4:** Users can refresh analytics

#### 8.3 Analytics Storage
- **FR-8.3.1:** Analytics stored in PostAnalytics table
- **FR-8.3.2:** Tracks: views, likes, comments, shares, saves
- **FR-8.3.3:** Tracks: reach, impressions, engagement rate
- **FR-8.3.4:** Tracks fetch timestamp

---

### 9. Dashboard & Navigation

#### 9.1 Dashboard
- **FR-9.1.1:** Dashboard shows quick stats
- **FR-9.1.2:** Dashboard shows campaign list
- **FR-9.1.3:** Dashboard shows Instagram connection status
- **FR-9.1.4:** Dashboard has "Create Campaign" button

#### 9.2 Navigation
- **FR-9.2.1:** Complete workflow navigation
- **FR-9.2.2:** Auto-redirects after actions
- **FR-9.2.3:** Breadcrumb navigation
- **FR-9.2.4:** Back buttons where appropriate

---

## 🔧 NON-FUNCTIONAL REQUIREMENTS

### 1. Performance

#### 1.1 Response Time
- **NFR-1.1.1:** API responses < 2 seconds
- **NFR-1.1.2:** AI content generation < 5 seconds per post
- **NFR-1.1.3:** Page load time < 3 seconds
- **NFR-1.1.4:** Database queries < 1 second

#### 1.2 Scalability
- **NFR-1.2.1:** Support 100+ concurrent users
- **NFR-1.2.2:** Handle 1000+ campaigns
- **NFR-1.2.3:** Handle 10,000+ posts

---

### 2. Security

#### 2.1 Authentication
- **NFR-2.1.1:** Passwords hashed with bcrypt
- **NFR-2.1.2:** JWT tokens for session management
- **NFR-2.1.3:** Tokens expire after 30 minutes
- **NFR-2.1.4:** HTTPS for OAuth redirects

#### 2.2 Data Protection
- **NFR-2.2.1:** Access tokens stored securely
- **NFR-2.2.2:** User data isolated by user_id
- **NFR-2.2.3:** SQL injection protection via ORM
- **NFR-2.2.4:** CORS configured properly

---

### 3. Reliability

#### 3.1 Availability
- **NFR-3.1.1:** 99% uptime target
- **NFR-3.1.2:** Graceful error handling
- **NFR-3.1.3:** Automatic fallbacks (AI → templates, API → mock)

#### 3.2 Data Integrity
- **NFR-3.2.1:** Database transactions for consistency
- **NFR-3.2.2:** Foreign key constraints
- **NFR-3.2.3:** Data validation on input

---

### 4. Usability

#### 4.1 User Interface
- **NFR-4.1.1:** Intuitive navigation
- **NFR-4.1.2:** Clear error messages
- **NFR-4.1.3:** Loading indicators
- **NFR-4.1.4:** Responsive design

#### 4.2 User Experience
- **NFR-4.2.1:** Complete workflow in < 10 minutes
- **NFR-4.2.2:** Minimal clicks required
- **NFR-4.2.3:** Auto-redirects after actions
- **NFR-4.2.4:** Informative console messages

---

### 5. Maintainability

#### 5.1 Code Quality
- **NFR-5.1.1:** Modular architecture
- **NFR-5.1.2:** Clear separation of concerns
- **NFR-5.1.3:** Comprehensive documentation
- **NFR-5.1.4:** Consistent coding style

#### 5.2 Testing
- **NFR-5.2.1:** Test scripts for all major features
- **NFR-5.2.2:** Testing guides provided
- **NFR-5.2.3:** Sample data generation scripts

---

## 🛠️ TECHNICAL REQUIREMENTS

### 1. Backend

#### 1.1 Framework & Language
- **TR-1.1.1:** Python 3.10+
- **TR-1.1.2:** FastAPI framework
- **TR-1.1.3:** Uvicorn ASGI server

#### 1.2 Database
- **TR-1.2.1:** SQLite for local development
- **TR-1.2.2:** SQLAlchemy ORM
- **TR-1.2.3:** Support for PostgreSQL (production)
- **TR-1.2.4:** Support for DynamoDB (optional)

#### 1.3 AI & APIs
- **TR-1.3.1:** AWS Bedrock (Claude 3 Sonnet)
- **TR-1.3.2:** boto3 for AWS SDK
- **TR-1.3.3:** Instagram Graph API v19.0
- **TR-1.3.4:** requests library for HTTP

#### 1.4 Security
- **TR-1.4.1:** python-jose for JWT
- **TR-1.4.2:** bcrypt for password hashing
- **TR-1.4.3:** python-dotenv for environment variables

---

### 2. Frontend

#### 2.1 Framework & Language
- **TR-2.1.1:** React 18
- **TR-2.1.2:** JavaScript/JSX
- **TR-2.1.3:** Vite build tool

#### 2.2 Libraries
- **TR-2.2.1:** React Router DOM for routing
- **TR-2.2.2:** Axios for HTTP requests
- **TR-2.2.3:** Recharts for analytics charts

#### 2.3 Styling
- **TR-2.3.1:** Custom CSS
- **TR-2.3.2:** Responsive design

---

### 3. Infrastructure

#### 3.1 Development
- **TR-3.1.1:** Windows compatible
- **TR-3.1.2:** Python virtual environment
- **TR-3.1.3:** npm for frontend dependencies

#### 3.2 Production (Optional)
- **TR-3.2.1:** AWS Bedrock for AI
- **TR-3.2.2:** AWS S3 for file storage (ready)
- **TR-3.2.3:** AWS EventBridge for scheduling (ready)
- **TR-3.2.4:** AWS Lambda for execution (ready)
- **TR-3.2.5:** AWS DynamoDB for database (ready)

---

### 4. External Services

#### 4.1 AWS Services
- **TR-4.1.1:** AWS Bedrock (Claude 3 Sonnet) - Active
- **TR-4.1.2:** AWS IAM for credentials
- **TR-4.1.3:** AWS S3 (ready to activate)
- **TR-4.1.4:** AWS EventBridge (ready to activate)
- **TR-4.1.5:** AWS Lambda (ready to activate)

#### 4.2 Meta Services
- **TR-4.2.1:** Meta Developer Account
- **TR-4.2.2:** Instagram Graph API v19.0
- **TR-4.2.3:** Instagram Business Account
- **TR-4.2.4:** OAuth 2.0

#### 4.3 Development Tools
- **TR-4.3.1:** ngrok for HTTPS tunneling
- **TR-4.3.2:** DB Browser for SQLite (optional)

---

## 📦 DEPENDENCIES

### Backend Dependencies
```
fastapi==0.104.1
sqlalchemy==2.0.23
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.4.2
pydantic-settings==2.0.3
httpx==0.25.2
requests==2.31.0
boto3==1.34.0
bcrypt==4.1.2
```

### Frontend Dependencies
```
react: ^18.2.0
react-dom: ^18.2.0
react-router-dom: ^6.20.0
axios: ^1.6.2
recharts: ^2.10.3
```

---

## 🔐 ENVIRONMENT VARIABLES

### Required Variables
```env
# Database
DATABASE_URL=sqlite:///./ai_content_agent.db

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Meta OAuth
META_APP_ID=your-app-id
META_APP_SECRET=your-app-secret
META_REDIRECT_URI=your-redirect-uri
FRONTEND_URL=your-frontend-url

# AWS Bedrock
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

---

## 📊 DATA MODELS

### 1. User
- id (UUID, PK)
- email (String, unique)
- password_hash (String)
- created_at (DateTime)

### 2. OAuthAccount
- id (UUID, PK)
- user_id (UUID, FK)
- provider (String)
- provider_account_id (String)
- access_token (String)
- refresh_token (String, optional)
- expires_at (DateTime, optional)

### 3. Campaign
- id (UUID, PK)
- user_id (UUID, FK)
- name (String)
- product_name (String)
- product_description (Text)
- campaign_settings (JSON)
- created_at (DateTime)

### 4. CampaignAsset
- id (UUID, PK)
- campaign_id (UUID, FK)
- file_path (String)
- file_type (String)
- file_size (Integer)
- asset_metadata (JSON)

### 5. GeneratedContent
- id (UUID, PK)
- campaign_id (UUID, FK)
- platform (String)
- content_type (String)
- content_text (Text)
- hashtags (String)
- ai_metadata (JSON)
- status (String)
- ai_model (String)
- created_at (DateTime)

### 6. ScheduledPost
- id (UUID, PK)
- content_id (UUID, FK)
- scheduled_for (DateTime)
- status (String)
- platform_post_id (String, optional)
- published_at (DateTime, optional)
- error_message (Text, optional)
- retry_count (Integer)

### 7. PostAnalytics
- id (UUID, PK)
- post_id (UUID, FK)
- views (Integer)
- likes (Integer)
- comments (Integer)
- shares (Integer)
- saves (Integer)
- reach (Integer)
- impressions (Integer)
- engagement_rate (Float)
- fetched_at (DateTime)

---

## 🎯 SUCCESS CRITERIA

### 1. Functional Success
- ✅ All 5 AI agents working
- ✅ Complete workflow functional
- ✅ Instagram integration working
- ✅ AWS Bedrock integration working
- ✅ Historical analytics working

### 2. Performance Success
- ✅ API responses < 2 seconds
- ✅ AI generation < 5 seconds
- ✅ Page loads < 3 seconds

### 3. User Success
- ✅ Complete campaign in < 10 minutes
- ✅ Intuitive navigation
- ✅ Clear error messages

### 4. Technical Success
- ✅ Production-ready code
- ✅ Comprehensive documentation
- ✅ Testing tools provided
- ✅ Scalable architecture

---

## 📝 CONSTRAINTS

### 1. Technical Constraints
- Python 3.10+ required
- Node.js 16+ required
- AWS account required for AI features
- Meta Developer account required for Instagram
- Instagram Business Account required

### 2. API Constraints
- Instagram: 25 posts per 24 hours
- Instagram: 50 API calls per hour
- Instagram: Insights available after 24-48 hours
- AWS Bedrock: Rate limits apply

### 3. Platform Constraints
- Instagram Business Account only (not personal)
- Images must be publicly accessible for posting
- OAuth requires HTTPS (ngrok for local dev)

---

## 🚀 FUTURE ENHANCEMENTS

### Phase 1 (Optional)
- Multi-platform support (Twitter, LinkedIn, TikTok)
- Advanced analytics with AI insights
- Content calendar view
- A/B testing for content

### Phase 2 (Optional)
- Team collaboration features
- White-label solution
- Mobile app
- Competitor analysis

### Phase 3 (Optional)
- Video content generation
- Automated hashtag research
- Influencer collaboration
- ROI tracking

---

## ✅ REQUIREMENTS STATUS

**All requirements:** ✅ COMPLETE  
**All features:** ✅ IMPLEMENTED  
**All agents:** ✅ ACTIVE  
**Documentation:** ✅ COMPREHENSIVE  
**Testing:** ✅ TOOLS PROVIDED  

**Project Status:** PRODUCTION READY 🎉

---

**Last Updated:** March 8, 2026  
**Version:** 2.0.0  
**Status:** Complete
