# Scheduling System Flow

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER CREATES CAMPAIGN                         │
│                  POST /campaigns/{id}/schedule                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              ANALYTICS AGENT FETCHES HISTORICAL DATA             │
│  • Query last 30 days of published posts                        │
│  • Calculate engagement by time of day                          │
│  • Identify peak engagement times                               │
│  • Analyze content type performance                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  AI SCHEDULER AGENT (AWS Bedrock)                │
│  • Receives historical performance data                         │
│  • Analyzes content type (reel vs post)                         │
│  • Considers platform algorithms                                │
│  • Selects optimal posting time                                 │
│                                                                  │
│  Example Output:                                                │
│  📊 Best times: 14:00, 19:00, 11:00, 16:00, 20:00              │
│  ✅ AI selected: 14:00 (based on live analytics)               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SCHEDULED POSTS CREATED                        │
│  • Save to database (status: pending)                           │
│  • scheduled_for: 2024-01-15 14:00:00                          │
│  • platform: instagram                                          │
│  • content_id: uuid                                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              BACKGROUND SCHEDULER (APScheduler)                  │
│  • Job added: post_uuid-1234                                    │
│  • Trigger: date[2024-01-15 14:00:00 UTC]                      │
│  • Status: Scheduled                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ (Optional)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER EDITS SCHEDULE TIME                      │
│              PUT /campaigns/{id}/schedule/{content_id}/time      │
│  • New time: 2024-01-15 16:30:00                               │
│  • Scheduler job automatically updated                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ (Wait for scheduled time)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SCHEDULED TIME REACHED                          │
│  • APScheduler triggers job                                     │
│  • Calls: post_scheduled_content_job(post_id)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    POSTING AGENT EXECUTES                        │
│  1. Fetch scheduled post from database                          │
│  2. Get content and campaign details                            │
│  3. Get user's Instagram OAuth token                            │
│  4. Get campaign image URL                                      │
│  5. Call Instagram Graph API                                    │
│     • Create media container                                    │
│     • Wait for processing                                       │
│     • Publish to Instagram                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
        ┌──────────────────┐  ┌──────────────────┐
        │     SUCCESS      │  │      FAILED      │
        └────────┬─────────┘  └────────┬─────────┘
                 │                     │
                 ▼                     ▼
    ┌────────────────────┐  ┌────────────────────┐
    │ Update Database    │  │ Update Database    │
    │ • status: published│  │ • status: failed   │
    │ • platform_post_id │  │ • error_message    │
    │ • published_at     │  │ • retry_count++    │
    └────────────────────┘  └────────┬───────────┘
                                     │
                                     │ (if retry_count < 3)
                                     ▼
                            ┌────────────────────┐
                            │ RETRY IN 5 MINUTES │
                            │ • Reschedule job   │
                            │ • status: pending  │
                            └────────────────────┘
```

## Key Components

### 1. Analytics Agent
- **Purpose**: Fetch historical performance data
- **Data Source**: Instagram API + Database
- **Output**: Best performing times, engagement patterns
- **Caching**: 5-minute cache to avoid repeated queries

### 2. Scheduler Agent (AI)
- **Purpose**: Select optimal posting time
- **AI Model**: AWS Bedrock Claude 3.5 Sonnet
- **Input**: Historical data + content details
- **Output**: Optimal time (HH:MM format)

### 3. Background Scheduler
- **Technology**: APScheduler
- **Type**: BackgroundScheduler
- **Timezone**: UTC
- **Features**: 
  - Auto-load pending posts on startup
  - Periodic refresh every 5 minutes
  - Concurrent job execution (max 3)
  - Automatic retry on failure

### 4. Posting Agent
- **Purpose**: Execute actual posting to Instagram
- **API**: Meta Graph API v19.0
- **Process**: Container → Process → Publish
- **Error Handling**: Retry up to 3 times

## Database States

```
┌──────────┐     ┌───────────┐     ┌────────────┐
│ PENDING  │────▶│ PUBLISHED │     │   FAILED   │
└──────────┘     └───────────┘     └─────┬──────┘
     ▲                                    │
     │                                    │
     └────────────────────────────────────┘
              (retry if count < 3)
```

## Monitoring Points

### 1. Scheduler Status
```
GET /scheduler/status
```
Shows:
- Running status
- Number of jobs
- Next run times

### 2. Health Check
```
GET /health
```
Shows:
- Database connection
- Scheduler status
- Job count

### 3. Database Query
```sql
SELECT * FROM scheduled_posts 
WHERE status = 'pending' 
AND scheduled_for > NOW()
ORDER BY scheduled_for ASC;
```

## Time Zones

All times are stored in UTC in the database. The `timezone_offset` parameter allows users to schedule in their local time:

```
User Time: 2024-01-15 14:00:00 EST (UTC-5)
Stored As: 2024-01-15 19:00:00 UTC
Posted At: 2024-01-15 19:00:00 UTC (14:00 EST)
```

## Error Handling

### Retry Logic
1. First attempt fails → Retry in 5 minutes
2. Second attempt fails → Retry in 5 minutes
3. Third attempt fails → Mark as failed (no more retries)

### Common Errors
- **OAuth Token Expired**: User needs to reconnect Instagram
- **Image URL Not Accessible**: Image must be publicly accessible
- **Rate Limit**: Instagram API rate limit reached
- **Invalid Media**: Image format or size issue

## Performance Considerations

### Caching
- Historical data cached for 5 minutes
- Reduces database queries
- Improves scheduling speed

### Concurrent Jobs
- Max 3 jobs can run simultaneously
- Prevents API rate limiting
- Ensures system stability

### Periodic Refresh
- Checks for new pending posts every 5 minutes
- Ensures no posts are missed
- Handles manual database updates

## Security

### OAuth Tokens
- Stored encrypted in database
- Never logged or exposed
- Validated before each post

### Image URLs
- Must be publicly accessible
- Validated before posting
- Supports HTTPS only

### API Keys
- AWS credentials from environment variables
- Never committed to code
- Rotated regularly

## Future Enhancements

1. **Multi-Platform**: Support Facebook, Twitter, LinkedIn
2. **Smart Retry**: Exponential backoff for retries
3. **Priority Queue**: High-value posts get priority
4. **Notifications**: Email/SMS on success/failure
5. **Analytics Dashboard**: Visualize optimal times
6. **A/B Testing**: Test different posting times
7. **Timezone Support**: User-specific timezones
8. **Bulk Operations**: Schedule multiple campaigns at once
