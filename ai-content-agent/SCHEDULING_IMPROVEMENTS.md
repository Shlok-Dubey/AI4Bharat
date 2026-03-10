# Scheduling Improvements - Real-Time Analytics & Automated Posting

## Overview
This document describes the improvements made to the scheduling system to address:
1. AWS Bedrock legacy model error
2. Real-time analytics-based scheduling
3. Editable scheduled times
4. Automated posting at scheduled times

## Changes Made

### 1. AWS Bedrock Model Update

**Problem**: Legacy model `anthropic.claude-3-sonnet-20240229-v1:0` is no longer accessible

**Solution**: Updated to active model `anthropic.claude-3-5-sonnet-20241022-v2:0`

**Files Modified**:
- `backend/.env` - Updated BEDROCK_MODEL_ID
- `backend/utils/bedrock_client.py` - Updated default model
- `backend/agents/scheduler_agent.py` - Updated default model

### 2. Real-Time Analytics Integration

**Feature**: AI scheduler now uses live Instagram analytics to determine optimal posting times

**How It Works**:
1. Fetches historical post performance from last 30 days
2. Analyzes engagement by time of day
3. Identifies peak engagement times
4. Uses AWS Bedrock AI to select optimal time based on:
   - Historical performance data
   - Content type (reels vs posts)
   - Platform algorithms
   - Audience behavior patterns

**Files Modified**:
- `backend/agents/scheduler_agent.py`:
  - Added `_get_historical_performance()` method
  - Enhanced `_ai_select_time()` with live analytics
  - Added caching to avoid repeated database queries
  - Integrated with analytics agent

**Example Output**:
```
📊 Analyzing 25 historical posts for optimal timing...
✅ Historical analysis complete:
   Best times: 14:00, 19:00, 11:00, 16:00, 20:00
   Peak days: Monday, Wednesday, Friday
✅ AI selected optimal time: 14:00 (based on live analytics)
```

### 3. Editable Scheduled Times

**Feature**: Users can now manually adjust AI-suggested posting times

**New Endpoint**: `PUT /campaigns/{campaign_id}/schedule/{content_id}/time`

**Request Body**:
```json
{
  "scheduled_for": "2024-01-15 14:30:00"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Scheduled time updated successfully",
  "content_id": "uuid",
  "campaign_id": "uuid",
  "old_time": "2024-01-15 12:00:00",
  "new_time": "2024-01-15 14:30:00",
  "post_time": "14:30",
  "post_date": "2024-01-15",
  "day_of_week": "Monday"
}
```

**Files Modified**:
- `backend/schemas/schedule.py` - Added `ScheduleUpdateRequest` schema
- `backend/routes/schedule.py` - Added `update_scheduled_time()` endpoint

### 4. Automated Posting System

**Feature**: Background scheduler automatically posts content at scheduled times

**Implementation**: APScheduler with background jobs

**How It Works**:
1. When posts are scheduled, jobs are added to APScheduler
2. Scheduler runs in background and monitors pending posts
3. At scheduled time, posts are automatically published to Instagram
4. Status is updated in database (pending → published/failed)
5. Failed posts are automatically retried (up to 3 times)

**New Files**:
- `backend/scheduler_service.py` - Complete scheduler implementation

**Key Functions**:
- `start_scheduler()` - Starts background scheduler on app startup
- `stop_scheduler()` - Stops scheduler on app shutdown
- `post_scheduled_content_job()` - Job function that posts content
- `add_scheduled_post_job()` - Adds/updates scheduled job
- `load_pending_posts()` - Loads pending posts on startup
- `get_scheduler_status()` - Returns scheduler status

**Files Modified**:
- `backend/main.py` - Integrated scheduler lifecycle
- `backend/routes/schedule.py` - Added scheduler job creation
- `backend/requirements_sqlite.txt` - Added APScheduler dependency

**Monitoring Endpoints**:
- `GET /health` - Includes scheduler status
- `GET /scheduler/status` - Detailed scheduler information

**Example Status Response**:
```json
{
  "running": true,
  "jobs": 5,
  "job_details": [
    {
      "id": "post_uuid-1234",
      "next_run": "2024-01-15T14:00:00",
      "trigger": "date[2024-01-15 14:00:00 UTC]"
    }
  ]
}
```

## Installation

1. Install new dependency:
```bash
cd backend
pip install -r requirements_sqlite.txt
```

2. Restart the backend server:
```bash
python main.py
```

The scheduler will automatically:
- Start on application startup
- Load all pending scheduled posts
- Begin monitoring and posting at scheduled times

## Usage Flow

### 1. Create Campaign & Generate Content
```
POST /campaigns
POST /campaigns/{id}/generate
```

### 2. Schedule Posts (AI-Optimized)
```
POST /campaigns/{id}/schedule
```
- AI analyzes historical data
- Selects optimal posting times
- Creates scheduled posts
- Adds jobs to background scheduler

### 3. Edit Schedule (Optional)
```
PUT /campaigns/{id}/schedule/{content_id}/time
```
- Manually adjust posting time
- Scheduler job is automatically updated

### 4. Automated Posting
- Scheduler runs in background
- Posts are published at scheduled time
- Status updates automatically
- Failed posts are retried

### 5. Monitor Status
```
GET /scheduler/status
GET /health
```

## Features Summary

✅ **Real-Time Analytics**: Uses live Instagram data for optimal timing
✅ **AI-Powered Scheduling**: AWS Bedrock analyzes patterns and suggests times
✅ **Editable Times**: Users can override AI suggestions
✅ **Automated Posting**: Background scheduler posts at scheduled times
✅ **Retry Logic**: Failed posts are automatically retried
✅ **Status Monitoring**: Real-time scheduler status and job tracking
✅ **Active Model**: Uses latest AWS Bedrock model (no legacy errors)

## Technical Details

### Scheduler Configuration
- **Timezone**: UTC
- **Coalesce**: False (runs all missed jobs)
- **Max Instances**: 3 concurrent jobs
- **Retry Attempts**: 3 times
- **Retry Delay**: 5 minutes
- **Refresh Interval**: Checks for new posts every 5 minutes

### Database Fields
- `scheduled_for` - When to post (datetime)
- `status` - pending/published/failed/cancelled
- `platform_post_id` - ID from social media platform
- `published_at` - When actually posted
- `error_message` - Error details if failed
- `retry_count` - Number of retry attempts

### Error Handling
- OAuth token validation
- Image URL accessibility check
- Platform API error handling
- Automatic retry on failure
- Detailed error logging

## Future Enhancements

1. **Multi-Platform Support**: Extend to Facebook, Twitter, LinkedIn
2. **Timezone Support**: User-specific timezone handling
3. **Bulk Operations**: Schedule/edit multiple posts at once
4. **Analytics Dashboard**: Visualize optimal posting times
5. **A/B Testing**: Test different posting times
6. **Smart Rescheduling**: Automatically adjust based on performance
7. **Notification System**: Alert users on post success/failure
8. **Queue Management**: Priority queue for high-value posts

## Troubleshooting

### Scheduler Not Running
Check status: `GET /scheduler/status`
- If not running, restart the backend server
- Check logs for startup errors

### Posts Not Publishing
1. Verify OAuth connection: Check Instagram account is connected
2. Check image URL: Must be publicly accessible
3. Review error logs: Check `error_message` field in database
4. Verify scheduled time: Must be in the future

### AWS Bedrock Errors
- Ensure `.env` has correct `BEDROCK_MODEL_ID`
- Verify AWS credentials are valid
- Check model access in AWS console
- Model must be active (not legacy)

## API Examples

### Schedule Campaign
```bash
curl -X POST "http://localhost:8002/campaigns/{campaign_id}/schedule" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-15",
    "timezone_offset": 0
  }'
```

### Update Scheduled Time
```bash
curl -X PUT "http://localhost:8002/campaigns/{campaign_id}/schedule/{content_id}/time" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "scheduled_for": "2024-01-15 14:30:00"
  }'
```

### Check Scheduler Status
```bash
curl "http://localhost:8002/scheduler/status"
```

## Conclusion

The scheduling system now provides:
- **Intelligent Timing**: AI analyzes real data to find optimal posting times
- **Flexibility**: Users can override AI suggestions
- **Automation**: Posts are published automatically at scheduled times
- **Reliability**: Automatic retries and error handling
- **Monitoring**: Real-time status and job tracking

This creates a complete end-to-end automated posting system that learns from historical data and executes posts reliably.
