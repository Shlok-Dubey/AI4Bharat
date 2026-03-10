# ⚡ Live Analytics Scheduling - Quick Start

The scheduler now analyzes YOUR Instagram performance to find YOUR best posting times!

---

## 🚀 Quick Test (5 minutes)

### Step 1: Create Sample Data
```bash
cd ai-content-agent/backend
.\venv\Scripts\activate
python seed_historical_data.py
```

**Output:**
```
✅ HISTORICAL DATA SEEDED SUCCESSFULLY!
Best performing times: 19:00, 20:00, 18:00, 12:00, 09:00
```

### Step 2: Schedule a Campaign

1. Start backend and frontend
2. Create campaign → Generate content → Approve
3. Click "Schedule Posts"

### Step 3: Watch Console

**You should see:**
```
📊 Analyzing 20 historical posts for optimal timing...
✅ Historical analysis complete:
   Best times: 19:00, 20:00, 18:00, 12:00, 09:00
✅ AI selected optimal time: 19:00 (based on live analytics)
✅ AI selected optimal time: 20:00 (based on live analytics)
```

### Step 4: Check Schedule

Posts should be scheduled at the best performing times (19:00, 20:00, 18:00, etc.)

---

## 🎯 What Changed

### Before:
- Static times (9am, 2pm, 7pm)
- Same for everyone

### Now:
- Analyzes YOUR last 30 days
- Finds YOUR best times
- AI uses YOUR data

---

## 📊 What Gets Analyzed

- Published posts (last 30 days)
- Engagement metrics (likes, comments, views)
- Best performing hours
- Peak days
- Content type patterns

---

## ✅ Success = See This in Console

```
📊 Analyzing X historical posts for optimal timing...
✅ AI selected optimal time: 19:00 (based on live analytics)
```

If you see "based on live analytics" - it's working! 🎉

---

## 🔄 With Real Data

1. Publish posts to Instagram
2. Wait 24-48 hours for analytics
3. Schedule new campaign
4. AI uses YOUR real performance data!

---

**For detailed guide:** See `TEST_LIVE_ANALYTICS_SCHEDULING.md`
