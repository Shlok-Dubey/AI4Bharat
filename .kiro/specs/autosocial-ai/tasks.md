# Implementation Plan: PostPilot AI

## Overview

This implementation plan breaks down the PostPilot AI platform into discrete, incremental coding tasks. The platform is a serverless AWS application with AWS Lambda (Python 3.11) backend, React frontend, Amazon DynamoDB database, and AWS cloud services integration. FastAPI is used only for local development. Each task builds on previous work, with property-based tests and unit tests integrated throughout to validate correctness early.

## Tasks

- [x] 1. Project scaffolding and infrastructure setup
  - Create backend directory structure for Lambda functions (lambdas/orchestrator/, lambdas/agents/, lambdas/workers/, shared/models/, shared/schemas/, shared/services/, shared/utils/)
  - Create local development API structure (dev_api/main.py, dev_api/routes/) using FastAPI for testing
  - Create frontend directory structure (src/components/, pages/, services/, hooks/, auth/, utils/)
  - Create environment.example file with all required environment variables
  - Set up Python virtual environment and install dependencies (Boto3, Pydantic, PyJWT, Bcrypt, Cryptography, Hypothesis, pytest, FastAPI for local dev)
  - Set up React project with Vite and install dependencies (Axios, React Router)
  - Create .gitignore files for Python and Node.js
  - Create AWS SAM or Serverless Framework configuration for Lambda deployment
  - _Requirements: 13.1, 13.7, 15.1, 15.2_

- [x] 2. Database models and repository layer
  - [x] 2.1 Create DynamoDB connection manager
    - Implement async DynamoDB client using aioboto3
    - Add health check method for DynamoDB connectivity
    - Add graceful shutdown handling
    - _Requirements: 13.3, 17.6, 29.5_
  
  - [x] 2.2 Define Pydantic domain models
    - Create User, Product, Campaign, Analytics, Memory domain models as dataclasses
    - Include all fields from design document data models
    - Add helper methods (to_dynamodb_item, from_dynamodb_item)
    - _Requirements: 10.3_
  
  - [x] 2.3 Implement repository pattern for data access
    - Create UserRepository with methods: create, get_by_id, get_by_email, update, delete
    - Create ProductRepository with methods: create, get_by_id, get_by_user, update, soft_delete
    - Create CampaignRepository with methods: create, get_by_id, get_by_user, atomic_status_update, get_scheduled
    - Create AnalyticsRepository with methods: create, get_by_campaign, get_by_user_and_date_range
    - Create MemoryRepository with methods: get_memory, update_memory, increment_confidence
    - All repository methods should be async and use DynamoDB PK/SK patterns for tenant isolation
    - _Requirements: 10.1, 26.1, 26.2_
  
  - [ ]* 2.4 Write property test for tenant isolation
    - **Property 5: Tenant Isolation**
    - **Validates: Requirements 3.3, 3.4, 26.1, 26.3**


- [x] 3. Authentication and authorization
  - [x] 3.1 Implement password hashing service
    - Create hash_password function using bcrypt with cost factor 12
    - Create verify_password function for password verification
    - _Requirements: 1.1, 11.1_
  
  - [ ]* 3.2 Write property test for password hashing integrity
    - **Property 1: Password Hashing Integrity**
    - **Validates: Requirements 1.1, 11.1**
  
  - [x] 3.3 Implement JWT token service
    - Create generate_access_token function (60 min expiry)
    - Create generate_refresh_token function (7 days expiry)
    - Create verify_token function with expiry checking
    - Create decode_token function to extract user_id
    - Use HS256 algorithm with secret from environment
    - _Requirements: 1.2, 1.3, 1.4_
  
  - [ ]* 3.4 Write property test for JWT token generation and validation
    - **Property 2: JWT Token Generation and Validation**
    - **Validates: Requirements 1.2, 1.3, 1.4**
  
  - [x] 3.5 Create authentication middleware
    - Implement get_current_user dependency for FastAPI
    - Extract JWT from Authorization header
    - Validate token and return user_id
    - Raise 401 error for invalid/expired tokens
    - _Requirements: 1.3, 1.4_
  
  - [x] 3.6 Create authorization helpers
    - Implement check_resource_ownership function
    - Verify user can only access their own resources
    - Raise 403 error for unauthorized access
    - _Requirements: 1.5, 26.3_

- [x] 4. User registration and login endpoints
  - [x] 4.1 Create Pydantic request/response schemas
    - UserRegisterRequest with email and password validation
    - UserLoginRequest with email and password
    - TokenResponse with access_token and refresh_token
    - UserResponse with user details (no sensitive data)
    - _Requirements: 10.3_
  
  - [x] 4.2 Implement user registration endpoint
    - POST /api/v1/auth/register
    - Validate input with Pydantic
    - Check if email already exists
    - Hash password and create user in database
    - Generate JWT tokens
    - Return tokens and user data
    - _Requirements: 1.1, 1.2_
  
  - [x] 4.3 Implement user login endpoint
    - POST /api/v1/auth/login
    - Validate credentials
    - Verify password with bcrypt
    - Generate JWT tokens
    - Return tokens and user data
    - _Requirements: 1.2_
  
  - [x] 4.4 Implement token refresh endpoint
    - POST /api/v1/auth/refresh
    - Validate refresh token
    - Generate new access token
    - Return new access token
    - _Requirements: 1.2_
  
  - [x] 4.5 Write integration tests for auth endpoints
    - Test registration with valid/invalid data
    - Test login with valid/invalid credentials
    - Test token refresh
    - Test expired token rejection
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [-] 5. Encryption and token management service
  - [x] 5.1 Implement encryption service
    - Create get_encryption_key function to retrieve key from AWS Secrets Manager
    - Implement encrypt_token using AES-256-GCM
    - Implement decrypt_token with proper nonce and tag handling
    - Cache encryption key in Lambda memory for duration of execution
    - _Requirements: 2.3, 11.2, 25.1, 25.2_
  
  - [ ] 5.2 Write property test for encryption round-trip
    - **Property 25: Encryption Round-Trip**
    - **Validates: Requirements 25.1**
  
  - [ ]* 5.3 Write property test for sensitive data encryption
    - **Property 3: Sensitive Data Encryption**
    - **Validates: Requirements 2.3, 11.2, 25.1**

- [ ] 6. Instagram OAuth integration
  - [x] 6.1 Implement Instagram OAuth flow
    - Create GET /api/v1/instagram/authorize endpoint to redirect to Instagram
    - Create GET /api/v1/instagram/callback endpoint to handle OAuth callback
    - Exchange authorization code for access and refresh tokens
    - Encrypt tokens before storing
    - Store Instagram user metadata (username, user_id)
    - _Requirements: 2.1, 2.2, 2.3, 2.6_
  
  - [x] 6.2 Implement token refresh logic
    - Create refresh_instagram_token function
    - Call Instagram token refresh endpoint
    - Encrypt and update tokens in database
    - _Requirements: 2.4_
  
  - [ ] 6.3 Write property test for token refresh on expiry
    - **Property 4: Token Refresh on Expiry**
    - **Validates: Requirements 2.4**
  
  - [x] 6.4 Write unit tests for Instagram OAuth
    - Test authorization redirect
    - Test callback with valid code
    - Test token encryption
    - Test token refresh
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [x] 8. AWS service clients setup
  - [x] 8.1 Create S3 client wrapper
    - Initialize boto3 S3 client with async support (aioboto3)
    - Implement upload_file method with user_id/resource_type/file_id key structure
    - Implement generate_presigned_url method (5 min expiry)
    - Implement delete_file method
    - Configure bucket name from environment
    - _Requirements: 3.2, 13.4, 26.4_
  
  - [x] 8.2 Create SQS client wrapper
    - Initialize boto3 SQS client with async support
    - Implement send_message method with deduplication
    - Implement receive_messages method with long polling
    - Implement delete_message method
    - Implement change_message_visibility method
    - Configure queue URL from environment
    - _Requirements: 6.2, 9.1, 13.5_
  
  - [x] 8.3 Create Bedrock client wrapper
    - Initialize boto3 Bedrock Runtime client
    - Implement invoke_model method for Claude 3 Sonnet
    - Set timeouts (5s connection, 15s response)
    - Implement retry logic with exponential backoff (2s, 4s, 8s)
    - _Requirements: 5.1, 19.3, 30.2_
  
  - [x] 8.4 Create Rekognition client wrapper
    - Initialize boto3 Rekognition client
    - Implement detect_labels method (MinConfidence=75)
    - Implement detect_faces method
    - Implement detect_moderation_labels method
    - Set timeouts (5s connection, 10s response)
    - Implement retry logic with exponential backoff (1s, 2s, 4s)
    - _Requirements: 4.1, 4.4, 19.4, 30.3_
  
  - [x] 8.5 Create Secrets Manager client wrapper
    - Initialize boto3 Secrets Manager client
    - Implement get_secret method for encryption key retrieval
    - Cache secrets in memory with 1-hour expiry
    - _Requirements: 25.2_

- [x] 9. Image analysis service
  - [x] 9.1 Implement image analysis algorithm
    - Create analyze_image method that takes image bytes
    - Call Rekognition DetectLabels and filter by confidence >= 75
    - Sort labels by confidence and take top 5
    - Call DetectFaces to check for human presence
    - Call DetectModerationLabels to check content safety
    - Extract dominant colors from label metadata
    - Return ImageAnalysis object with all fields
    - _Requirements: 4.1, 4.2, 4.4_
  
  - [ ]* 9.2 Write property test for image analysis structure
    - **Property 6: Image Analysis Structure**
    - **Validates: Requirements 4.4**
  
  - [ ]* 9.3 Write unit tests for image analysis
    - Test with mocked Rekognition responses
    - Test label filtering and sorting
    - Test face detection
    - Test content safety checking
    - Test error handling when Rekognition fails
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 10. Product management endpoints
  - [x] 10.1 Create product schemas
    - ProductCreateRequest with name, description validation
    - ProductUpdateRequest with optional fields
    - ProductResponse with all product fields
    - _Requirements: 3.1, 10.3_
  
  - [x] 10.2 Implement product creation endpoint
    - POST /api/v1/products with multipart/form-data
    - Validate image file (JPEG/PNG, max 10MB)
    - Upload image to S3                       
    - Analyze image with Rekognition
    - Create product in database with user_id association
    - Return product with image_url and analysis
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [x] 10.3 Implement product listing endpoint
    - GET /api/v1/products
    - Filter by authenticated user_id
    - Exclude soft-deleted products
    - Support pagination
    - Return list of products
    - _Requirements: 3.4_
  
  - [x] 10.4 Implement product update endpoint
    - PUT /api/v1/products/{id}
    - Verify ownership
    - Validate changes
    - Update database record
    - _Requirements: 3.5_
  
  - [x] 10.5 Implement product deletion endpoint
    - DELETE /api/v1/products/{id}
    - Verify ownership
    - Soft-delete by setting deleted_at timestamp
    - Keep record in database
    - _Requirements: 3.6, 24.3_
  
  - [ ]* 10.6 Write property test for soft delete behavior
    - **Property 20: Soft Delete Behavior**
    - **Validates: Requirements 24.3**
  
  - [ ]* 10.7 Write integration tests for product endpoints
    - Test product creation with image upload
    - Test product listing returns only user's products
    - Test product update
    - Test product deletion (soft delete)
    - Test unauthorized access attempts
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 11. Campaign generation service
  - [x] 11.1 Implement hashtag generation algorithm
    - Create generate_hashtags function
    - Convert suggested hashtags to lowercase, remove spaces, prefix with #
    - Add label-based hashtags from top 3 product labels
    - Add fixed brand hashtags (#smallbusiness, #shoponline, #supportlocal)
    - Remove duplicates (case-insensitive)
    - Limit to 10 total hashtags
    - _Requirements: 5.2_
  
  - [ ]* 11.2 Write property test for hashtag generation algorithm
    - **Property 24: Hashtag Generation Algorithm**
    - **Validates: Requirements 5.2_
  
  - [x] 11.3 Implement Business Profiling Lambda
    - Create Lambda handler for business profiling
    - Retrieve business context from DynamoDB Memory table
    - Call Bedrock to reason about business identity
    - Return business profile
    - _Requirements: 5.1, 5.2_
  
  - [x] 11.4 Implement Campaign Strategy Lambda
    - Create Lambda handler for campaign strategy
    - Receive business profile and product details
    - Retrieve past performance from DynamoDB Memory
    - Call Bedrock to decide optimal strategy
    - Return strategy (tone, CTA, hook pattern)
    - _Requirements: 5.1, 5.2_
  
  - [x] 11.5 Implement Content Generation Lambda
    - Create Lambda handler for content generation
    - Receive strategy and product details
    - Retrieve best-performing patterns from DynamoDB Memory
    - Call Bedrock to generate caption and hashtags
    - Apply hashtag generation algorithm
    - Return generated content
    - _Requirements: 5.1, 5.2_
  
  - [x] 11.6 Implement Scheduling Intelligence Lambda
    - Create Lambda handler for scheduling intelligence
    - Retrieve engagement patterns from DynamoDB Memory
    - Call Bedrock to determine optimal posting time
    - Return scheduling recommendation
    - _Requirements: 5.2_
  
  - [x] 11.7 Implement Agent Orchestrator Lambda
    - Create Lambda handler for orchestration
    - Invoke Business Profiling Lambda
    - Invoke Campaign Strategy Lambda with profile
    - Invoke Content Generation Lambda with strategy
    - Invoke Scheduling Intelligence Lambda
    - Aggregate all agent outputs
    - Store campaign in DynamoDB with status "draft"
    - Store bedrock_model_version and prompt_template_version
    - Return complete campaign
    - _Requirements: 5.1, 5.2, 5.3, 5.6_
  
  - [ ]* 11.8 Write property test for campaign generation structure
    - **Property 7: Campaign Generation Structure**
    - **Validates: Requirements 5.2, 5.3**
  
  - [ ]* 11.9 Write unit tests for campaign generation
    - Test with mocked Bedrock responses
    - Test hashtag generation
    - Test agent orchestration
    - Test error handling when Bedrock fails
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 13. Rate limiting and quota management
  - [ ] 13.1 Implement token bucket rate limiting
    - Create check_rate_limit function with DynamoDB-backed storage
    - Implement token bucket algorithm (100 tokens, refill 100/min)
    - Calculate refill based on elapsed time
    - Update bucket atomically using DynamoDB conditional writes
    - Return allowed status and rate limit headers
    - _Requirements: 20.1, 20.2_
  
  - [ ] 13.2 Create rate limiting middleware for local dev API
    - Apply to all /api/v1/ endpoints in FastAPI dev server
    - Extract user_id from JWT
    - Call check_rate_limit
    - Return 429 with retry-after header if exceeded
    - Add rate limit headers to all responses
    - _Requirements: 11.4, 20.1, 20.2_
  
  - [ ]* 13.3 Write property test for rate limiting enforcement
    - **Property 16: Rate Limiting Enforcement**
    - **Validates: Requirements 20.1**
  
  - [ ] 13.4 Implement daily campaign quota management
    - Create check_and_increment_quota function
    - Check if quota_reset_date is today, reset if not
    - Check if campaigns_generated_today < daily_campaign_quota
    - Increment counter using DynamoDB atomic counter
    - Return quota status
    - _Requirements: 20.3, 20.4_
  
  - [ ]* 13.5 Write property test for daily quota enforcement
    - **Property 17: Daily Campaign Quota Enforcement**
    - **Validates: Requirements 20.3**
  
  - [ ]* 13.6 Write unit tests for rate limiting and quota
    - Test token bucket refill calculation
    - Test rate limit enforcement
    - Test quota reset at midnight UTC
    - Test quota enforcement
    - _Requirements: 20.1, 20.2, 20.3, 20.4_

- [x] 14. Campaign scheduling service
  - [x] 14.1 Implement campaign scheduling
    - Create schedule_campaign method in SchedulerService
    - Calculate delay_seconds from scheduled_time
    - If delay > 900s (15 min), set delay to 0 (worker will check time)
    - Create SQS message with campaign_id and scheduled_time
    - Use message deduplication with campaign_id
    - Send message to queue
    - _Requirements: 6.2_
  
  - [x] 14.2 Implement campaign scheduling endpoint
    - POST /api/v1/campaigns/{id}/schedule
    - Validate scheduled_time is in future and within 90 days
    - Verify campaign ownership
    - Update campaign status to "scheduled"
    - Call scheduler service to add to queue
    - Return updated campaign
    - _Requirements: 6.1, 6.2, 6.6_
  
  - [ ]* 14.3 Write property test for future timestamp validation
    - **Property 8: Future Timestamp Validation**
    - **Validates: Requirements 6.1**
  
  - [ ]* 14.4 Write property test for queue message creation
    - **Property 9: Queue Message Creation**
    - **Validates: Requirements 6.2**
  
  - [x] 14.5 Implement campaign cancellation endpoint
    - POST /api/v1/campaigns/{id}/cancel
    - Verify campaign ownership
    - Update campaign status to "cancelled"
    - Attempt to remove message from queue (best effort)
    - _Requirements: 6.5_
  
  - [ ]* 14.6 Write integration tests for scheduling
    - Test scheduling with valid future time
    - Test scheduling with past time (should fail)
    - Test scheduling beyond 90 days (should fail)
    - Test queue message creation
    - Test campaign cancellation
    - _Requirements: 6.1, 6.2, 6.5, 6.6_

- [x] 15. Instagram publishing service
  - [x] 15.1 Implement Instagram publishing with retry
    - Create publish_post method in InstagramService
    - Retrieve and decrypt Instagram token
    - Check token expiry, refresh if needed
    - Generate S3 presigned URL for image
    - Create Instagram media container via Graph API
    - Poll container status (max 30 seconds, 5s intervals)
    - Publish container to Instagram feed
    - Return Instagram post_id
    - Implement retry logic for 5xx errors (1s, 2s, 4s backoff)
    - Implement retry-after handling for 429 errors
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 19.1, 19.2, 30.1_
  
  - [ ]* 15.2 Write property test for retry with exponential backoff
    - **Property 12: Retry with Exponential Backoff**
    - **Validates: Requirements 9.3, 9.5, 19.1, 19.3, 19.4**
  
  - [ ]* 15.3 Write property test for rate limit retry-after handling
    - **Property 13: Rate Limit Retry-After Handling**
    - **Validates: Requirements 19.2**
  
  - [ ]* 15.4 Write property test for backoff jitter
    - **Property 14: Backoff Jitter**
    - **Validates: Requirements 19.6**
  
  - [x] 15.5 Implement idempotency checking for publishing
    - Create publish_with_idempotency_check method
    - Check if campaign already has instagram_post_id
    - If yes, verify post exists on Instagram
    - If exists, return existing post_id
    - If not exists, proceed with publishing
    - _Requirements: 18.1, 18.3_
  
  - [ ]* 15.6 Write property test for publishing idempotency
    - **Property 10: Campaign Publishing Idempotency**
    - **Validates: Requirements 7.6, 18.1, 18.2, 18.5**
  
  - [ ]* 15.7 Write unit tests for Instagram publishing
    - Test with mocked Instagram API
    - Test token refresh on expiry
    - Test retry on 5xx errors
    - Test retry-after on 429 errors
    - Test idempotency (duplicate publish attempts)
    - Test error handling
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 16. Worker Lambda for campaign publishing
  - [x] 16.1 Implement Publishing Worker Lambda handler
    - Create Lambda handler triggered by SQS
    - Parse message body for campaign_id and scheduled_time
    - Check if scheduled_time <= current_time
    - If not ready, return (message will be retried)
    - Atomically update campaign status: scheduled → publishing using DynamoDB conditional update
    - If update fails (already processed), return success
    - Retrieve campaign from DynamoDB
    - Call Instagram service to publish
    - On success: Update status to "published", store post_id in DynamoDB
    - On failure: Increment publish_attempts
    - If attempts >= 3: Update status to "failed"
    - If attempts < 3: Update status to "scheduled", raise exception for SQS retry
    - _Requirements: 6.3, 7.1, 7.5, 9.2, 9.3, 9.4, 18.2_
  
  - [x] 16.2 Configure SQS dead-letter queue
    - Configure SQS dead-letter queue in infrastructure
    - Set maxReceiveCount to 3
    - Log failure reason, retry count, and payload to CloudWatch
    - _Requirements: 9.5, 21.1, 21.2, 21.3_
  
  - [ ]* 16.3 Write integration tests for worker Lambda
    - Test message processing with scheduled campaign
    - Test atomic status update
    - Test retry logic
    - Test dead-letter queue placement
    - _Requirements: 6.3, 9.2, 9.3, 9.4, 9.5_

- [ ] 17. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [x] 18. Analytics service and endpoints
  - [x] 18.1 Implement Instagram insights fetching
    - Create fetch_insights method in InstagramService
    - Call Instagram Graph API /{post_id}/insights
    - Request metrics: likes, comments, reach, impressions
    - Calculate engagement_rate: (likes + comments) / reach
    - Return InstagramInsights object
    - _Requirements: 8.1_
  
  - [x] 18.2 Implement analytics aggregation
    - Create get_analytics_summary method in AnalyticsService
    - Query DynamoDB analytics table for user's campaigns in date range
    - Calculate totals: sum of likes, comments, reach, impressions
    - Calculate averages: mean engagement_rate
    - Calculate trends: compare to previous period
    - Identify top performing campaigns
    - Return AnalyticsSummary object
    - _Requirements: 8.3_
  
  - [x] 18.3 Implement analytics storage
    - Create store_analytics method
    - Associate metrics with campaign_id and timestamp
    - Store in DynamoDB analytics table
    - _Requirements: 8.2_
  
  - [ ]* 18.4 Write property test for analytics association
    - **Property 11: Analytics Association**
    - **Validates: Requirements 8.2**
  
  - [x] 18.5 Implement analytics endpoints for local dev API
    - GET /api/v1/analytics?start_date=&end_date=
    - Verify user authentication
    - Call analytics service to aggregate data
    - Return summary statistics
    - _Requirements: 8.3_
  
  - [x] 18.6 Implement Analytics Collector Lambda
    - Create Lambda handler triggered by EventBridge (every 6 hours)
    - Query DynamoDB for published campaigns with last_analytics_fetch > 24h ago
    - For each campaign, fetch insights from Instagram
    - Store analytics in DynamoDB
    - Update campaign.last_analytics_fetch timestamp
    - _Requirements: 8.1, 8.4_
  
  - [x] 18.7 Implement Performance Learning Lambda
    - Create Lambda handler invoked by Analytics Collector
    - Retrieve campaign metadata and metrics from DynamoDB
    - Call Bedrock to reason over performance data
    - Identify success patterns and insights
    - Update DynamoDB Memory table with learned patterns
    - Increase confidence scores with more data
    - _Requirements: 8.1, 8.4_
  
  - [ ]* 18.8 Write integration tests for analytics
    - Test insights fetching with mocked Instagram API
    - Test analytics storage
    - Test analytics aggregation
    - Test analytics endpoint
    - _Requirements: 8.1, 8.2, 8.3, 8.6_

- [ ] 19. Campaign management endpoints for local dev API
  - [ ] 19.1 Create campaign schemas
    - CampaignGenerateRequest with product_id, tone, idempotency_key
    - CampaignScheduleRequest with scheduled_time validation
    - CampaignResponse with all campaign fields
    - _Requirements: 10.3_
  
  - [ ] 19.2 Implement campaign generation endpoint
    - POST /api/v1/campaigns/generate
    - Check daily quota with check_and_increment_quota
    - Validate input with Pydantic
    - Invoke Agent Orchestrator Lambda
    - Return generated campaign
    - _Requirements: 5.1, 5.2, 5.3, 20.3_
  
  - [ ] 19.3 Implement campaign listing endpoint
    - GET /api/v1/campaigns
    - Filter by authenticated user_id
    - Support filtering by status
    - Support pagination
    - Return list of campaigns
    - _Requirements: 26.1_
  
  - [ ] 19.4 Implement campaign detail endpoint
    - GET /api/v1/campaigns/{id}
    - Verify ownership
    - Return campaign details
    - _Requirements: 26.3_
  
  - [ ]* 19.5 Write integration tests for campaign endpoints
    - Test campaign generation with quota enforcement
    - Test campaign listing returns only user's campaigns
    - Test campaign detail with ownership verification
    - Test unauthorized access attempts
    - _Requirements: 5.1, 5.2, 5.3, 20.3, 26.1, 26.3_

- [ ] 20. Error handling and logging
  - [ ] 20.1 Create exception hierarchy
    - Define PostPilotError base exception
    - Define ValidationError, AuthenticationError, AuthorizationError
    - Define ResourceNotFoundError, RateLimitError, QuotaExceededError
    - Define ExternalServiceError, InstagramPublishError, BedrockError, RekognitionError
    - _Requirements: 10.5, 14.1, 14.2_
  
  - [ ] 20.2 Implement error handling middleware for local dev API
    - Create exception handlers for each error type
    - Map exceptions to HTTP status codes
    - Return standardized error responses
    - Include trace_id in error responses
    - Add retry-after headers for rate limit errors
    - _Requirements: 10.5, 14.1, 14.5_
  
  - [ ] 20.3 Implement structured logging for Lambda functions
    - Configure logging with JSON formatter
    - Include timestamp, level, service, trace_id, message
    - Log all Lambda invocations (function name, request_id, duration)
    - Log authentication attempts
    - Log external API calls
    - Log SQS message processing
    - Never log sensitive data (passwords, tokens, keys)
    - _Requirements: 11.6, 14.1, 14.2, 14.3, 14.4, 14.6, 22.1_
  
  - [ ]* 20.4 Write property test for structured logging format
    - **Property 18: Structured Logging Format**
    - **Validates: Requirements 22.1, 11.6**
  
  - [ ] 20.5 Implement trace ID for Lambda functions
    - Use AWS request_id as trace_id
    - Propagate to all service calls
    - Include in all log entries
    - Include in error responses
    - _Requirements: 22.5_
  
  - [ ]* 20.6 Write property test for trace ID propagation
    - **Property 19: Trace ID Propagation**
    - **Validates: Requirements 22.5**

- [ ] 21. Circuit breaker implementation
  - [ ] 21.1 Implement circuit breaker pattern
    - Create CircuitBreaker class with states: closed, open, half-open
    - Track consecutive failures per external service
    - Open circuit after 5 consecutive failures
    - Return fast-fail errors when open (60 seconds)
    - Allow one test request in half-open state
    - Close circuit if test succeeds
    - _Requirements: 17.7, 30.5, 30.6, 30.7_
  
  - [ ] 21.2 Apply circuit breakers to external services
    - Wrap Instagram API calls with circuit breaker
    - Wrap Bedrock API calls with circuit breaker
    - Wrap Rekognition API calls with circuit breaker
    - _Requirements: 17.7_
  
  - [ ]* 21.3 Write property test for circuit breaker behavior
    - **Property 23: Circuit Breaker Behavior**
    - **Validates: Requirements 30.5, 30.6, 30.7**
  
  - [ ]* 21.4 Write unit tests for circuit breaker
    - Test circuit opens after 5 failures
    - Test fast-fail when open
    - Test half-open state
    - Test circuit closes on success
    - _Requirements: 17.7, 30.5, 30.6, 30.7_

- [ ] 22. Timeout configuration
  - [ ] 22.1 Configure HTTP client timeouts
    - Set Instagram API timeouts (10s connection, 30s response)
    - Set Bedrock timeouts (5s connection, 15s response)
    - Set Rekognition timeouts (5s connection, 10s response)
    - Raise timeout exceptions when exceeded
    - _Requirements: 30.1, 30.2, 30.3, 30.4_
  
  - [ ]* 22.2 Write property test for timeout configuration
    - **Property 22: Timeout Configuration**
    - **Validates: Requirements 30.1, 30.2, 30.3**

- [ ] 23. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 24. Input validation and security
  - [ ] 24.1 Implement input validation with Pydantic
    - Add field validators for all request schemas
    - Validate email format, password strength
    - Validate file types and sizes
    - Validate date ranges
    - Validate string lengths
    - _Requirements: 10.3, 11.3_
  
  - [ ]* 24.2 Write property test for input validation
    - **Property 15: Input Validation with Pydantic**
    - **Validates: Requirements 10.3, 11.3**
  
  - [ ] 24.3 Implement input sanitization
    - Sanitize user inputs to prevent injection attacks
    - Escape special characters in MongoDB queries
    - Validate and sanitize file uploads
    - _Requirements: 11.3_
  
  - [ ]* 24.4 Write security tests
    - Test MongoDB injection attempts
    - Test XSS attempts
    - Test file upload with malicious files
    - Test authentication bypass attempts
    - Test authorization bypass attempts
    - _Requirements: 11.3, 28.7_

- [ ] 25. Health check endpoints for local dev API
  - [ ] 25.1 Implement health check endpoints
    - GET /health/liveness - Always return 200 if service is running
    - GET /health/readiness - Return 200 if DynamoDB is connected, 503 otherwise
    - Check DynamoDB connectivity
    - Return status within 100ms
    - _Requirements: 17.3, 17.4, 22.3, 22.4_
  
  - [ ]* 25.2 Write tests for health checks
    - Test liveness endpoint
    - Test readiness with DynamoDB connected
    - Test readiness with DynamoDB disconnected
    - _Requirements: 17.3, 22.3, 22.4_

- [ ] 26. Data export endpoint
  - [ ] 26.1 Implement data export functionality
    - GET /api/v1/users/me/export
    - Verify user authentication
    - Query all user's products, campaigns, analytics
    - Format as JSON
    - Return complete data export
    - _Requirements: 24.5_
  
  - [ ]* 26.2 Write property test for data export completeness
    - **Property 21: Data Export Completeness**
    - **Validates: Requirements 24.5**
  
  - [ ]* 26.3 Write integration test for data export
    - Create user with products, campaigns, analytics
    - Export data
    - Verify all records are included
    - _Requirements: 24.5_

- [ ] 27. API versioning
  - [ ] 27.1 Implement API versioning
    - Prefix all routes with /api/v1/
    - Create router structure for versioning
    - Document versioning strategy
    - _Requirements: 27.1_
  
  - [ ] 27.2 Add deprecation warning headers
    - Implement middleware to add deprecation headers
    - Configure for future API versions
    - _Requirements: 27.5_

  - [x] 28. Frontend React application
  - [x] 28.1 Create authentication context and hooks
    - Implement AuthContext with user state and token management
    - Create useAuth hook
    - Store tokens in localStorage
    - Implement login, logout, refreshToken functions
    - _Requirements: 1.2, 1.6, 12.3_
  
  - [x] 28.2 Create API client service
    - Implement Axios instance with base URL
    - Add request interceptor to include JWT token
    - Add response interceptor to handle 401 and refresh token
    - Implement methods for all API endpoints
    - _Requirements: 12.3, 12.4_
  
  - [x] 28.3 Create authentication pages
    - Login page with email/password form
    - Registration page with email/password form
    - Implement form validation
    - Handle authentication errors
    - Redirect to dashboard on success
    - _Requirements: 12.1, 12.6_
  
  - [x] 28.4 Create dashboard layout
    - Navigation bar with links to products, campaigns, analytics
    - Protected routes requiring authentication
    - Logout button
    - _Requirements: 12.2, 12.7_
  
  - [x] 28.5 Create product management pages
    - Product list page with grid/list view
    - Product upload form with image preview
    - Product edit form
    - Product delete confirmation
    - Display loading states
    - Handle errors with user-friendly messages
    - _Requirements: 12.5, 12.6_
  
  - [x] 28.6 Create campaign management pages
    - Campaign list page with filters (status)
    - Campaign generation form (select product, choose tone)
    - Campaign detail view with caption, hashtags, image
    - Campaign scheduling form with date/time picker
    - Display loading states
    - Handle quota exceeded errors
    - _Requirements: 12.5, 12.6_
  
  - [x] 28.7 Create analytics dashboard
    - Display summary statistics (total likes, comments, reach, impressions)
    - Display engagement rate
    - Display trends with charts
    - Display top performing campaigns
    - Date range selector
    - _Requirements: 8.5_
  
  - [x] 28.8 Create Instagram connection flow
    - Instagram connect button
    - Handle OAuth redirect
    - Display connection status
    - _Requirements: 2.1_

- [ ] 29. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [x] 30. AWS Lambda deployment configuration
  - [x] 30.1 Create Lambda deployment package structure
    - Create requirements.txt for Lambda layers (Boto3, Pydantic, PyJWT, Bcrypt, Cryptography)
    - Create layer for shared dependencies
    - Create deployment packages for each Lambda function
    - _Requirements: 13.1_
  
  - [x] 30.2 Create SAM or Serverless Framework template
    - Define all Lambda functions (Orchestrator, Agents, Workers, Analytics)
    - Define API Gateway integration
    - Define DynamoDB tables with PK/SK structure
    - Define S3 buckets
    - Define SQS queues with DLQ
    - Define EventBridge rules for scheduled tasks
    - Define IAM roles with least-privilege permissions
    - _Requirements: 13.1, 13.2_
  
  - [x] 30.3 Configure Lambda function settings
    - Set Python 3.11 runtime
    - Configure memory and timeout per function
    - Configure environment variables
    - Configure VPC settings if needed
    - Configure reserved concurrency for critical functions
    - _Requirements: 13.2_
  
  - [x] 30.4 Create environment configuration files
    - Create .env.example with all required variables
    - Document each variable
    - Create separate configs for dev, staging, prod
    - _Requirements: 15.1, 15.2, 15.6_
  
  - [x] 30.5 Configure CloudWatch logging
    - Set up log groups for each Lambda function
    - Configure log retention (30 days)
    - Set up log streams
    - _Requirements: 13.6, 14.1_
  
  - [x] 30.6 Configure CloudWatch alarms
    - Create alarm for Lambda error rate > 5%
    - Create alarm for SQS queue depth > 1000
    - Create alarm for Lambda duration approaching timeout
    - Create alarm for publish failure rate > 10%
    - Configure SNS notifications
    - _Requirements: 22.6, 22.7_
  
  - [x] 30.7 Create local development setup with FastAPI
    - Create dev_api/main.py with FastAPI app
    - Implement all API endpoints for local testing
    - Configure to invoke Lambda functions locally or use direct service calls
    - Create docker-compose.yml for local DynamoDB (DynamoDB Local)
    - _Requirements: 13.7_

- [ ] 31. Database indexes and optimization
  - [ ] 31.1 Create DynamoDB table definitions
    - users table: PK=USER#{user_id}, unique email GSI, sparse instagram_user_id GSI
    - products table: PK=USER#{user_id}, SK=PRODUCT#{product_id}, sparse deleted_at GSI
    - campaigns table: PK=USER#{user_id}, SK=CAMPAIGN#{campaign_id}, GSI for status+scheduled_time queries, unique idempotency_key GSI, sparse instagram_post_id GSI
    - analytics table: PK=CAMPAIGN#{campaign_id}, SK=ANALYTICS#{timestamp}, GSI for user_id+fetched_at queries
    - memory table: PK=USER#{user_id}, SK=MEMORY#{memory_type}
    - rate_limits table: PK=USER#{user_id}, SK=RATE_LIMIT#{resource}, TTL on expires_at
    - _Requirements: 26.2, 29.7_
  
  - [ ] 31.2 Configure DynamoDB capacity settings
    - Set appropriate read/write capacity or use on-demand billing
    - Configure auto-scaling if using provisioned capacity
    - Configure point-in-time recovery
    - _Requirements: 29.5_

- [ ] 32. Configuration validation and startup checks
  - [ ] 32.1 Implement configuration validation
    - Create validate_config function
    - Check all required environment variables are set
    - Validate format of URLs, keys, etc.
    - Fail fast on startup if config is invalid
    - _Requirements: 15.3_
  
  - [ ] 32.2 Implement startup health checks
    - Check DynamoDB connectivity on Lambda cold start
    - Check AWS service connectivity (S3, SQS, Secrets Manager)
    - Log startup status to CloudWatch
    - _Requirements: 17.3_

- [ ] 33. Documentation
  - [ ] 33.1 Create comprehensive README.md
    - System architecture explanation (AWS serverless)
    - AI workflow (multi-agent Lambda architecture with Bedrock)
    - Campaign Intelligence Memory (DynamoDB-backed learning)
    - Instagram integration flow
    - Token lifecycle management
    - Campaign generation pipeline (agent orchestration)
    - Scheduling & Lambda worker logic
    - DynamoDB schema overview (PK/SK patterns)
    - Deployment guide (AWS SAM/Serverless Framework + Lambda)
    - Environment variables list
    - Security considerations
    - Future improvements
    - Scalability plan
    - _Requirements: 15.6_
  
  - [ ] 33.2 Create development_rules.md
    - Follow clean architecture principles
    - Use async IO wherever possible
    - No business logic in Lambda handlers
    - Use service layer
    - Environment variables only
    - No hardcoded secrets
    - Type hints everywhere
    - Clear docstrings
    - Separate Lambda functions by responsibility
    - _Requirements: 10.1, 10.2, 10.6, 11.7_
  
  - [ ] 33.3 Create API documentation
    - Document all endpoints with OpenAPI/Swagger
    - Include request/response examples
    - Document error codes
    - Document rate limits and quotas
    - _Requirements: 27.4_
  
  - [ ] 33.4 Create architecture.md
    - Document serverless system architecture with diagrams
    - Document Lambda invocation patterns
    - Document DynamoDB data models and access patterns
    - Document AI agent workflow
    - Document algorithms
    - _Requirements: 15.6_

- [ ] 34. Final integration and end-to-end testing
  - [ ]* 34.1 Write end-to-end test for complete user flow
    - Register user
    - Login
    - Connect Instagram (mocked)
    - Upload product
    - Generate campaign (invoke Orchestrator Lambda)
    - Schedule campaign
    - Lambda worker processes and publishes (mocked Instagram)
    - Fetch analytics
    - _Requirements: 28.5_
  
  - [ ]* 34.2 Write end-to-end test for rate limiting
    - Make 101 requests in 60 seconds
    - Verify 101st request is rate limited
    - Wait for rate limit reset
    - Verify subsequent request succeeds
    - _Requirements: 20.1, 28.5_
  
  - [ ]* 34.3 Write end-to-end test for quota enforcement
    - Generate 51 campaigns in one day
    - Verify 51st request is quota limited
    - _Requirements: 20.3, 28.5_

- [ ] 35. Final checkpoint - Ensure all tests pass
  - Run full test suite (unit, integration, property-based, E2E)
  - Verify 80% code coverage minimum
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based and unit tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties with minimum 100 iterations
- Unit tests validate specific examples and edge cases with mocked dependencies
- Integration tests validate API endpoints with mocked external services and local DynamoDB
- End-to-end tests validate complete user flows
- All external services (Instagram, Bedrock, Rekognition, S3, SQS) should be mocked in tests
- Use Hypothesis for property-based testing in Python
- Use pytest with pytest-asyncio for async test support
- Use httpx-mock or responses for mocking HTTP calls
- Use moto for mocking AWS services
- Follow clean architecture: Lambda handlers → services → repositories → DynamoDB
- No business logic in Lambda handlers
- All service methods should be async
- Include comprehensive docstrings and type hints
- Never log sensitive data (passwords, tokens, API keys)
- Always validate user ownership before allowing resource access
- Use environment variables for all configuration
- Fail fast on Lambda cold start if required config is missing
- FastAPI is used ONLY for local development and testing, NOT for production deployment
- Production deployment uses AWS Lambda + API Gateway

