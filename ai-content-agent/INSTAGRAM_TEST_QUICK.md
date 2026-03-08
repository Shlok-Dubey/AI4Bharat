# Quick Instagram Posting Test

## Fastest Way to Test (5 minutes)

### Step 1: Get Your Instagram Credentials

You need two things:
1. **Access Token** - From when you connected Instagram
2. **Instagram Account ID** - From when you connected Instagram

**How to find them:**
- Check backend console when you connect Instagram (it logs them)
- Or query database: `SELECT provider_account_id, access_token FROM oauth_accounts WHERE provider='instagram'`

### Step 2: Run Test Script

```bash
cd ai-content-agent/backend
.\venv\Scripts\activate
python test_instagram_post.py
```

### Step 3: Enter Info

When prompted:
- **Access Token:** Paste from database
- **Account ID:** Paste from database  
- **Image URL:** Press Enter (uses default test image)

### Step 4: Confirm

Type `yes` and press Enter

### Step 5: Watch Console

You should see:
```
📸 Creating Instagram media container...
✅ Container created: 123456789
✅ Published to Instagram! Media ID: 987654321
```

### Step 6: Check Instagram

Open your Instagram Business Account - the post should be there!

---

## ⚠️ Common Issues

### "Image URL not publicly accessible"
**Fix:** Use the default test image (just press Enter when asked)

### "Access token expired"
**Fix:** Reconnect Instagram in the app

### "Rate limit exceeded"
**Fix:** Wait a bit (Instagram allows 25 posts per 24 hours)

---

## ✅ Success = Post appears on Instagram!

If you see the post on your Instagram feed, posting is working! 🎉

---

**For detailed guide:** See `TEST_INSTAGRAM_POSTING.md`
