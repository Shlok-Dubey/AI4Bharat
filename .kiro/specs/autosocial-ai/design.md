# Design Document: PostPilot AI (AI-First Multi-Agent Architecture)

## Overview

PostPilot AI is an AI-driven autonomous content orchestration platform that uses multiple specialized AI agents to automate social media presence for businesses. Unlike traditional rule-based systems, this platform employs intelligent agents that learn from campaign performance, adapt strategies, and continuously improve content quality through a shared Campaign Intelligence Memory.

### System Purpose

The platform transforms social media automation from static scheduling to intelligent orchestration by:
- Using AI agents to reason about business context and campaign strategy
- Learning from past campaign performance to improve future content
- Adapting content tone, timing, and style based on analytics feedback
- Autonomously generating, scheduling, and publishing Instagram content
- Building business-specific intelligence that improves over time

### Why AI is Essential

Traditional rule-based social media tools fail because:
- **Static Templates**: Cannot adapt to changing audience preferences
- **No Learning**: Same mistakes repeated across campaigns
- **Generic Content**: One-size-fits-all approach ignores business uniqueness
- **Manual Optimization**: Requires constant human intervention to improve

AI agents solve these problems by:
- **Contextual Reasoning**: Understanding business goals and product context
- **Continuous Learning**: Analyzing what works and adapting strategies
- **Personalization**: Tailoring content to each business's unique voice
- **Autonomous Improvement**: Self-optimizing without human intervention

### Technology Stack

**Frontend:**
- React 18 with Vite
- Axios for HTTP client
- React Router for navigation
- JWT authentication

**AWS Serverless Backend:**
- AWS Lambda (Python 3.11 runtime) for all compute
- Amazon API Gateway for HTTP endpoints
- Amazon DynamoDB for all data storage (users, campaigns, analytics, memory)
- Amazon S3 for media storage
- Amazon SQS for asynchronous job scheduling
- Amazon EventBridge for scheduled triggers
- Amazon CloudWatch for logging and monitoring

**AI Services:**
- Amazon Bedrock (Claude 3.5 Sonnet) for all agent reasoning and content generation
- Amazon Rekognition for image analysis

**External APIs:**
- Instagram Graph API v18.0
- OAuth 2.0 for Instagram authentication

**Development Tools:**
- Pydantic v2 for data validation (Lambda layer)
- Boto3 for AWS SDK (Lambda layer)


## Architecture

### AWS Serverless Multi-Agent System

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER (React Frontend)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Amazon API Gateway  │
                  └──────────┬───────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              AGENT ORCHESTRATOR (Lambda)                         │
│  - Receives HTTP requests from API Gateway                       │
│  - Invokes specialized agent Lambdas                             │
│  - Aggregates agent outputs                                      │
│  - Returns coordinated response                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │  BUSINESS    │  │  CAMPAIGN    │  │   CONTENT    │
    │  PROFILING   │  │  STRATEGY    │  │  GENERATION  │
    │   (Lambda)   │  │   (Lambda)   │  │   (Lambda)   │
    └──────────────┘  └──────────────┘  └──────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   SCHEDULING         │
                  │   INTELLIGENCE       │
                  │     (Lambda)         │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │    Amazon SQS        │
                  │  (Publishing Queue)  │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   PUBLISHING         │
                  │   WORKER (Lambda)    │
                  │  (SQS Trigger)       │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Instagram Graph API │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   ANALYTICS          │
                  │   COLLECTOR (Lambda) │
                  │  (EventBridge)       │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   PERFORMANCE        │
                  │   LEARNING (Lambda)  │
                  └──────────┬───────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │      Amazon DynamoDB         │
              │  - Users & Auth              │
              │  - Products & Campaigns      │
              │  - Analytics Data            │
              │  - Campaign Intelligence     │
              │    Memory (Learned Patterns) │
              └──────────────────────────────┘

              ┌──────────────────────────────┐
              │       Amazon S3              │
              │  - Product Images            │
              │  - Media Assets              │
              └──────────────────────────────┘

              ┌──────────────────────────────┐
              │    Amazon Bedrock            │
              │  (Claude 3.5 Sonnet)         │
              │  - All Agent Reasoning       │
              └──────────────────────────────┘

              ┌──────────────────────────────┐
              │   Amazon Rekognition         │
              │  - Image Analysis            │
              └──────────────────────────────┘
```

### Event-Driven Execution Model

**Synchronous (API Gateway → Lambda)**:
- User authentication and registration
- Product upload and management
- Campaign generation (orchestrates agent Lambdas)
- Campaign scheduling

**Asynchronous (SQS → Lambda)**:
- Campaign publishing at scheduled time
- Retry logic for failed publishes

**Scheduled (EventBridge → Lambda)**:
- Analytics collection (every 6 hours)
- Performance learning and memory updates

### AI-Driven Workflow Loop

The system follows an intelligent, self-improving loop:

```
User Input (Product + Context)
    ↓
Agent Reasoning (Business Profiling)
    ↓
Strategy Decision (Campaign Strategy Agent)
    ↓
Content Generation (Content Generation Agent)
    ↓
Scheduling Decision (Scheduling Intelligence Agent)
    ↓
Publishing (Instagram API)
    ↓
Analytics Collection (Instagram Insights)
    ↓
Learning (Performance Learning Agent)
    ↓
Memory Update (Campaign Intelligence Memory)
    ↓
Next Campaign Improvement (Loop back with learned insights)
```

### Why This is AI-First, Not Rule-Based

**Traditional Approach (What We're NOT Doing):**
- Fixed templates with variable substitution
- Static scheduling rules (e.g., "always post at 6 PM")
- Generic hashtag lists
- No learning from performance

**AI-First Approach (What We ARE Doing):**
- **Business Profiling Agent** reasons about business identity, target audience, and brand voice by analyzing implicit patterns
- **Campaign Strategy Agent** evaluates product context and past performance to decide optimal campaign approach based on learned effectiveness
- **Content Generation Agent** creates contextually relevant content by reasoning over strategy, product details, and best-performing patterns from Memory
- **Scheduling Intelligence Agent** determines best posting time by analyzing historical engagement patterns and reasoning about audience behavior
- **Performance Learning Agent** continuously analyzes what worked, extracts insights, and updates Memory so future campaigns improve automatically

Each agent uses Amazon Bedrock (Claude 3.5 Sonnet) for reasoning, not simple if-then rules.

### Request Flow Patterns

#### Pattern 1: User Registration and Authentication
1. User submits credentials to React frontend
2. React sends POST to API Gateway
3. API Gateway triggers Authentication Lambda
4. Lambda hashes password with bcrypt, stores user in DynamoDB
5. Lambda generates JWT tokens (60 min access, 7 days refresh)
6. Tokens returned to React and stored in localStorage

#### Pattern 2: Instagram OAuth Connection
1. User authorizes Instagram via OAuth
2. API Gateway triggers OAuth Handler Lambda
3. Lambda exchanges code for Instagram tokens
4. Lambda encrypts tokens using AWS KMS
5. Lambda stores encrypted tokens in DynamoDB users table
6. Lambda fetches Instagram profile metadata and stores

#### Pattern 3: Product Upload and Image Analysis
1. User uploads product with image via React
2. API Gateway triggers Product Upload Lambda
3. Lambda uploads image to S3
4. Lambda invokes Rekognition to analyze image
5. Lambda stores product in DynamoDB with analysis results
6. Image analysis becomes input for AI agents during campaign generation

#### Pattern 4: AI Campaign Generation (Multi-Agent Lambda Orchestration)

This is where the AI magic happens:

1. **User Request**: User clicks "Generate Campaign"
2. **API Gateway** triggers **Agent Orchestrator Lambda**
3. **Orchestrator invokes Business Profiling Lambda**:
   - Lambda retrieves business context from DynamoDB Memory table
   - Lambda calls Bedrock to reason about business identity
   - Lambda returns business profile
4. **Orchestrator invokes Campaign Strategy Lambda**:
   - Lambda receives business profile and product details
   - Lambda retrieves past performance from DynamoDB Memory
   - Lambda calls Bedrock to decide optimal strategy
   - Lambda returns strategy (tone, CTA, hook pattern)
5. **Orchestrator invokes Content Generation Lambda**:
   - Lambda receives strategy and product details
   - Lambda retrieves best-performing patterns from DynamoDB Memory
   - Lambda calls Bedrock to generate caption and hashtags
   - Lambda returns generated content
6. **Orchestrator invokes Scheduling Intelligence Lambda**:
   - Lambda retrieves engagement patterns from DynamoDB Memory
   - Lambda calls Bedrock to determine optimal posting time
   - Lambda returns scheduling recommendation
7. **Orchestrator aggregates** all agent outputs
8. **Orchestrator stores** campaign in DynamoDB campaigns table
9. **Response** returned to React via API Gateway

#### Pattern 5: Campaign Scheduling and Publishing
1. User schedules campaign via React
2. API Gateway triggers Scheduling Lambda
3. Lambda validates scheduled time
4. Lambda updates campaign status to "scheduled" in DynamoDB
5. Lambda sends message to SQS queue with campaign details
6. **At scheduled time**, SQS triggers Publishing Worker Lambda
7. Worker Lambda retrieves campaign from DynamoDB
8. Worker Lambda decrypts Instagram token from DynamoDB
9. Worker Lambda downloads image from S3
10. Worker Lambda creates Instagram media container and publishes
11. Worker Lambda updates campaign status to "published" in DynamoDB

#### Pattern 6: Analytics and Learning Loop
1. **EventBridge scheduled rule** triggers Analytics Collector Lambda (every 6 hours)
2. Lambda queries DynamoDB for published campaigns
3. Lambda fetches Instagram Insights for each campaign
4. Lambda stores metrics in DynamoDB analytics table
5. Lambda invokes Performance Learning Lambda
6. **Performance Learning Lambda**:
   - Retrieves campaign metadata and metrics from DynamoDB
   - Calls Bedrock to reason over performance data
   - Identifies success patterns and insights
   - Updates DynamoDB Memory table with learned patterns
   - Increases confidence scores with more data
7. **Next campaign generation** automatically benefits:
   - All agent Lambdas read updated Memory from DynamoDB
   - Agents reason over learned insights to improve campaigns


## AI Agent Specifications

Each agent is an independent AWS Lambda function that uses Amazon Bedrock for reasoning. Agents are stateless and invoked by the Orchestrator Lambda.

### Agent Orchestrator Lambda

**Purpose**: Central Lambda that coordinates multi-agent workflow

**Trigger**: API Gateway HTTP request

**Workflow**:
1. Invoke Business Profiling Lambda to understand business identity
2. Invoke Campaign Strategy Lambda with profile to decide optimal approach
3. Invoke Content Generation Lambda with strategy to create content
4. Invoke Scheduling Intelligence Lambda to determine best posting time
5. Aggregate all agent outputs into complete Campaign object
6. Store in DynamoDB campaigns table and return to user

**AWS Services Used**:
- Lambda SDK to invoke other Lambdas
- DynamoDB for data storage
- CloudWatch for logging

### Business Profiling Lambda

**Purpose**: Understand the business identity, target audience, and brand voice

**Trigger**: Invoked by Orchestrator Lambda

**Inputs**:
- User ID
- Historical campaigns (from DynamoDB Memory table)
- Product catalog (from DynamoDB products table)
- Instagram profile data (from DynamoDB users table)

**Outputs**:
- Business type (e.g., "fashion boutique", "tech startup")
- Target audience demographics
- Brand voice characteristics
- Key value propositions

**DynamoDB Interaction**:
- Reads: Memory table (PK: USER#{user_id}, SK: MEMORY#business_profile)
- Writes: Updates business profile in Memory table

**AWS Services Used**:
- Amazon Bedrock for AI reasoning
- DynamoDB for memory storage
- CloudWatch for logging

**AI Responsibility**:
- **Why AI**: Cannot use rules to understand nuanced business identity, which emerges from implicit patterns across products, content, and audience interactions
- **What AI Does**: Calls Bedrock to reason over product descriptions, past content, Instagram bio, and engagement patterns to infer business type, target audience demographics, brand personality, and value propositions
- **Why Not Rules**: Business identity is contextual, multi-dimensional, and often implicit; requires reasoning about subtle patterns that rules cannot capture

### Campaign Strategy Lambda

**Purpose**: Decide optimal campaign approach based on product context and past performance

**Trigger**: Invoked by Orchestrator Lambda

**Inputs**:
- Business profile (from Business Profiling Lambda)
- Product details and image analysis (from DynamoDB)
- Past campaign performance (from DynamoDB Memory table)
- User tone preference

**Outputs**:
- Recommended tone
- CTA (Call-to-Action) style
- Hook pattern
- Content angle
- Hashtag strategy

**DynamoDB Interaction**:
- Reads: Memory table (PK: USER#{user_id}, SK: MEMORY#performance_insights)
- Reads: Campaigns table for historical data

**AWS Services Used**:
- Amazon Bedrock for AI reasoning
- DynamoDB for memory and campaign data
- CloudWatch for logging

**AI Responsibility**:
- **Why AI**: Strategy requires reasoning about multiple factors, trade-offs, and learned performance patterns that interact in complex ways
- **What AI Does**: Evaluates product context, business goals, and past campaign performance from Memory, then calls Bedrock to decide the optimal campaign approach (tone, CTA style, hook pattern) based on what has driven engagement for this specific business
- **Why Not Rules**: Strategy is contextual and business-specific; what works for one product/audience may not work for another, and effectiveness changes over time based on performance data

### Content Generation Lambda

**Purpose**: Generate engaging captions and hashtags that match learned patterns

**Trigger**: Invoked by Orchestrator Lambda

**Inputs**:
- Campaign strategy (from Campaign Strategy Lambda)
- Product details and image analysis (from DynamoDB)
- Best-performing content patterns (from DynamoDB Memory table)

**Outputs**:
- Caption (120-180 characters)
- Hashtags (max 10)
- Emojis (contextually appropriate)

**DynamoDB Interaction**:
- Reads: Memory table (PK: USER#{user_id}, SK: MEMORY#content_patterns)

**AWS Services Used**:
- Amazon Bedrock for AI reasoning
- DynamoDB for memory storage
- CloudWatch for logging

**AI Responsibility**:
- **Why AI**: Content must be creative, contextual, authentic, and match the brand voice while incorporating learned patterns about what drives engagement
- **What AI Does**: Calls Bedrock to generate original captions that weave together the campaign strategy, product details, image analysis, and best-performing content patterns from Memory, creating natural-sounding content that resonates with the specific audience
- **Why Not Rules**: Templates produce generic, inauthentic content; AI creates contextually relevant captions that feel human-written while strategically incorporating learned success factors

### Scheduling Intelligence Lambda

**Purpose**: Determine optimal posting time using historical engagement data

**Trigger**: Invoked by Orchestrator Lambda

**Inputs**:
- User ID
- Campaign context
- Historical engagement data (from DynamoDB Memory table)
- User timezone (from DynamoDB users table)

**Outputs**:
- Optimal posting time (datetime)
- Confidence score
- Reasoning

**DynamoDB Interaction**:
- Reads: Memory table (PK: USER#{user_id}, SK: MEMORY#engagement_patterns)

**AWS Services Used**:
- Amazon Bedrock for AI reasoning
- DynamoDB for memory storage
- CloudWatch for logging

**AI Responsibility**:
- **Why AI**: Optimal timing depends on complex, non-linear patterns in engagement data that vary by business and audience
- **What AI Does**: Analyzes historical engagement patterns from Memory, reasons about audience behavior, and calls Bedrock to determine the best posting window based on learned performance data
- **Why Not Rules**: Engagement patterns are business-specific and evolve over time; static rules like "always 6 PM" ignore actual audience behavior and performance data

### Performance Learning Lambda

**Purpose**: Analyze campaign performance and update Campaign Intelligence Memory

**Trigger**: Invoked by Analytics Collector Lambda after fetching Instagram Insights

**Inputs**:
- Campaign ID
- Instagram analytics (likes, comments, reach, impressions) from DynamoDB
- Campaign metadata (tone, CTA, hook, posting time) from DynamoDB

**Outputs**:
- Performance insights
- Memory updates
- Learned patterns

**DynamoDB Interaction**:
- Reads: Analytics table, Campaigns table
- Writes: Memory table (all memory types: performance_insights, content_patterns, engagement_patterns)

**AWS Services Used**:
- Amazon Bedrock for AI reasoning
- DynamoDB for data and memory storage
- CloudWatch for logging

**AI Responsibility**:
- **Why AI**: Identifying what worked requires reasoning about complex, interacting factors in campaign performance data
- **What AI Does**: Calls Bedrock to analyze performance data, extract patterns about what drove engagement (tone, CTA, timing, content structure), and generate actionable insights that update Campaign Intelligence Memory for future campaign improvements
- **Why Not Rules**: Performance factors interact in non-obvious ways; requires reasoning to identify true causal patterns vs. correlation, and to generate insights that generalize to future campaigns


## Campaign Intelligence Memory (DynamoDB)

This is the core AI learning component. Each business has its own memory stored in a dedicated DynamoDB table.

### DynamoDB Memory Table Structure

**Table Name**: `campaign_intelligence_memory`

**Primary Key**:
- Partition Key (PK): `USER#{user_id}`
- Sort Key (SK): `MEMORY#{memory_type}`

**Memory Types**: `business_profile`, `performance_insights`, `content_patterns`, `engagement_patterns`

**Attributes**:
- `memory_type`: String
- `data`: Map (memory-specific data structure)
- `confidence`: Number (0.0-1.0)
- `sample_size`: Number (campaigns analyzed)
- `last_updated`: Number (Unix timestamp)
- `created_at`: Number (Unix timestamp)

### Memory Types

#### Business Profile Memory
```json
{
  "business_type": "sustainable fashion boutique",
  "target_audience": {
    "demographics": "25-40, urban professionals",
    "interests": ["sustainability", "ethical fashion"],
    "values": ["environmental consciousness", "quality over quantity"]
  },
  "brand_voice": {
    "tone": "authentic and educational",
    "personality_traits": ["passionate", "knowledgeable", "approachable"],
    "language_style": "conversational with expertise"
  },
  "value_propositions": ["eco-friendly materials", "fair trade practices"]
}
```

#### Performance Insights Memory
```json
{
  "best_tone": {
    "tone": "luxury",
    "avg_engagement_rate": 4.2,
    "sample_size": 8
  },
  "best_cta_style": {
    "style": "question-based",
    "avg_engagement_rate": 4.5
  },
  "success_factors": [
    "Short captions (120-140 chars) perform better",
    "Questions as CTAs increase comments"
  ],
  "patterns_to_avoid": [
    "Generic hashtags show low reach",
    "Multiple emojis reduce engagement"
  ]
}
```

#### Content Patterns Memory
```json
{
  "best_caption_structures": [
    {
      "structure": "Hook + Benefit + CTA",
      "avg_engagement": 4.5,
      "count": 6
    }
  ],
  "effective_hashtag_combinations": [
    {
      "hashtags": ["#sustainablefashion", "#ethicalstyle"],
      "avg_reach": 1250
    }
  ],
  "emoji_usage": {
    "optimal_count": 2,
    "best_emojis": ["✨", "🌿", "💚"]
  }
}
```

#### Engagement Patterns Memory
```json
{
  "best_posting_times": [
    {
      "day_of_week": "Monday",
      "hour": 18,
      "avg_engagement_rate": 4.8
    }
  ],
  "engagement_by_day": {
    "Monday": {"avg_engagement": 4.2, "count": 5},
    "Wednesday": {"avg_engagement": 4.5, "count": 4}
  },
  "audience_activity_pattern": "evening_peak"
}
```


## Key Algorithms

### Image Analysis Algorithm

**Lambda**: Product Upload Handler

**Steps**:
1. Validate image format and size (JPEG/PNG, max 10MB)
2. Upload image to S3 bucket
3. Call Rekognition DetectLabels (MinConfidence: 75)
4. Agent evaluates labels by confidence scores
5. Agent selects top 5 most relevant labels
6. Call Rekognition DetectFaces to detect human presence
7. Call Rekognition DetectModerationLabels for content safety verification
8. Agent extracts dominant colors from visual data
9. Store ImageAnalysis object in DynamoDB products table
10. Return analysis for agent consumption

### Campaign Generation Algorithm

**Lambda**: Agent Orchestrator

**Steps**:
1. **Business Profiling Lambda** reasons about business identity using historical campaigns and product catalog from DynamoDB
2. **Campaign Strategy Lambda** evaluates product context and past performance from DynamoDB to decide:
   - Optimal tone based on learned effectiveness
   - CTA style that drives engagement
   - Hook pattern that resonates with audience
   - Hashtag strategy aligned with brand
3. **Content Generation Lambda** creates caption and hashtags by:
   - Calling Bedrock with strategy, product details, and image analysis
   - Incorporating best-performing content patterns from DynamoDB Memory
   - Generating contextually relevant hashtags
   - Ensuring brand consistency
4. **Scheduling Intelligence Lambda** determines optimal posting time by:
   - Analyzing historical engagement patterns from DynamoDB Memory
   - Reasoning over day-of-week and time-of-day performance
   - Considering user timezone and audience activity patterns
   - Calling Bedrock to decide best posting window
5. **Orchestrator aggregates** all agent outputs into complete campaign
6. **Store Campaign** in DynamoDB campaigns table with status "draft"

### Instagram Publishing Algorithm

**Lambda**: Publishing Worker (triggered by SQS)

**Steps**:
1. Receive message from SQS queue
2. Retrieve campaign from DynamoDB campaigns table
3. Retrieve and decrypt Instagram token from DynamoDB users table
4. Check token expiry, refresh if needed (call Instagram API)
5. Generate S3 presigned URL for image (5 min expiry)
6. Create Instagram media container via Graph API
7. Poll container status (max 30 seconds, 5s intervals)
8. Publish container to Instagram feed
9. Store Instagram post_id in DynamoDB campaigns table
10. Update campaign status to "published" in DynamoDB
11. Delete message from SQS queue

**Retry Logic**:
- 5xx errors: Lambda retries automatically (up to 2 retries)
- 429 rate limit: Wait for retry-after header duration, then retry
- 4xx errors (except 429): No retry, mark campaign as failed
- If all retries exhausted: Message moves to SQS Dead Letter Queue

### Analytics Aggregation Algorithm

**Lambda**: Performance Learning Lambda

**Steps**:
1. Query DynamoDB analytics table for user's campaigns in date range
2. **Performance Learning Lambda** analyzes the data:
   - Evaluates campaign performance vs. historical baselines
   - Identifies successful patterns (tone, CTA, timing, content structure)
   - Reasons about what drove engagement
   - Calls Bedrock to extract actionable insights
3. **Lambda updates DynamoDB Memory table** with:
   - Best-performing tone and CTA styles
   - Effective content patterns and structures
   - Optimal posting times and engagement windows
   - Success factors and patterns to avoid
4. **Memory confidence scores** increase with sample size
5. **Future campaigns** automatically leverage these learned insights through agent reasoning


## Data Models

### DynamoDB Tables

#### users Table
**Primary Key**: PK (Partition Key) = `USER#{user_id}`

**Attributes**:
- User credentials and profile
- Instagram OAuth tokens (encrypted with AWS KMS)
- Timezone and quota settings
- Daily campaign generation counter
- Quota reset date

#### products Table
**Primary Key**: 
- PK = `USER#{user_id}`
- SK (Sort Key) = `PRODUCT#{product_id}`

**Attributes**:
- Product details (name, description)
- S3 image URL
- Rekognition analysis results
- Soft delete support (deleted_at timestamp)

**Access Pattern**: Query by PK to get all products for a user

#### campaigns Table
**Primary Key**:
- PK = `USER#{user_id}`
- SK = `CAMPAIGN#{campaign_id}`

**Attributes**:
- Campaign content (caption, hashtags)
- Status (draft, scheduled, publishing, published, failed)
- Scheduling information
- Instagram post ID
- Bedrock model version tracking

**Global Secondary Index (GSI)**: 
- GSI PK = `status`
- GSI SK = `scheduled_time`
- Used by Publishing Worker Lambda to query scheduled campaigns

**Access Pattern**: Query by PK to get all campaigns for a user

#### analytics Table
**Primary Key**:
- PK = `CAMPAIGN#{campaign_id}`
- SK = `ANALYTICS#{timestamp}`

**Attributes**:
- Instagram insights per campaign
- Metrics: likes, comments, reach, impressions
- Engagement rate calculations
- Timestamp for trend analysis

**Access Pattern**: Query by PK to get all analytics for a campaign

#### memory Table (Campaign Intelligence Memory)
**Primary Key**:
- PK = `USER#{user_id}`
- SK = `MEMORY#{memory_type}`

**Attributes**:
- Per-user learned patterns
- Memory types: business_profile, performance_insights, content_patterns, engagement_patterns
- Confidence scores and sample sizes
- Last updated timestamps

**Access Pattern**: Query by PK and SK to get specific memory type for a user


## Security Considerations (High-Level)

**Authentication & Authorization**:
- JWT tokens with 60-minute access and 7-day refresh expiry
- Bcrypt password hashing (cost factor 12) in Lambda
- Resource ownership verification on all Lambda operations
- Tenant isolation enforced at DynamoDB query level (PK filtering)

**Data Protection**:
- Instagram tokens encrypted using AWS KMS
- Sensitive data never logged (passwords, tokens, API keys)
- HTTPS/TLS for all API communication via API Gateway
- S3 bucket encryption at rest

**Rate Limiting & Quotas**:
- Token bucket algorithm implemented in Lambda: 100 requests per minute per user
- Rate limit state stored in DynamoDB
- Daily campaign generation quota: 50 per user
- Automatic quota reset at midnight UTC

**Input Validation**:
- Pydantic schemas validate all API inputs in Lambda
- File upload restrictions (JPEG/PNG only, max 10MB)
- Input sanitization to prevent injection attacks

**AWS IAM Security**:
- Lambda execution roles with least-privilege permissions
- Separate IAM roles for each Lambda function
- S3 bucket policies restrict access to Lambda roles only
- DynamoDB table policies enforce access control


## Testing Strategy (High-Level)

**Unit Tests**:
- Agent Lambda logic with mocked Bedrock responses
- Hashtag generation logic
- Token encryption/decryption with KMS
- Rate limiting calculations

**Integration Tests**:
- API Gateway → Lambda integration
- Lambda → DynamoDB operations
- Lambda → S3 operations
- Multi-agent Lambda orchestration workflow
- Campaign scheduling and SQS message flow
- Analytics collection and aggregation

**End-to-End Tests**:
- Complete user journey: register → upload product → generate campaign → schedule → publish
- Rate limiting enforcement across multiple API calls
- Quota enforcement across daily boundary

**Mocking Strategy**:
- All external services mocked (Instagram, Bedrock, Rekognition)
- AWS services mocked using moto library (S3, SQS, DynamoDB)
- Use pytest for Python Lambda testing
- Use AWS SAM Local for local Lambda testing


## Deployment Architecture

**AWS Serverless Services**:
- **API Gateway**: REST API with JWT authorizer for all HTTP endpoints
- **Lambda Functions**: 
  - Agent Orchestrator Lambda
  - Business Profiling Lambda
  - Campaign Strategy Lambda
  - Content Generation Lambda
  - Scheduling Intelligence Lambda
  - Publishing Worker Lambda (SQS trigger)
  - Analytics Collector Lambda (EventBridge trigger)
  - Performance Learning Lambda
  - Authentication Lambda
  - Product Management Lambdas
- **DynamoDB Tables**: users, products, campaigns, analytics, memory
- **S3 Bucket**: Product images and media assets
- **SQS Queue**: Campaign publishing queue with Dead Letter Queue
- **EventBridge Rule**: Scheduled trigger for analytics collection (every 6 hours)
- **CloudWatch Logs**: Centralized logging for all Lambdas

**Frontend Hosting**:
- React SPA hosted on S3 + CloudFront CDN
- CloudFront distribution with custom domain
- S3 bucket configured for static website hosting

**Infrastructure as Code**:
- AWS SAM (Serverless Application Model) templates
- CloudFormation for infrastructure provisioning
- Separate stacks for dev, staging, production

**Environment Configuration**:
- Lambda environment variables for configuration
- AWS Systems Manager Parameter Store for non-sensitive config
- AWS Secrets Manager for sensitive data (Instagram client secrets, JWT secrets)
- Separate configurations per environment

**Monitoring & Observability**:
- CloudWatch Logs for all Lambda executions
- CloudWatch Metrics for Lambda performance
- CloudWatch Alarms for error rates and throttling
- X-Ray for distributed tracing (optional)


## Future Enhancements

**Multi-Platform Support**:
- Extend to Facebook, Twitter, LinkedIn
- Platform-specific content optimization
- Cross-platform analytics

**Advanced AI Features**:
- Image generation for products without photos
- Video content generation
- A/B testing automation
- Sentiment analysis on comments

**Business Intelligence**:
- Competitor analysis
- Trend prediction
- Audience growth forecasting
- ROI optimization

**Scalability**:
- Multi-region deployment
- CDN for global content delivery
- Database sharding for large-scale users
- Caching layer for frequently accessed data
