# How to Test All Agents - Simple Guide

Follow these steps to verify all agents are working correctly.

---

## Step 1: Start the Backend

```bash
cd ai-content-agent/backend
.\venv\Scripts\activate
python -m uvicorn main:app --host 0.0.0.0 --port 8002
```

**Keep this terminal open** - You'll watch the console messages here.

---

## Step 2: Start the Frontend (New Terminal)

```bash
cd ai-content-agent/frontend
npm run dev
```

Open browser: **http://localhost:5173**

---

## Step 3: Test Content Generator Agent (AI)

### Actions:
1. Log in to the application
2. Click "Create New Campaign"
3. Fill in:
   - Campaign Name: "Test Campaign"
   - Product Name: "EcoBottle"
   - Description: "Sustainable water bottle made from recycled materials"
   - Duration: 7 days
4. Click "Generate Content"

### Watch Backend Console For:
```
🤖 Generating content with AWS Bedrock (Claude)...
```

### Expected Result:
- 5 posts appear with AI-generated captions
- Each has unique, engaging text with emojis
- 15-20 hashtags per post
- Different from template text

### ✅ Success Indicator:
Captions are creative and unique (not generic templates)

---

## Step 4: Test Campaign Planner Agent (AI)

### Actions:
1. Click "Approve All" on the generated content
2. Click "View Campaign Plan"

### Watch Backend Console For:
```
🤖 Using AI to optimize campaign distribution...
✅ AI optimized content order: [2, 0, 4, 1, 3]
```

### Expected Result:
- Content is distributed across 7 days
- Strategic ordering (not just sequential)
- High-engagement content (reels) placed strategically

### ✅ Success Indicator:
Console shows AI optimization message with content order array

---

## Step 5: Test Scheduler Agent (AI)

### Actions:
1. In Campaign Plan, click "Schedule Posts"
2. Review the schedule preview

### Watch Backend Console For:
```
✅ AI selected optimal time: 09:00
✅ AI selected optimal time: 14:00
✅ AI selected optimal time: 19:00
```

### Expected Result:
- Each post has a specific time assigned
- Times are spread throughout the day
- Different times for different content types

### ✅ Success Indicator:
Console shows "AI selected optimal time" for each post

---

## Step 6: Test Posting Agent (Instagram API)

### ⚠️ Important Prerequisites:
- Instagram Business Account connected
- Product image uploaded (must be publicly accessible URL)
- Valid access token

### Actions:
1. Click "Approve Schedule"
2. Go to Analytics page
3. Find a scheduled post
4. Click "Publish Now" (if available)

### Watch Backend Console For:
```
📸 Creating Instagram media container...
✅ Container created: 123456789
✅ Container ready for publishing
🚀 Publishing to Instagram...
✅ Published to Instagram! Media ID: 987654321
```

### Expected Result:
- Post appears on your Instagram Business Account
- Caption and hashtags included
- Image displayed correctly

### ✅ Success Indicator:
- Console shows "Published to Instagram! Media ID: XXXXX"
- Post visible on Instagram feed

### 🔴 If It Fails:
- Check image URL is publicly accessible
- Verify Instagram token is valid
- Check rate limits (25 posts per 24 hours)

---

## Step 7: Test Analytics Agent (Instagram API)

### ⚠️ Important Note:
Instagram insights take 24-48 hours to become available. If post is recent, you'll see mock data.

### Actions:
1. Go to Analytics page
2. Click "Refresh Analytics"

### Watch Backend Console For:
```
📊 Fetching Instagram insights for post 987654321...
✅ Fetched real Instagram analytics: 45 likes, 12 comments
```

### Expected Result (if post is 24+ hours old):
- Real likes, comments, saves counts
- Actual impressions and reach
- Engagement rate calculated
- Source shows "instagram_api"

### Expected Result (if post is recent):
- Mock data displayed
- Console shows "Insights not available yet"
- System falls back gracefully

### ✅ Success Indicator:
Console shows "Fetched real Instagram analytics" OR "Insights not available yet"

---

## Quick Test (Without Instagram)

If you don't want to publish to Instagram yet, you can test the AI agents:

### Test AI Agents Only:

1. **Content Generator:**
   - Create campaign → Generate content
   - Look for: `🤖 Generating content with AWS Bedrock`
   - Check: Captions are unique and creative

2. **Campaign Planner:**
   - Approve content → View plan
   - Look for: `🤖 Using AI to optimize campaign distribution`
   - Check: Console shows content order array

3. **Scheduler:**
   - Schedule posts
   - Look for: `✅ AI selected optimal time: XX:XX`
   - Check: Multiple time selection messages

---

## Console Message Reference

### Success Messages:
- `🤖` = AI operation in progress
- `✅` = Operation successful
- `📸` = Instagram posting
- `📊` = Analytics fetching

### Warning Messages:
- `⚠️` = Fallback to alternative method
- Still works, just using backup method

### Error Messages:
- `❌` = Operation failed
- Check error details in message

---

## Troubleshooting

### "Bedrock not available"
**Fix:** Check AWS credentials in `.env` file
```bash
cd backend
python test_aws_connection.py
```

### "Instagram API error 190"
**Fix:** Access token expired, reconnect Instagram account

### "Container creation failed"
**Fix:** Ensure image URL is publicly accessible (not localhost)

### "Insights not available"
**Fix:** Wait 24-48 hours after posting, or use mock data

### No console messages
**Fix:** Make sure backend terminal is visible and running

---

## Expected Timeline

### Immediate (Works Now):
- ✅ Content Generator (AI)
- ✅ Campaign Planner (AI)
- ✅ Scheduler (AI)

### Requires Instagram Connection:
- ✅ Posting Agent (needs Instagram Business Account)
- ⏳ Analytics Agent (needs 24-48 hours after posting)

---

## Success Checklist

Use this to verify everything works:

- [ ] Backend starts without errors
- [ ] Frontend loads successfully
- [ ] Can create campaign
- [ ] Content generation shows AI message
- [ ] Generated content is unique/creative
- [ ] Campaign plan shows AI optimization
- [ ] Scheduler shows AI time selection
- [ ] (Optional) Post publishes to Instagram
- [ ] (Optional) Analytics fetch real or mock data

---

## Video Walkthrough (What to Expect)

### 1. Create Campaign (30 seconds)
- Fill form → Click Generate

### 2. Watch Console (5 seconds)
```
🤖 Generating content with AWS Bedrock (Claude)...
```

### 3. Review Content (30 seconds)
- See AI-generated captions
- Approve all

### 4. Watch Console (2 seconds)
```
🤖 Using AI to optimize campaign distribution...
✅ AI optimized content order: [2, 0, 4, 1, 3]
```

### 5. Schedule Posts (10 seconds)
- Click Schedule Posts

### 6. Watch Console (5 seconds)
```
✅ AI selected optimal time: 09:00
✅ AI selected optimal time: 14:00
✅ AI selected optimal time: 19:00
```

### 7. Done! ✅
All AI agents tested and working!

---

## Need Help?

### Check Logs:
1. Backend console (terminal running uvicorn)
2. Browser console (F12 → Console tab)
3. Network tab (F12 → Network tab)

### Common Issues:
- Port 8002 in use → Kill process and restart
- AWS credentials → Run `python test_aws_connection.py`
- Instagram token → Reconnect Instagram account

---

**Total Test Time: 5-10 minutes**

**You'll know it's working when you see the emoji messages in the console! 🤖✅📸📊**
