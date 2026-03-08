# ⚡ Quick Test - 5 Minutes

The fastest way to verify all agents are working.

---

## 🚀 Start Servers

### Terminal 1 - Backend:
```bash
cd ai-content-agent/backend
.\venv\Scripts\activate
python -m uvicorn main:app --host 0.0.0.0 --port 8002
```

### Terminal 2 - Frontend:
```bash
cd ai-content-agent/frontend
npm run dev
```

**Open:** http://localhost:5173

---

## ✅ Test Checklist

### 1️⃣ Content Generator (AI) - 2 minutes

**Do:**
- Login → Create Campaign → Generate Content

**Watch Backend Console:**
```
🤖 Generating content with AWS Bedrock (Claude)...
```

**Check:**
- [ ] Console shows AI message
- [ ] 5 posts generated
- [ ] Captions are unique (not templates)
- [ ] Has emojis and hashtags

---

### 2️⃣ Campaign Planner (AI) - 1 minute

**Do:**
- Approve All → View Campaign Plan

**Watch Backend Console:**
```
🤖 Using AI to optimize campaign distribution...
✅ AI optimized content order: [2, 0, 4, 1, 3]
```

**Check:**
- [ ] Console shows AI optimization
- [ ] Shows content order array
- [ ] Content distributed across days

---

### 3️⃣ Scheduler (AI) - 1 minute

**Do:**
- Click "Schedule Posts"

**Watch Backend Console:**
```
✅ AI selected optimal time: 09:00
✅ AI selected optimal time: 14:00
✅ AI selected optimal time: 19:00
```

**Check:**
- [ ] Console shows AI time selection
- [ ] Multiple time messages
- [ ] Times are different

---

### 4️⃣ Posting Agent (Instagram) - Optional

**Do:**
- Approve Schedule → Analytics → Publish Now

**Watch Backend Console:**
```
📸 Creating Instagram media container...
✅ Published to Instagram! Media ID: 987654321
```

**Check:**
- [ ] Console shows Instagram messages
- [ ] Post appears on Instagram feed

**Skip if:** No Instagram account connected

---

### 5️⃣ Analytics Agent (Instagram) - Optional

**Do:**
- Analytics → Refresh Analytics

**Watch Backend Console:**
```
📊 Fetching Instagram insights...
✅ Fetched real Instagram analytics: 45 likes, 12 comments
```

**Check:**
- [ ] Console shows analytics fetch
- [ ] Real or mock data displayed

**Note:** Real data needs 24-48 hours after posting

---

## 🎯 Success Criteria

### Minimum (AI Agents):
- ✅ See `🤖 Generating content with AWS Bedrock`
- ✅ See `🤖 Using AI to optimize`
- ✅ See `✅ AI selected optimal time`

### Full (With Instagram):
- ✅ All above
- ✅ See `📸 Creating Instagram media container`
- ✅ See `📊 Fetching Instagram insights`

---

## 🔍 What to Look For

### Backend Console Messages:

**AI Working:**
```
🤖 Generating content with AWS Bedrock (Claude)...
🤖 Using AI to optimize campaign distribution...
✅ AI selected optimal time: 14:00
```

**Instagram Working:**
```
📸 Creating Instagram media container...
✅ Container created: 123456789
✅ Published to Instagram! Media ID: 987654321
📊 Fetching Instagram insights for post 987654321...
✅ Fetched real Instagram analytics: 45 likes, 12 comments
```

**Fallbacks (Still OK):**
```
⚠️ AI time selection failed, falling back to algorithm
⚠️ Insights not available yet for post 123456789
```

---

## ❌ Troubleshooting

### No AI Messages?
```bash
cd backend
python test_aws_connection.py
```
Should show: `✅ Bedrock access granted!`

### No Instagram Messages?
- Check Instagram account is connected
- Verify image URL is publicly accessible
- Check access token is valid

### Backend Errors?
- Check port 8002 is free
- Verify `.env` file exists
- Check AWS credentials

---

## 📊 Test Results

After testing, you should see:

**Console Output Example:**
```
🤖 Generating content with AWS Bedrock (Claude)...
✅ Content generated successfully
🤖 Using AI to optimize campaign distribution...
✅ AI optimized content order: [2, 0, 4, 1, 3]
✅ AI selected optimal time: 09:00
✅ AI selected optimal time: 14:00
✅ AI selected optimal time: 19:00
✅ AI selected optimal time: 21:00
✅ AI selected optimal time: 11:00
📊 Schedule created successfully
```

**This means ALL AI agents are working! 🎉**

---

## 🎬 Quick Demo Script

1. **Start servers** (2 terminals)
2. **Open browser** → http://localhost:5173
3. **Login** → test@example.com
4. **Create Campaign:**
   - Name: "Test"
   - Product: "EcoBottle"
   - Description: "Sustainable water bottle"
   - Duration: 7 days
5. **Click "Generate Content"**
6. **Watch console** → See `🤖` messages
7. **Approve All**
8. **View Campaign Plan** → See `🤖` optimization
9. **Schedule Posts** → See `✅ AI selected` messages
10. **Done!** ✅

**Total Time: 5 minutes**

---

## 💡 Pro Tips

1. **Keep backend console visible** - That's where all the action is!
2. **Look for emojis** - 🤖 = AI, ✅ = Success, 📸 = Instagram
3. **Don't worry about warnings** - ⚠️ means fallback is working
4. **Test without Instagram first** - AI agents work independently

---

## ✅ You're Done When...

You see these 3 messages in the console:
1. `🤖 Generating content with AWS Bedrock`
2. `🤖 Using AI to optimize campaign distribution`
3. `✅ AI selected optimal time`

**That's it! All AI agents are working!** 🎉

---

**Need detailed testing?** See `HOW_TO_TEST.md`

**Need help?** See `TESTING_GUIDE.md`
