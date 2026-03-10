# AI Content Agent - Complete Manual Workflow Guide

## Overview
This guide walks through the complete end-to-end workflow for creating and publishing Instagram content manually (without automatic posting).

## Prerequisites
- AWS credentials configured in `.env` file
- Instagram Business Account
- Backend server running on port 8002
- Frontend server running on port 5173

## Complete Workflow Steps

### 1. User Signup/Login ✅
**Frontend:** `/signup` or `/login`
**Backend:** `POST /auth/signup` or `POST /auth/login`

- Create account with email and password
- Receive JWT token for authentication
- Token stored in localStorage

### 2. Connect Instagram Business Account ✅
**Frontend:** Dashboard → Instagram Connect button
**Backend:** `GET /auth/meta/connect` → OAuth flow → `GET /auth/meta/callback`

- Click "Connect Instagram" button
- Authorize Meta OAuth permissions
- System stores access token and Instagram account ID in DynamoDB
- Returns to dashboard with success message

### 3. Create Campaign ✅
**Frontend:** `/campaigns/create`
**Backend:** `POST /campaigns`

- Fill in campaign details:
  - Campaign name
  - Product name
  - Product description
  - Target platforms (Instagram)
  - Campaign duration (days)
- Campaign saved to DynamoDB with status "draft"

### 4. Upload Campaign Assets ✅
**Frontend:** Campaign Plan page → Upload Images
**Backend:** `POST /campaigns/{campaign_id}/assets`

- Upload product images (PNG, JPG, JPEG)
- Images stored in S3 bucket
- Asset metadata saved to DynamoDB
- S3 URLs returned for display

### 5. Generate AI Content ✅
**Frontend:** Campaign Plan page → Generate Content button
**Backend:** `POST /campaigns/{campaign_id}/generate-content`

- Select platform (Instagram)
- Select content type (post, story, reel)
- Specify number of variations
- AI generates captions, hashtags, and scripts using AWS Bedrock
- Content saved to DynamoDB with status "pending"

### 6. Review & Approve Content ✅
**Frontend:** `/campaigns/{campaign_id}/review`
**Backend:** `PUT /content/{content_id}/approve`

- View all generated content
- Review captions, hashtags, and metadata
- Approve or reject each piece
- Only approved content can be scheduled

### 7. Schedule Posts ✅
**Frontend:** Campaign Plan page → Schedule Posts button → `/campaigns/{campaign_id}/schedule`
**Backend:** `POST /campaigns/{campaign_id}/schedule`

- System calls Campaign Planner Agent to distribute content across campaign days
- System calls Scheduler Agent to assign optimal posting times based on:
  - Historical Instagram analytics (if available)
  - AI recommendations via Bedrock
  - Platform best practices (fallback)
- Schedule preview displayed with:
  - Posts grouped by day
  - Optimal posting times
  - Peak time indicators
  - Platform distribution
- Click "Approve Schedule" to save

### 8. View Scheduled Posts ✅
**Frontend:** `/campaigns/{campaign_id}/scheduled-posts`
**Backend:** `GET /campaigns/{campaign_id}/schedule/preview`

- View all scheduled posts organized by day
- See posting times and content previews
- Access manual publish functionality

### 9. Manual Publishing ✅ (NEW)
**Frontend:** Scheduled Posts page → "Publish Now" button
**Backend:** `POST /campaigns/{campaign_id}/posts/{post_id}/publish`

**Publishing Flow:**
1. User clicks "Publish Now" on a scheduled post
2. Backend verifies:
   - Campaign ownership
   - Post exists and is not already published
   - Instagram OAuth account is connected
   - Campaign has uploaded assets
3. Backend calls Posting Agent:
   - Validates and refreshes Instagram token if needed
   - Creates Instagram media container with image URL and caption
   - Waits for container to be ready
   - Publishes container to Instagram
4. Backend updates post status to "published" in DynamoDB
5. Frontend shows success message with Instagram Media ID
6. Post status updated in UI

**Error Handling:**
- Token expired → User must reconnect Instagram
- Invalid media URL → Check S3 permissions
- Rate limit → Wait and retry
- Network errors → Retry with exponential backoff

### 10. View Analytics ✅
**Frontend:** `/campaigns/{campaign_id}/analytics`
**Backend:** Analytics endpoints (future enhancement)

- View campaign performance
- Track published posts
- Monitor engagement metrics

## Key Features

### Manual Publishing (No Automatic Posting)
- EventBridge and Lambda are OPTIONAL and currently disabled
- Users have full control over when posts are published
- Posts are saved to DynamoDB with scheduled times
- Users manually click "Publish Now" to post to Instagram
- Ideal for testing and controlled publishing

### AI-Powered Scheduling
- Scheduler Agent analyzes historical Instagram performance
- Recommends optimal posting times using AWS Bedrock
- Falls back to platform best practices when no data exists
- Considers:
  - Day of week (weekday vs weekend)
  - Time of day (peak engagement hours)
  - Historical engagement rates
  - Platform-specific patterns

### Token Management
- Automatic token validation before posting
- Automatic token refresh using Meta's long-lived tokens
- Clear error messages when re-authentication is needed
- Tokens stored securely in DynamoDB

## Database Schema (DynamoDB)

### Tables Used:
1. **users** - User accounts
2. **oauth_accounts** - Instagram OAuth tokens
3. **campaigns** - Campaign metadata
4. **campaign_assets** - Uploaded images (S3 URLs)
5. **generated_content** - AI-generated captions and content
6. **scheduled_posts** - Scheduled post times and status
7. **post_analytics** - Instagram performance metrics (future)

## API Endpoints Summary

### Authentication
- `POST /auth/signup` - Create account
- `POST /auth/login` - Login
- `GET /auth/meta/connect` - Start Instagram OAuth
- `GET /auth/meta/callback` - Complete Instagram OAuth
- `GET /auth/meta/accounts` - Get connected accounts

### Campaigns
- `POST /campaigns` - Create campaign
- `GET /campaigns` - List user's campaigns
- `GET /campaigns/{id}` - Get campaign details
- `PATCH /campaigns/{id}` - Update campaign
- `DELETE /campaigns/{id}` - Delete campaign

### Assets
- `POST /campaigns/{id}/assets` - Upload image
- `GET /campaigns/{id}/assets` - List campaign assets
- `DELETE /campaigns/{id}/assets/{asset_id}` - Delete asset

### Content Generation
- `POST /campaigns/{id}/generate-content` - Generate AI content
- `GET /campaigns/{id}/content` - List generated content
- `GET /content/{id}` - Get content details
- `PUT /content/{id}/approve` - Approve/reject content

### Scheduling
- `POST /campaigns/{id}/schedule` - Create schedule
- `GET /campaigns/{id}/schedule/preview` - View schedule
- `PATCH /campaigns/{id}/schedule/{post_id}/time` - Edit scheduled time
- `POST /campaigns/{id}/posts/{post_id}/publish` - **Manual publish** 🚀

## Environment Variables Required

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# DynamoDB Tables
DYNAMODB_TABLE_USERS=ai-content-users
DYNAMODB_TABLE_OAUTH_ACCOUNTS=ai-content-oauth-accounts
DYNAMODB_TABLE_CAMPAIGNS=ai-content-campaigns
DYNAMODB_TABLE_CAMPAIGN_ASSETS=ai-content-campaign-assets
DYNAMODB_TABLE_GENERATED_CONTENT=ai-content-generated-content
DYNAMODB_TABLE_SCHEDULED_POSTS=ai-content-scheduled-posts
DYNAMODB_TABLE_POST_ANALYTICS=ai-content-post-analytics

# S3 Configuration
S3_BUCKET_NAME=ai-content-assets
S3_REGION=us-east-1

# AWS Bedrock
BEDROCK_MODEL_ID=us.anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_REGION=us-east-1

# Instagram OAuth (Meta)
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_REDIRECT_URI=http://localhost:8002/auth/meta/callback
META_SCOPES=instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement

# JWT
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Optional: EventBridge (for automatic posting - currently disabled)
# AWS_LAMBDA_POST_HANDLER_ARN=arn:aws:lambda:region:account:function:name
```

## Testing the Workflow

1. Start backend: `cd backend && python main.py`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser: `http://localhost:5173`
4. Follow steps 1-9 above
5. Verify post appears on Instagram

## Troubleshooting

### "Campaign not found" error
- Ensure campaign exists in DynamoDB
- Check campaign_id in URL matches database

### "No approved content" error
- Generate content first
- Approve at least one content piece

### "Instagram account not connected" error
- Connect Instagram from Dashboard
- Check OAuth token is valid

### "Failed to publish" error
- Check S3 image URLs are publicly accessible
- Verify Instagram token is valid
- Check Instagram API rate limits
- Review backend logs for detailed error

### EventBridge warnings
- These are informational only
- Automatic posting is disabled by design
- Posts are still saved to DynamoDB
- Use manual publishing instead

## Future Enhancements

1. **Automatic Posting** (Optional)
   - Configure AWS Lambda function
   - Set AWS_LAMBDA_POST_HANDLER_ARN
   - EventBridge will trigger Lambda at scheduled times
   - Lambda calls posting workflow automatically

2. **Analytics Dashboard**
   - Fetch Instagram Insights API
   - Display engagement metrics
   - Track performance over time

3. **Multi-Platform Support**
   - Facebook, Twitter, LinkedIn
   - Platform-specific optimizations

4. **Bulk Operations**
   - Publish multiple posts at once
   - Batch content generation
   - Mass approval/rejection

## Success Criteria

✅ User can signup and login
✅ User can connect Instagram Business Account
✅ User can create campaigns
✅ User can upload product images
✅ AI generates relevant content using Bedrock
✅ User can review and approve content
✅ AI schedules posts at optimal times
✅ User can view scheduled posts
✅ User can manually publish posts to Instagram
✅ Posts appear on Instagram feed
✅ Dashboard shows accurate statistics

## Conclusion

The end-to-end workflow is now complete with manual publishing. Users have full control over when their content is published to Instagram, while still benefiting from AI-powered content generation and intelligent scheduling recommendations.
