# PostPilot AI - Backend Architecture Guide

## Table of Contents
1. [Database Schema (DynamoDB)](#database-schema)
2. [API Endpoints](#api-endpoints)
3. [Backend Architecture & Connections](#backend-architecture)
4. [Data Flow Examples](#data-flow-examples)

---

## Database Schema (DynamoDB)

PostPilot AI uses **Amazon DynamoDB** with a single-table design pattern for multi-tenancy. Each table uses partition keys (PK) and sort keys (SK) for efficient querying.

### Table 1: `users`

**Purpose**: Store user credentials, Instagram OAuth tokens, and quota information

**Primary Key**:
- **PK**: `USER#{user_id}` (Partition Key)

**Attributes**:
```
{
  "user_id": "uuid",
  "email": "user@example.com",
  "password_hash": "bcrypt_hashed_password",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  
  // Instagram OAuth Data (encrypted)
  "instagram_user_id": "instagram_12345",
  "instagram_username": "@mybusiness",
  "instagram_access_token": "encrypted_token",
  "instagram_refresh_token": "encrypted_token",
  "instagram_token_expires_at": "2024-03-01T00:00:00Z",
  
  // Rate Limiting & Quotas
  "daily_campaign_quota": 50,
  "campaigns_generated_today": 12,
  "quota_reset_date": "2024-01-01",
  "rate_limit_tokens": 100,
  "rate_limit_last_refill": "2024-01-01T12:00:00Z",
  
  // User Settings
  "timezone": "America/New_York"
}
```

**Access Patterns**:
- Get user by ID: Query by PK
- Get user by email: Scan with filter (or use GSI in production)

---

### Table 2: `products`

**Purpose**: Store business products with image analysis results

**Primary Key**:
- **PK**: `USER#{user_id}` (Partition Key)
- **SK**: `PRODUCT#{product_id}` (Sort Key)

**Attributes**:
```
{
  "product_id": "uuid",
  "user_id": "uuid",
  "name": "Eco-Friendly Water Bottle",
  "description": "Sustainable stainless steel bottle",
  "image_url": "s3://bucket/user_id/products/product_id.jpg",
  
  // Rekognition Analysis Results
  "image_analysis": {
    "labels": [
      {"name": "Bottle", "confidence": 98.5},
      {"name": "Product", "confidence": 95.2}
    ],
    "dominant_colors": ["#2E7D32", "#FFFFFF"],
    "has_faces": false,
    "is_safe": true
  },
  
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "deleted_at": null  // Soft delete support
}
```

**Access Patterns**:
- Get all products for user: Query by PK
- Get specific product: Query by PK + SK
- List active products: Query by PK, filter where deleted_at is null

---

### Table 3: `campaigns`

**Purpose**: Store AI-generated campaigns with scheduling and publishing status

**Primary Key**:
- **PK**: `USER#{user_id}` (Partition Key)
- **SK**: `CAMPAIGN#{campaign_id}` (Sort Key)

**Global Secondary Index (GSI)**:
- **GSI PK**: `status` (e.g., "scheduled")
- **GSI SK**: `scheduled_time`
- Used by worker Lambda to find campaigns ready to publish

**Attributes**:
```
{
  "campaign_id": "uuid",
  "user_id": "uuid",
  "product_id": "uuid",
  
  // AI-Generated Content
  "caption": "Discover sustainable living with our eco-friendly bottle! 🌿",
  "hashtags": ["#sustainable", "#ecofriendly", "#zerowaste"],
  
  // Campaign Metadata
  "tone": "inspirational",
  "cta_style": "question-based",
  "hook_pattern": "benefit-first",
  
  // Scheduling & Status
  "status": "draft | scheduled | publishing | published | failed | cancelled",
  "scheduled_time": "2024-01-02T18:00:00Z",
  "published_at": null,
  
  // Instagram Publishing
  "instagram_post_id": null,
  "publish_attempts": 0,
  
  // AI Traceability
  "bedrock_model_version": "claude-3-5-sonnet-20240620",
  "prompt_template_version": "v1.2",
  
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Access Patterns**:
- Get all campaigns for user: Query by PK
- Get specific campaign: Query by PK + SK
- Find scheduled campaigns: Query GSI by status="scheduled", ordered by scheduled_time

---

### Table 4: `analytics`

**Purpose**: Store Instagram insights and performance metrics

**Primary Key**:
- **PK**: `CAMPAIGN#{campaign_id}` (Partition Key)
- **SK**: `ANALYTICS#{timestamp}` (Sort Key)

**Attributes**:
```
{
  "campaign_id": "uuid",
  "user_id": "uuid",
  "timestamp": "2024-01-03T00:00:00Z",
  
  // Instagram Insights
  "likes": 245,
  "comments": 18,
  "reach": 1850,
  "impressions": 2340,
  "engagement_rate": 4.2,  // (likes + comments) / reach * 100
  
  // Metadata
  "fetched_at": "2024-01-03T12:00:00Z"
}
```

**Access Patterns**:
- Get all analytics for campaign: Query by PK
- Get analytics in date range: Query by PK, filter by SK range

---

### Table 5: `memory` (Campaign Intelligence Memory)

**Purpose**: Store AI-learned patterns and insights per user (the "brain" of the system)

**Primary Key**:
- **PK**: `USER#{user_id}` (Partition Key)
- **SK**: `MEMORY#{memory_type}` (Sort Key)

**Memory Types**: `business_profile`, `performance_insights`, `content_patterns`, `engagement_patterns`

**Attributes**:
```
{
  "user_id": "uuid",
  "memory_type": "performance_insights",
  
  // Memory-Specific Data (varies by type)
  "data": {
    "best_tone": {
      "tone": "inspirational",
      "avg_engagement_rate": 4.5,
      "sample_size": 12
    },
    "best_cta_style": {
      "style": "question-based",
      "avg_engagement_rate": 4.8,
      "sample_size": 8
    },
    "success_factors": [
      "Short captions (120-140 chars) perform better",
      "Questions as CTAs increase comments by 30%"
    ]
  },
  
  // Confidence Metrics
  "confidence": 0.85,  // 0.0 - 1.0
  "sample_size": 20,   // Number of campaigns analyzed
  
  "last_updated": "2024-01-03T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Access Patterns**:
- Get specific memory type: Query by PK + SK
- Get all memory for user: Query by PK

---

## API Endpoints

The backend exposes RESTful APIs through **FastAPI** (local dev) and **AWS API Gateway** (production).

### Authentication APIs (`/api/v1/auth`)

#### 1. **POST /api/v1/auth/register**
**Purpose**: Register a new user

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response** (201 Created):
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "user_id": "uuid",
    "email": "user@example.com"
  }
}
```

**What Happens**:
1. Validates email format and password strength
2. Checks if email already exists in DynamoDB
3. Hashes password with bcrypt (cost factor 12)
4. Creates user record in `users` table
5. Generates JWT tokens (60 min access, 7 days refresh)
6. Returns tokens to client

---

#### 2. **POST /api/v1/auth/login**
**Purpose**: Authenticate existing user

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "user_id": "uuid",
    "email": "user@example.com"
  }
}
```

**What Happens**:
1. Looks up user by email in DynamoDB
2. Verifies password with bcrypt
3. Generates new JWT tokens
4. Returns tokens to client

---

#### 3. **POST /api/v1/auth/refresh**
**Purpose**: Get new access token using refresh token

**Request Body**:
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**What Happens**:
1. Validates refresh token signature and expiry
2. Extracts user_id from token
3. Generates new access token (60 min expiry)
4. Returns new access token

---

### Instagram OAuth APIs (`/api/v1/instagram`)

#### 4. **GET /api/v1/instagram/authorize**
**Purpose**: Redirect user to Instagram OAuth page

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200 OK):
```json
{
  "authorization_url": "https://api.instagram.com/oauth/authorize?client_id=...&redirect_uri=...&scope=...&state=..."
}
```

**What Happens**:
1. Validates JWT token
2. Generates OAuth state parameter (CSRF protection)
3. Constructs Instagram authorization URL
4. Returns URL to frontend

---

#### 5. **GET /api/v1/instagram/callback**
**Purpose**: Handle Instagram OAuth callback

**Query Parameters**:
- `code`: Authorization code from Instagram
- `state`: CSRF protection token

**Response** (200 OK):
```json
{
  "message": "Instagram account connected successfully",
  "instagram_username": "@mybusiness"
}
```

**What Happens**:
1. Validates state parameter
2. Exchanges authorization code for access token (Instagram API)
3. Exchanges short-lived token for long-lived token (60 days)
4. Fetches Instagram user profile
5. Encrypts tokens with AES-256-GCM
6. Stores encrypted tokens in DynamoDB `users` table
7. Returns success message

---

#### 6. **POST /api/v1/instagram/refresh**
**Purpose**: Manually refresh Instagram token

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200 OK):
```json
{
  "message": "Instagram token refreshed successfully",
  "expires_at": "2024-03-01T00:00:00Z"
}
```

**What Happens**:
1. Validates JWT token
2. Retrieves user from DynamoDB
3. Decrypts Instagram refresh token
4. Calls Instagram token refresh endpoint
5. Encrypts new tokens
6. Updates DynamoDB with new tokens and expiry
7. Returns success message

---

### Product Management APIs (`/api/v1/products`) - TO BE IMPLEMENTED

#### 7. **POST /api/v1/products**
**Purpose**: Upload product with image

**Headers**: `Authorization: Bearer {access_token}`

**Request Body** (multipart/form-data):
```
name: "Eco-Friendly Water Bottle"
description: "Sustainable stainless steel bottle"
image: [file upload]
```

**Response** (201 Created):
```json
{
  "product_id": "uuid",
  "name": "Eco-Friendly Water Bottle",
  "description": "Sustainable stainless steel bottle",
  "image_url": "https://s3.amazonaws.com/...",
  "image_analysis": {
    "labels": [...],
    "dominant_colors": [...],
    "has_faces": false,
    "is_safe": true
  }
}
```

**What Happens**:
1. Validates JWT token
2. Validates image (JPEG/PNG, max 10MB)
3. Uploads image to S3
4. Calls Rekognition for image analysis
5. Creates product record in DynamoDB
6. Returns product with analysis

---

#### 8. **GET /api/v1/products**
**Purpose**: List user's products

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200 OK):
```json
{
  "products": [
    {
      "product_id": "uuid",
      "name": "Eco-Friendly Water Bottle",
      "image_url": "https://s3.amazonaws.com/...",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### Campaign APIs (`/api/v1/campaigns`) - TO BE IMPLEMENTED

#### 9. **POST /api/v1/campaigns/generate**
**Purpose**: Generate AI campaign for product

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "product_id": "uuid",
  "tone": "inspirational",
  "idempotency_key": "unique_key"
}
```

**Response** (201 Created):
```json
{
  "campaign_id": "uuid",
  "caption": "Discover sustainable living...",
  "hashtags": ["#sustainable", "#ecofriendly"],
  "recommended_posting_time": "2024-01-02T18:00:00Z",
  "status": "draft"
}
```

**What Happens**:
1. Validates JWT token
2. Checks daily campaign quota
3. Invokes Agent Orchestrator Lambda
4. Orchestrator invokes 4 AI agent Lambdas:
   - Business Profiling Lambda
   - Campaign Strategy Lambda
   - Content Generation Lambda
   - Scheduling Intelligence Lambda
5. Aggregates agent outputs
6. Stores campaign in DynamoDB
7. Returns generated campaign

---

#### 10. **POST /api/v1/campaigns/{id}/schedule**
**Purpose**: Schedule campaign for publishing

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "scheduled_time": "2024-01-02T18:00:00Z"
}
```

**Response** (200 OK):
```json
{
  "campaign_id": "uuid",
  "status": "scheduled",
  "scheduled_time": "2024-01-02T18:00:00Z"
}
```

**What Happens**:
1. Validates JWT token and ownership
2. Validates scheduled_time is in future
3. Updates campaign status to "scheduled"
4. Sends message to SQS queue
5. Returns updated campaign

---

## Backend Architecture & Connections

### Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                    │
│  - FastAPI Routes (dev_api/routes/)                     │
│  - Request/Response Schemas (shared/schemas/)           │
│  - Input Validation (Pydantic)                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                        │
│  - Business Logic (shared/services/)                    │
│  - JWT Service (token generation/validation)            │
│  - Password Service (bcrypt hashing)                    │
│  - Encryption Service (AES-256-GCM)                     │
│  - Instagram Service (OAuth, API calls)                 │
│  - Authorization Service (ownership checks)             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   REPOSITORY LAYER                       │
│  - Data Access (repositories/)                          │
│  - UserRepository                                       │
│  - ProductRepository                                    │
│  - CampaignRepository                                   │
│  - AnalyticsRepository                                  │
│  - MemoryRepository                                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    DATA LAYER                            │
│  - DynamoDB Client (shared/utils/dynamodb.py)           │
│  - Domain Models (shared/models/domain.py)              │
│  - AWS SDK (boto3)                                      │
└─────────────────────────────────────────────────────────┘
```

---

### Component Connections

#### 1. **Authentication Flow**

```
Frontend
   │
   │ POST /api/v1/auth/register
   ▼
dev_api/routes/auth.py (Route Handler)
   │
   │ Validates input with Pydantic schema
   ▼
shared/services/password_service.py
   │
   │ hash_password(password)
   ▼
repositories/user_repository.py
   │
   │ create(user)
   ▼
shared/utils/dynamodb.py
   │
   │ put_item()
   ▼
DynamoDB users table
   │
   ▼
shared/services/jwt_service.py
   │
   │ generate_access_token(user_id)
   │ generate_refresh_token(user_id)
   ▼
Response with tokens
```

---

#### 2. **Instagram OAuth Flow**

```
Frontend
   │
   │ GET /api/v1/instagram/authorize
   ▼
dev_api/routes/instagram.py
   │
   │ Validates JWT token
   ▼
shared/services/auth_middleware.py
   │
   │ get_current_user(token)
   ▼
shared/services/instagram_service.py
   │
   │ get_authorization_url()
   ▼
Response with Instagram URL
   │
   ▼
User authorizes on Instagram
   │
   ▼
Instagram redirects to callback
   │
   │ GET /api/v1/instagram/callback?code=...
   ▼
dev_api/routes/instagram.py
   │
   ▼
shared/services/instagram_service.py
   │
   │ exchange_code_for_token(code)
   │ exchange_for_long_lived_token(token)
   │ get_user_profile(token)
   ▼
shared/services/encryption_service.py
   │
   │ encrypt_token(access_token)
   │ encrypt_token(refresh_token)
   ▼
repositories/user_repository.py
   │
   │ update(user_id, instagram_data)
   ▼
DynamoDB users table
```

---

#### 3. **Campaign Generation Flow (Future)**

```
Frontend
   │
   │ POST /api/v1/campaigns/generate
   ▼
dev_api/routes/campaigns.py
   │
   │ Check daily quota
   ▼
repositories/user_repository.py
   │
   │ check_and_increment_quota()
   ▼
lambdas/orchestrator/handler.py (Agent Orchestrator)
   │
   ├─► lambdas/agents/business_profiling.py
   │   │
   │   ├─► repositories/memory_repository.py
   │   │   └─► DynamoDB memory table
   │   │
   │   └─► Amazon Bedrock (Claude 3.5 Sonnet)
   │
   ├─► lambdas/agents/campaign_strategy.py
   │   │
   │   ├─► repositories/memory_repository.py
   │   └─► Amazon Bedrock
   │
   ├─► lambdas/agents/content_generation.py
   │   │
   │   ├─► repositories/memory_repository.py
   │   └─► Amazon Bedrock
   │
   └─► lambdas/agents/scheduling_intelligence.py
       │
       ├─► repositories/memory_repository.py
       └─► Amazon Bedrock
   │
   ▼
Orchestrator aggregates results
   │
   ▼
repositories/campaign_repository.py
   │
   │ create(campaign)
   ▼
DynamoDB campaigns table
```

---

### Key Design Patterns

#### 1. **Repository Pattern**
- Abstracts data access logic
- Each entity has its own repository
- Repositories use DynamoDB client from `shared/utils/dynamodb.py`

Example:
```python
# repositories/user_repository.py
class UserRepository:
    def __init__(self, dynamodb_client):
        self.client = dynamodb_client
        self.table_name = "users"
    
    async def create(self, user: User) -> User:
        # Convert domain model to DynamoDB item
        item = user.to_dynamodb_item()
        await self.client.put_item(self.table_name, item)
        return user
```

---

#### 2. **Service Layer Pattern**
- Business logic separated from routes
- Services orchestrate multiple repositories
- Services handle external API calls

Example:
```python
# shared/services/instagram_service.py
class InstagramService:
    def __init__(self, user_repo, encryption_service):
        self.user_repo = user_repo
        self.encryption = encryption_service
    
    async def exchange_code_for_token(self, code):
        # Call Instagram API
        # Encrypt tokens
        # Store in database
```

---

#### 3. **Dependency Injection**
- Routes receive dependencies via FastAPI's Depends()
- Makes testing easier with mocks

Example:
```python
# dev_api/routes/auth.py
@router.post("/register")
async def register(
    request: UserRegisterRequest,
    user_repo: UserRepository = Depends(get_user_repository)
):
    # Use injected repository
```

---

## Data Flow Examples

### Example 1: User Registration

```
1. User submits email + password
   ↓
2. Route validates with Pydantic schema
   ↓
3. Password Service hashes password (bcrypt, cost 12)
   ↓
4. User Repository creates user in DynamoDB
   PK: USER#uuid
   Attributes: email, password_hash, created_at, etc.
   ↓
5. JWT Service generates tokens
   - Access token: 60 min expiry
   - Refresh token: 7 days expiry
   ↓
6. Response returns tokens to frontend
   ↓
7. Frontend stores tokens in localStorage
```

---

### Example 2: Instagram OAuth Connection

```
1. User clicks "Connect Instagram"
   ↓
2. Frontend calls GET /api/v1/instagram/authorize
   ↓
3. Backend generates OAuth URL with state parameter
   ↓
4. Frontend redirects user to Instagram
   ↓
5. User authorizes on Instagram
   ↓
6. Instagram redirects to callback URL with code
   ↓
7. Backend receives GET /api/v1/instagram/callback?code=...
   ↓
8. Instagram Service exchanges code for short-lived token
   ↓
9. Instagram Service exchanges for long-lived token (60 days)
   ↓
10. Instagram Service fetches user profile
   ↓
11. Encryption Service encrypts tokens (AES-256-GCM)
   ↓
12. User Repository updates user record in DynamoDB
   PK: USER#uuid
   New attributes: instagram_access_token (encrypted),
                   instagram_refresh_token (encrypted),
                   instagram_token_expires_at,
                   instagram_username
   ↓
13. Response confirms connection
```

---

### Example 3: Campaign Generation (Future Implementation)

```
1. User selects product and clicks "Generate Campaign"
   ↓
2. Frontend calls POST /api/v1/campaigns/generate
   Body: { product_id, tone, idempotency_key }
   ↓
3. Route checks daily campaign quota
   - Query DynamoDB users table
   - Check campaigns_generated_today < daily_campaign_quota
   - Increment counter atomically
   ↓
4. Route invokes Agent Orchestrator Lambda
   ↓
5. Orchestrator invokes Business Profiling Lambda
   - Reads memory table: MEMORY#business_profile
   - Calls Bedrock to reason about business identity
   - Returns business profile
   ↓
6. Orchestrator invokes Campaign Strategy Lambda
   - Receives business profile
   - Reads memory table: MEMORY#performance_insights
   - Calls Bedrock to decide strategy
   - Returns tone, CTA style, hook pattern
   ↓
7. Orchestrator invokes Content Generation Lambda
   - Receives strategy
   - Reads product from products table
   - Reads memory table: MEMORY#content_patterns
   - Calls Bedrock to generate caption + hashtags
   - Returns generated content
   ↓
8. Orchestrator invokes Scheduling Intelligence Lambda
   - Reads memory table: MEMORY#engagement_patterns
   - Calls Bedrock to determine optimal time
   - Returns recommended posting time
   ↓
9. Orchestrator aggregates all outputs
   ↓
10. Campaign Repository creates campaign in DynamoDB
   PK: USER#uuid
   SK: CAMPAIGN#uuid
   Attributes: caption, hashtags, tone, status=draft, etc.
   ↓
11. Response returns generated campaign to frontend
```

---

## Summary

### Database Tables
1. **users** - User credentials, Instagram tokens, quotas
2. **products** - Business products with image analysis
3. **campaigns** - AI-generated campaigns with status
4. **analytics** - Instagram insights and metrics
5. **memory** - AI-learned patterns per user

### API Endpoints (Implemented)
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/instagram/authorize` - Get OAuth URL
- `GET /api/v1/instagram/callback` - Handle OAuth callback
- `POST /api/v1/instagram/refresh` - Refresh Instagram token

### Backend Layers
1. **Routes** - HTTP endpoints, input validation
2. **Services** - Business logic, external APIs
3. **Repositories** - Data access abstraction
4. **Utils** - DynamoDB client, helpers

### Key Connections
- Routes → Services → Repositories → DynamoDB
- Services use encryption for sensitive data
- JWT middleware protects authenticated routes
- Repository pattern abstracts database operations
- AI agents (future) will use Bedrock for reasoning

This architecture follows clean architecture principles with clear separation of concerns, making it maintainable, testable, and scalable.
