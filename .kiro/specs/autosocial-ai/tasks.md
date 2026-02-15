# Implementation Plan: PostPilot AI

## Overview

This implementation plan breaks down the PostPilot AI platform into discrete, incremental coding tasks. The platform is a production-ready SaaS application with Python FastAPI backend, React frontend, MongoDB database, and AWS cloud services integration. Each task builds on previous work, with property-based tests and unit tests integrated throughout to validate correctness early.

## Tasks

- [ ] 1. Project scaffolding and infrastructure setup
  - Create backend directory structure (main.py, config/, models/, schemas/, routes/, services/, repositories/, workers/, utils/)
  - Create frontend directory structure (src/components/, pages/, services/, hooks/, auth/, utils/)
  - Set up Docker configuration (Dockerfile for API service, Dockerfile for worker service, docker-compose.yml)
  - Create environment.example file with all required environment variables
  - Set up Python virtual environment and install dependencies (FastAPI, Motor, Pydantic, Boto3, PyJWT, Bcrypt, Cryptography, Hypothesis, pytest)
  - Set up React project with Vite and install dependencies (Axios, React Router)
  - Create .gitignore files for Python and Node.js
  - _Requirements: 13.1, 13.7, 15.1, 15.2_

- [ ] 2. Database models and repository layer
  - [ ] 2.1 Create MongoDB connection manager
    - Implement async MongoDB client with connection pooling
    - Add health check method for database connectivity
    - Add graceful shutdown handling
    - _Requirements: 13.3, 17.6, 29.5_
  
  - [ ] 2.2 Define Pydantic domain models
    - Create User, Product, Campaign, Analytics, RateLimit domain models as dataclasses
    - Include all fields from design document data models
    - Add helper methods (to_document, from_document)
    - _Requirements: 10.3_
  
  - [ ] 2.3 Implement repository pattern for data access
    - Create UserRepository with methods: create, get_by_id, get_by_email, update, delete
    - Create ProductRepository with methods: create, get_by_id, get_by_user, update, soft_delete
    - Create CampaignRepository with methods: create, get_by_id, get_by_user, atomic_status_update, get_scheduled
    - Create AnalyticsRepository with methods: create, get_by_campaign, get_by_user_and_date_range
    - All repository methods should be async and include user_id filtering for tenant isolation
    - _Requirements: 10.1, 26.1, 26.2_
  
  - [ ]* 2.4 Write property test for tenant isolation
    - **Property 5: Tenant Isolation**
    - **Validates: Requirements 3.3, 3.4, 26.1, 26.3**


- [ ] 3. Authentication and authorization
  - [ ] 3.1 Implement password hashing service
    - Create hash_password function using bcrypt with cost factor 12
    - Create verify_password function for password verification
    - _Requirements: 1.1, 11.1_
  
  - [ ]* 3.2 Write property test for password hashing integrity
    - **Property 1: Password Hashing Integrity**
    - **Validates: Requirements 1.1, 11.1**
  
  - [ ] 3.3 Implement JWT token service
    - Create generate_access_token function (60 min expiry)
    - Create generate_refresh_token function (7 days expiry)
    - Create verify_token function with expiry checking
    - Create decode_token function to extract user_id
    - Use HS256 algorithm with secret from environment
    - _Requirements: 1.2, 1.3, 1.4_
  
  - [ ]* 3.4 Write property test for JWT token generation and validation
    - **Property 2: JWT Token Generation and Validation**
    - **Validates: Requirements 1.2, 1.3, 1.4**
  
  - [ ] 3.5 Create authentication middleware
    - Implement get_current_user dependency for FastAPI
    - Extract JWT from Authorization header
    - Validate token and return user_id
    - Raise 401 error for invalid/expired tokens
    - _Requirements: 1.3, 1.4_
  
  - [ ] 3.6 Create authorization helpers
    - Implement check_resource_ownership function
    - Verify user can only access their own resources
    - Raise 403 error for unauthorized access
    - _Requirements: 1.5, 26.3_

- [ ] 4. User registration and login endpoints
  - [ ] 4.1 Create Pydantic request/response schemas
    - UserRegisterRequest with email and password validation
    - UserLoginRequest with email and password
    - TokenResponse with access_token and refresh_token
    - UserResponse with user details (no sensitive data)
    - _Requirements: 10.3_
  
  - [ ] 4.2 Implement user registration endpoint
    - POST /api/v1/auth/register
    - Validate input with Pydantic
    - Check if email already exists
    - Hash password and create user in database
    - Generate JWT tokens
    - Return tokens and user data
    - _Requirements: 1.1, 1.2_
  
  - [ ] 4.3 Implement user login endpoint
    - POST /api/v1/auth/login
    - Validate credentials
    - Verify password with bcrypt
    - Generate JWT tokens
    - Return tokens and user data
    - _Requirements: 1.2_
  
  - [ ] 4.4 Implement token refresh endpoint
    - POST /api/v1/auth/refresh
    - Validate refresh token
    - Generate new access token
    - Return new access token
    - _Requirements: 1.2_
  
  - [ ]* 4.5 Write integration tests for auth endpoints
    - Test registration with valid/invalid data
    - Test login with valid/invalid credentials
    - Test token refresh
    - Test expired token rejection
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 5. Encryption and token management service
  - [ ] 5.1 Implement encryption service
    - Create get_encryption_key function to retrieve key from AWS Secrets Manager
    - Implement encrypt_token using AES-256-GCM
    - Implement decrypt_token with proper nonce and tag handling
    - Cache encryption key in memory for 1 hour
    - _Requirements: 2.3, 11.2, 25.1, 25.2_
  
  - [ ]* 5.2 Write property test for encryption round-trip
    - **Property 25: Encryption Round-Trip**
    - **Validates: Requirements 25.1**
  
  - [ ]* 5.3 Write property test for sensitive data encryption
    - **Property 3: Sensitive Data Encryption**
    - **Validates: Requirements 2.3, 11.2, 25.1**

- [ ] 6. Instagram OAuth integration
  - [ ] 6.1 Implement Instagram OAuth flow
    - Create GET /api/v1/instagram/authorize endpoint to redirect to Instagram
    - Create GET /api/v1/instagram/callback endpoint to handle OAuth callback
    - Exchange authorization code for access and refresh tokens
    - Encrypt tokens before storing
    - Store Instagram user metadata (username, user_id)
    - _Requirements: 2.1, 2.2, 2.3, 2.6_
  
  - [ ] 6.2 Implement token refresh logic
    - Create refresh_instagram_token function
    - Call Instagram token refresh endpoint
    - Encrypt and update tokens in database
    - _Requirements: 2.4_
  
  - [ ]* 6.3 Write property test for token refresh on expiry
    - **Property 4: Token Refresh on Expiry**
    - **Validates: Requirements 2.4**
  
  - [ ]* 6.4 Write unit tests for Instagram OAuth
    - Test authorization redirect
    - Test callback with valid code
    - Test token encryption
    - Test token refresh
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 8. AWS service clients setup
  - [ ] 8.1 Create S3 client wrapper
    - Initialize boto3 S3 client with async support (aioboto3)
    - Implement upload_file method with user_id/resource_type/file_id key structure
    - Implement generate_presigned_url method (5 min expiry)
    - Implement delete_file method
    - Configure bucket name from environment
    - _Requirements: 3.2, 13.4, 26.4_
  
  - [ ] 8.2 Create SQS client wrapper
    - Initialize boto3 SQS client with async support
    - Implement send_message method with deduplication
    - Implement receive_messages method with long polling
    - Implement delete_message method
    - Implement change_message_visibility method
    - Configure queue URL from environment
    - _Requirements: 6.2, 9.1, 13.5_
  
  - [ ] 8.3 Create Bedrock client wrapper
    - Initialize boto3 Bedrock Runtime client
    - Implement invoke_model method for Claude 3 Sonnet
    - Set timeouts (5s connection, 15s response)
    - Implement retry logic with exponential backoff (2s, 4s, 8s)
    - _Requirements: 5.1, 19.3, 30.2_
  
  - [ ] 8.4 Create Rekognition client wrapper
    - Initialize boto3 Rekognition client
    - Implement detect_labels method (MinConfidence=75)
    - Implement detect_faces method
    - Implement detect_moderation_labels method
    - Set timeouts (5s connection, 10s response)
    - Implement retry logic with exponential backoff (1s, 2s, 4s)
    - _Requirements: 4.1, 4.4, 19.4, 30.3_
  
  - [ ] 8.5 Create Secrets Manager client wrapper
    - Initialize boto3 Secrets Manager client
    - Implement get_secret method for encryption key retrieval
    - Cache secrets in memory with 1-hour expiry
    - _Requirements: 25.2_

- [ ] 9. Image analysis service
  - [ ] 9.1 Implement image analysis algorithm
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
  - [ ] 10.1 Create product schemas
    - ProductCreateRequest with name, description validation
    - ProductUpdateRequest with optional fields
    - ProductResponse with all product fields
    - _Requirements: 3.1, 10.3_
  
  - [ ] 10.2 Implement product creation endpoint
    - POST /api/v1/products with multipart/form-data
    - Validate image file (JPEG/PNG, max 10MB)
    - Upload image to S3
    - Analyze image with Rekognition
    - Create product in database with user_id association
    - Return product with image_url and analysis
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 10.3 Implement product listing endpoint
    - GET /api/v1/products
    - Filter by authenticated user_id
    - Exclude soft-deleted products
    - Support pagination
    - Return list of products
    - _Requirements: 3.4_
  
  - [ ] 10.4 Implement product update endpoint
    - PUT /api/v1/products/{id}
    - Verify ownership
    - Validate changes
    - Update database record
    - _Requirements: 3.5_
  
  - [ ] 10.5 Implement product deletion endpoint
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

- [ ] 11. Campaign generation service
  - [ ] 11.1 Implement hashtag generation algorithm
    - Create generate_hashtags function
    - Convert suggested hashtags to lowercase, remove spaces, prefix with #
    - Add label-based hashtags from top 3 product labels
    - Add fixed brand hashtags (#smallbusiness, #shoponline, #supportlocal)
    - Remove duplicates (case-insensitive)
    - Limit to 10 total hashtags
    - _Requirements: 5.2_
  
  - [ ]* 11.2 Write property test for hashtag generation algorithm
    - **Property 24: Hashtag Generation Algorithm**
    - **Validates: Requirements 5.2**
  
  - [ ] 11.3 Implement optimal posting time calculation
    - Create calculate_optimal_posting_time function
    - Use user timezone from database
    - Suggest 18:00 for weekdays, 11:00 for weekends
    - If time is past, add 1 day
    - Convert to UTC for storage
    - _Requirements: 5.2_
  
  - [ ] 11.4 Implement campaign generation with Bedrock
    - Create generate_campaign method in CampaignService
    - Check idempotency_key for duplicate requests
    - Retrieve product with image analysis
    - Construct Bedrock prompt with product details and tone
    - Call Bedrock API with Claude 3 Sonnet model
    - Parse JSON response for caption and hashtags
    - Apply hashtag generation algorithm
    - Calculate optimal posting time
    - Create campaign in database with status "draft"
    - Store bedrock_model_version and prompt_template_version
    - _Requirements: 5.1, 5.2, 5.3, 5.6_
  
  - [ ]* 11.5 Write property test for campaign generation structure
    - **Property 7: Campaign Generation Structure**
    - **Validates: Requirements 5.2, 5.3**
  
  - [ ]* 11.6 Write unit tests for campaign generation
    - Test with mocked Bedrock responses
    - Test idempotency (duplicate requests)
    - Test hashtag generation
    - Test optimal time calculation
    - Test error handling when Bedrock fails
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 13. Rate limiting and quota management
  - [ ] 13.1 Implement token bucket rate limiting
    - Create check_rate_limit function with MongoDB-backed storage
    - Implement token bucket algorithm (100 tokens, refill 100/min)
    - Calculate refill based on elapsed time
    - Update bucket atomically
    - Return allowed status and rate limit headers
    - _Requirements: 20.1, 20.2_
  
  - [ ] 13.2 Create rate limiting middleware
    - Apply to all /api/v1/ endpoints
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
    - Increment counter if allowed
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

- [ ] 14. Campaign scheduling service
  - [ ] 14.1 Implement campaign scheduling
    - Create schedule_campaign method in SchedulerService
    - Calculate delay_seconds from scheduled_time
    - If delay > 900s (15 min), set delay to 0 (worker will check time)
    - Create SQS message with campaign_id and scheduled_time
    - Use message deduplication with campaign_id
    - Send message to queue
    - _Requirements: 6.2_
  
  - [ ] 14.2 Implement campaign scheduling endpoint
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
  
  - [ ] 14.5 Implement campaign cancellation endpoint
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

- [ ] 15. Instagram publishing service
  - [ ] 15.1 Implement Instagram publishing with retry
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
  
  - [ ] 15.5 Implement idempotency checking for publishing
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

- [ ] 16. Worker service for campaign publishing
  - [ ] 16.1 Implement worker message processing
    - Create process_message method in WorkerService
    - Parse message body for campaign_id and scheduled_time
    - Check if scheduled_time <= current_time
    - If not ready, extend message visibility and return
    - Atomically update campaign status: scheduled → publishing
    - If update fails (already processed), delete message and return
    - Retrieve campaign from database
    - Call Instagram service to publish
    - On success: Update status to "published", store post_id, delete message
    - On failure: Increment publish_attempts
    - If attempts >= 3: Update status to "failed", delete message
    - If attempts < 3: Update status to "scheduled", extend visibility (30s)
    - _Requirements: 6.3, 7.1, 7.5, 9.2, 9.3, 9.4, 18.2_
  
  - [ ] 16.2 Implement worker polling loop
    - Create poll_and_process method
    - Receive up to 10 messages from SQS (long polling 20s)
    - Process messages concurrently (max 5 concurrent)
    - Use asyncio.gather for parallel processing
    - Loop indefinitely
    - _Requirements: 9.2, 9.6_
  
  - [ ] 16.3 Implement dead-letter queue handling
    - Configure SQS dead-letter queue
    - Move messages after 3 failed attempts
    - Log failure reason, retry count, and payload
    - _Requirements: 9.5, 21.1, 21.2, 21.3_
  
  - [ ]* 16.4 Write integration tests for worker
    - Test message processing with scheduled campaign
    - Test atomic status update
    - Test retry logic
    - Test dead-letter queue placement
    - Test concurrent processing
    - _Requirements: 6.3, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ] 17. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 18. Analytics service and endpoints
  - [ ] 18.1 Implement Instagram insights fetching
    - Create fetch_insights method in InstagramService
    - Call Instagram Graph API /{post_id}/insights
    - Request metrics: likes, comments, reach, impressions
    - Calculate engagement_rate: (likes + comments) / reach
    - Return InstagramInsights object
    - _Requirements: 8.1_
  
  - [ ] 18.2 Implement analytics aggregation
    - Create get_analytics_summary method in AnalyticsService
    - Query analytics collection for user's campaigns in date range
    - Calculate totals: sum of likes, comments, reach, impressions
    - Calculate averages: mean engagement_rate
    - Calculate trends: compare to previous period
    - Identify top performing campaigns
    - Return AnalyticsSummary object
    - _Requirements: 8.3_
  
  - [ ] 18.3 Implement analytics storage
    - Create store_analytics method
    - Associate metrics with campaign_id and timestamp
    - Store in analytics collection
    - _Requirements: 8.2_
  
  - [ ]* 18.4 Write property test for analytics association
    - **Property 11: Analytics Association**
    - **Validates: Requirements 8.2**
  
  - [ ] 18.5 Implement analytics endpoints
    - GET /api/v1/analytics?start_date=&end_date=
    - Verify user authentication
    - Call analytics service to aggregate data
    - Return summary statistics
    - _Requirements: 8.3_
  
  - [ ] 18.6 Implement periodic analytics fetching worker task
    - Create fetch_analytics_for_published_campaigns task
    - Query campaigns with status "published" and last_analytics_fetch > 24h ago
    - For each campaign, fetch insights from Instagram
    - Store analytics in database
    - Update campaign.last_analytics_fetch timestamp
    - _Requirements: 8.1, 8.4_
  
  - [ ]* 18.7 Write integration tests for analytics
    - Test insights fetching with mocked Instagram API
    - Test analytics storage
    - Test analytics aggregation
    - Test analytics endpoint
    - _Requirements: 8.1, 8.2, 8.3, 8.6_

- [ ] 19. Campaign management endpoints
  - [ ] 19.1 Create campaign schemas
    - CampaignGenerateRequest with product_id, tone, idempotency_key
    - CampaignScheduleRequest with scheduled_time validation
    - CampaignResponse with all campaign fields
    - _Requirements: 10.3_
  
  - [ ] 19.2 Implement campaign generation endpoint
    - POST /api/v1/campaigns/generate
    - Check daily quota with check_and_increment_quota
    - Validate input with Pydantic
    - Call campaign service to generate campaign
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
  
  - [ ] 20.2 Implement error handling middleware
    - Create exception handlers for each error type
    - Map exceptions to HTTP status codes
    - Return standardized error responses
    - Include trace_id in error responses
    - Add retry-after headers for rate limit errors
    - _Requirements: 10.5, 14.1, 14.5_
  
  - [ ] 20.3 Implement structured logging
    - Configure logging with JSON formatter
    - Include timestamp, level, service, trace_id, message
    - Log all API requests (method, path, status, duration)
    - Log authentication attempts
    - Log external API calls
    - Log queue message processing
    - Never log sensitive data (passwords, tokens, keys)
    - _Requirements: 11.6, 14.1, 14.2, 14.3, 14.4, 14.6, 22.1_
  
  - [ ]* 20.4 Write property test for structured logging format
    - **Property 18: Structured Logging Format**
    - **Validates: Requirements 22.1, 11.6**
  
  - [ ] 20.5 Implement trace ID middleware
    - Generate unique trace_id for each request
    - Store in request.state
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

- [ ] 25. Health check endpoints
  - [ ] 25.1 Implement health check endpoints
    - GET /health/liveness - Always return 200 if service is running
    - GET /health/readiness - Return 200 if database is connected, 503 otherwise
    - Check database connectivity
    - Return status within 100ms
    - _Requirements: 17.3, 17.4, 22.3, 22.4_
  
  - [ ]* 25.2 Write tests for health checks
    - Test liveness endpoint
    - Test readiness with database connected
    - Test readiness with database disconnected
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

- [ ] 28. Frontend React application
  - [ ] 28.1 Create authentication context and hooks
    - Implement AuthContext with user state and token management
    - Create useAuth hook
    - Store tokens in localStorage
    - Implement login, logout, refreshToken functions
    - _Requirements: 1.2, 1.6, 12.3_
  
  - [ ] 28.2 Create API client service
    - Implement Axios instance with base URL
    - Add request interceptor to include JWT token
    - Add response interceptor to handle 401 and refresh token
    - Implement methods for all API endpoints
    - _Requirements: 12.3, 12.4_
  
  - [ ] 28.3 Create authentication pages
    - Login page with email/password form
    - Registration page with email/password form
    - Implement form validation
    - Handle authentication errors
    - Redirect to dashboard on success
    - _Requirements: 12.1, 12.6_
  
  - [ ] 28.4 Create dashboard layout
    - Navigation bar with links to products, campaigns, analytics
    - Protected routes requiring authentication
    - Logout button
    - _Requirements: 12.2, 12.7_
  
  - [ ] 28.5 Create product management pages
    - Product list page with grid/list view
    - Product upload form with image preview
    - Product edit form
    - Product delete confirmation
    - Display loading states
    - Handle errors with user-friendly messages
    - _Requirements: 12.5, 12.6_
  
  - [ ] 28.6 Create campaign management pages
    - Campaign list page with filters (status)
    - Campaign generation form (select product, choose tone)
    - Campaign detail view with caption, hashtags, image
    - Campaign scheduling form with date/time picker
    - Display loading states
    - Handle quota exceeded errors
    - _Requirements: 12.5, 12.6_
  
  - [ ] 28.7 Create analytics dashboard
    - Display summary statistics (total likes, comments, reach, impressions)
    - Display engagement rate
    - Display trends with charts
    - Display top performing campaigns
    - Date range selector
    - _Requirements: 8.5_
  
  - [ ] 28.8 Create Instagram connection flow
    - Instagram connect button
    - Handle OAuth redirect
    - Display connection status
    - _Requirements: 2.1_

- [ ] 29. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 30. Docker and deployment configuration
  - [ ] 30.1 Create Dockerfile for API service
    - Use Python 3.11 base image
    - Install dependencies from requirements.txt
    - Copy application code
    - Expose port 8000
    - Set CMD to run uvicorn
    - _Requirements: 13.1_
  
  - [ ] 30.2 Create Dockerfile for worker service
    - Use Python 3.11 base image
    - Install dependencies from requirements.txt
    - Copy application code
    - Set CMD to run worker polling loop
    - _Requirements: 13.1_
  
  - [ ] 30.3 Create docker-compose.yml for local development
    - Define api-service container
    - Define worker-service container
    - Define MongoDB container (for local dev)
    - Define environment variables
    - Set up networking
    - _Requirements: 13.1, 13.7_
  
  - [ ] 30.4 Create ECS task definitions
    - Create task definition for API service
    - Create task definition for worker service
    - Configure CPU and memory limits
    - Configure environment variables
    - Configure CloudWatch logging
    - _Requirements: 13.2, 13.6_
  
  - [ ] 30.5 Create environment configuration files
    - Create .env.example with all required variables
    - Document each variable
    - Create separate configs for dev, staging, prod
    - _Requirements: 15.1, 15.2, 15.6_
  
  - [ ] 30.6 Configure CloudWatch logging
    - Set up log groups for API service and worker service
    - Configure log retention (30 days)
    - Set up log streams
    - _Requirements: 13.6, 14.1_
  
  - [ ] 30.7 Configure CloudWatch alarms
    - Create alarm for API error rate > 5%
    - Create alarm for queue depth > 1000
    - Create alarm for worker lag > 5 minutes
    - Create alarm for publish failure rate > 10%
    - Configure SNS notifications
    - _Requirements: 22.6, 22.7_

- [ ] 31. Database indexes and optimization
  - [ ] 31.1 Create MongoDB indexes
    - users: unique index on email, sparse index on instagram_user_id
    - products: index on user_id, compound index on (user_id, created_at), sparse index on deleted_at
    - campaigns: index on user_id, compound indexes on (user_id, scheduled_time) and (user_id, status), index on scheduled_time, unique index on idempotency_key, sparse index on instagram_post_id
    - analytics: index on campaign_id, compound index on (user_id, fetched_at)
    - rate_limits: TTL index on expires_at
    - _Requirements: 26.2, 29.7_
  
  - [ ] 31.2 Configure MongoDB connection pooling
    - Set appropriate pool size limits
    - Configure connection timeout
    - Configure socket timeout
    - _Requirements: 29.5_

- [ ] 32. Configuration validation and startup checks
  - [ ] 32.1 Implement configuration validation
    - Create validate_config function
    - Check all required environment variables are set
    - Validate format of URLs, keys, etc.
    - Fail fast on startup if config is invalid
    - _Requirements: 15.3_
  
  - [ ] 32.2 Implement startup health checks
    - Check database connectivity on startup
    - Check AWS service connectivity (S3, SQS, Secrets Manager)
    - Log startup status
    - _Requirements: 17.3_

- [ ] 33. Documentation
  - [ ] 33.1 Create comprehensive README.md
    - System architecture explanation
    - AI workflow (Bedrock + Rekognition flow)
    - Instagram integration flow
    - Token lifecycle management
    - Campaign generation pipeline
    - Scheduling & worker logic
    - MongoDB schema overview
    - Deployment guide (Docker + ECS)
    - Environment variables list
    - Security considerations
    - Future improvements
    - Scalability plan
    - _Requirements: 15.6_
  
  - [ ] 33.2 Create development_rules.md
    - Follow clean architecture principles
    - Use async IO wherever possible
    - No business logic in route handlers
    - Use service layer
    - Environment variables only
    - No hardcoded secrets
    - Type hints everywhere
    - Clear docstrings
    - Separate worker from API service
    - _Requirements: 10.1, 10.2, 10.6, 11.7_
  
  - [ ] 33.3 Create API documentation
    - Document all endpoints with OpenAPI/Swagger
    - Include request/response examples
    - Document error codes
    - Document rate limits and quotas
    - _Requirements: 27.4_
  
  - [ ] 33.4 Create architecture.md
    - Document system architecture with diagrams
    - Document request flow patterns
    - Document data models
    - Document algorithms
    - _Requirements: 15.6_

- [ ] 34. Final integration and end-to-end testing
  - [ ]* 34.1 Write end-to-end test for complete user flow
    - Register user
    - Login
    - Connect Instagram (mocked)
    - Upload product
    - Generate campaign
    - Schedule campaign
    - Worker processes and publishes (mocked Instagram)
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
- Integration tests validate API endpoints with real database and mocked external services
- End-to-end tests validate complete user flows
- All external services (Instagram, Bedrock, Rekognition, S3, SQS) should be mocked in tests
- Use Hypothesis for property-based testing in Python
- Use pytest with pytest-asyncio for async test support
- Use httpx-mock or responses for mocking HTTP calls
- Use moto for mocking AWS services
- Follow clean architecture: routes → services → repositories → database
- No business logic in route handlers
- All service methods should be async
- Include comprehensive docstrings and type hints
- Never log sensitive data (passwords, tokens, API keys)
- Always validate user ownership before allowing resource access
- Use environment variables for all configuration
- Fail fast on startup if required config is missing

