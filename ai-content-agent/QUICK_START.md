# Quick Start - Scheduling System

## What Was Fixed

### 1. ✅ AWS Bedrock Model Error
**Before**: `Access denied. This Model is marked by provider as Legacy`
**After**: Updated to active model `anthropic.claude-3-5-sonnet-20241022-v2:0`

### 2. ✅ Real-Time Analytics Scheduling
**Before**: Used static peak times
**After**: AI analyzes your Instagram historical data (last 30 days) to find optimal posting times

### 3. ✅ Editable Schedule Times
**Before**: No way to change AI-suggested times
**After**: New API endpoint to update scheduled times

### 4. ✅ Automated Posting
**Before**: Posts were scheduled but not automatically published
**After**: Background scheduler automatically posts at scheduled times

## Installation

```bash
cd ai-content-agent/backend
pip install APScheduler==3.10.4
```

Or run the install script:
```bash
cd ai-content-agent/backend
install_scheduler.bat
```

## Start the Server

```bash
cd ai-content-agent/backend
python main.py
```

The scheduler will automatically:
- Start in the background
- Load all pending scheduled posts
- Post content at scheduled times
- Retry failed posts automatically

## How It Works

### 1. Schedule Posts (AI-Optimized)
```
POST /campaigns/{campaign_id}/schedule
```

The AI will:
- Analyze your last 30 days of Instagram posts
- Find which times got the best engagement
- Select optimal posting times based on real data
- Create scheduled posts
- Add them to the background scheduler

**Example Console Output**:
```
📊 Analyzing 25 historical posts for optimal timing...
✅ Historical analysis complete:
   Best times: 14:00, 19:00, 11:00, 16:00, 20:00
   Peak days: Monday, Wednesday, Friday
✅ AI selected optimal time: 14:00 (based on live analytics)
```

### 2. Edit Schedule (Optional)
```
PUT /campaigns/{campaign_id}/schedule/{content_id}/time
Body: { "scheduled_for": "2024-01-15 14:30:00" }
```

### 3. Automated Posting
The scheduler runs in the background and:
- Monitors pending posts
- Posts at scheduled time
- Updates status (pending → published)
- Retries on failure (up to 3 times)

### 4. Monitor Status
```
GET /scheduler/status
```

Response:
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

## Key Features

✅ **Smart Scheduling**: Uses YOUR Instagram data to find best times
✅ **Editable**: Override AI suggestions anytime
✅ **Automated**: Posts publish automatically at scheduled time
✅ **Reliable**: Auto-retry on failure
✅ **Monitored**: Real-time status tracking

## Testing

### 1. Check Scheduler Status
Visit: http://localhost:8002/scheduler/status

### 2. Check Health
Visit: http://localhost:8002/health

Should show:
```json
{
  "status": "healthy",
  "database": "connected",
  "scheduler": {
    "running": true,
    "jobs": 5
  }
}
```

### 3. Schedule a Test Post
1. Create a campaign
2. Generate content
3. Schedule posts
4. Check scheduler status to see the job
5. Wait for scheduled time (or set it to 1 minute from now)
6. Post will automatically publish to Instagram

## Troubleshooting

### Scheduler Not Running
```bash
# Check status
curl http://localhost:8002/scheduler/status

# Restart server
python main.py
```

### Posts Not Publishing
1. Check Instagram OAuth is connected
2. Verify image URL is publicly accessible
3. Check error logs in database
4. Ensure scheduled time is in the future

### AWS Bedrock Errors
- Verify `.env` has `BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0`
- Check AWS credentials are valid
- Ensure model access in AWS console

## What's Next?

The system is now fully automated:
1. AI analyzes your data
2. Suggests optimal times
3. You can edit if needed
4. Posts publish automatically
5. Failed posts retry automatically

No more manual posting! 🎉

## Need Help?

See `SCHEDULING_IMPROVEMENTS.md` for detailed technical documentation.
