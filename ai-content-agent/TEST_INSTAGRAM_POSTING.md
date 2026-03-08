# Test Instagram Posting - Step by Step

This guide will help you test if Instagram posting is working.

---

## ⚠️ Important Prerequisites

1. **Instagram Business Account** connected via OAuth
2. **Publicly accessible image URL** (Instagram can't access localhost)
3. **Valid access token** (not expired)

---

## Method 1: Using the Test Script (Easiest)

### Step 1: Get Your Credentials

First, you need your Instagram credentials. Run this query in your database:

```sql
SELECT provider_account_id, access_token 
FROM oauth_accounts 
WHERE provider = 'instagram' 
ORDER BY created_at DESC 
LIMIT 1;
```

Or check the backend console when you connect Instagram - it logs the account ID.

### Step 2: Run the Test Script

```bash
cd ai-content-agent/backend
.\venv\Scripts\activate
python test_instagram_post.py
```

### Step 3: Follow the Prompts

The script will ask for:
1. **Access Token** - From database or OAuth connection
2. **Instagram Account ID** - From database or OAuth connection
3. **Image URL** - Must be publicly accessible (use https://picsum.photos/1080/1080 for testing)

### Step 4: Confirm and Post

Type `yes` to confirm and the script will post to Instagram.

### Expected Output:

**Success:**
```
📸 Creating Instagram media container...
✅ Container created: 123456789
✅ Container ready for publishing
🚀 Publishing to Instagram...
✅ Published to Instagram! Media ID: 987654321

✅ SUCCESS!
Media ID: 987654321
🎉 Post published to Instagram!
```

**Check your Instagram account** - The post should appear in your feed!

---

## Method 2: Using the API Endpoint

### Step 1: Start the Backend

```bash
cd ai-content-agent/backend
.\venv\Scripts\activate
python -m uvicorn main:app --host 0.0.0.0 --port 8002
```

### Step 2: Create a Campaign with Content

1. Open http://localhost:5173
2. Login
3. Create a campaign
4. Generate content
5. Approve at least one post

### Step 3: Get the Content ID

Check the browser console or backend logs for the content ID, or use this API:

```bash
curl http://localhost:8002/campaigns/{campaign_id}/content
```

### Step 4: Publish via API

```bash
curl -X POST "http://localhost:8002/campaigns/{campaign_id}/schedule/{content_id}/publish" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Expected Response:

```json
{
  "success": true,
  "message": "Post published to Instagram successfully!",
  "media_id": "987654321",
  "content_id": "...",
  "campaign_id": "...",
  "published_at": "2026-03-08T..."
}
```

---

## Method 3: Using the Frontend (Coming Soon)

The frontend doesn't have a "Publish Now" button yet. You can add one or use Methods 1 or 2.

---

## 🔧 Troubleshooting

### Issue: "Image URL not publicly accessible"

**Problem:** Instagram can't access localhost URLs

**Solutions:**
1. **Use ngrok** to expose your local server:
   ```bash
   ngrok http 8002
   ```
   Then use the ngrok URL for images

2. **Upload to a public server:**
   - Upload image to Imgur, Cloudinary, or S3
   - Use the public URL

3. **Use a test image:**
   - Use `https://picsum.photos/1080/1080` for testing

### Issue: "Access token expired (Error 190)"

**Problem:** Instagram access token has expired

**Solution:**
1. Go to the app
2. Disconnect Instagram
3. Reconnect Instagram
4. Try again

### Issue: "Container creation failed"

**Problem:** Image format or size issue

**Solution:**
- Use JPG or PNG format
- Image should be at least 320x320 pixels
- Maximum file size: 8MB
- Aspect ratio: 1:1 (square) or 4:5 (portrait)

### Issue: "Rate limit exceeded (Error 368)"

**Problem:** Posted too many times

**Solution:**
- Instagram allows 25 posts per 24 hours
- Wait before posting again

### Issue: "Invalid account ID"

**Problem:** Wrong Instagram Business Account ID

**Solution:**
- Check the database for the correct account ID
- Make sure it's an Instagram Business Account (not personal)

---

## 📊 What to Check

### Backend Console Messages:

**Success Flow:**
```
📸 Creating Instagram media container...
✅ Container created: 123456789
✅ Container ready for publishing
🚀 Publishing to Instagram...
✅ Published to Instagram! Media ID: 987654321
```

**Failure Flow:**
```
📸 Creating Instagram media container...
❌ Failed to create container: [error message]
```

### Instagram Account:

1. Open Instagram app or web
2. Go to your Business Account
3. Check the feed
4. The post should appear with:
   - Your uploaded image
   - The caption
   - The hashtags

---

## 🎯 Quick Test Checklist

- [ ] Instagram Business Account connected
- [ ] Access token is valid (not expired)
- [ ] Image URL is publicly accessible
- [ ] Backend is running
- [ ] Run test script or API call
- [ ] Watch backend console for messages
- [ ] Check Instagram feed for post

---

## 💡 Pro Tips

### For Testing:

1. **Use a test Instagram account** - Don't spam your main account
2. **Use test images** - Use https://picsum.photos for random images
3. **Check rate limits** - Only 25 posts per 24 hours
4. **Watch the console** - All the action happens there

### For Production:

1. **Upload images to S3** - Don't use local URLs
2. **Implement retry logic** - Handle temporary failures
3. **Queue posts** - Don't post all at once
4. **Monitor rate limits** - Track API usage

---

## 🔍 Debugging Steps

### 1. Verify Instagram Connection

```bash
cd backend
python -c "from database_sqlite import get_db; from models.user import OAuthAccount; db = next(get_db()); account = db.query(OAuthAccount).filter(OAuthAccount.provider=='instagram').first(); print(f'Account ID: {account.provider_account_id}' if account else 'No Instagram account found')"
```

### 2. Test Image URL

Open the image URL in your browser. If you can see it, Instagram can too.

### 3. Check Access Token

The access token should be a long string (100+ characters). If it's short or empty, reconnect Instagram.

### 4. Test Posting Agent

```bash
cd backend
python -c "from agents.posting_agent import get_posting_agent; agent = get_posting_agent(); print('Posting agent loaded successfully!')"
```

---

## 📝 Example Test

Here's a complete example:

```bash
# 1. Start backend
cd ai-content-agent/backend
.\venv\Scripts\activate
python -m uvicorn main:app --host 0.0.0.0 --port 8002

# 2. In another terminal, run test
cd ai-content-agent/backend
.\venv\Scripts\activate
python test_instagram_post.py

# 3. Enter credentials when prompted:
# Access Token: [paste from database]
# Account ID: [paste from database]
# Image URL: https://picsum.photos/1080/1080

# 4. Type 'yes' to confirm

# 5. Watch the console for:
# ✅ Published to Instagram! Media ID: 987654321

# 6. Check Instagram feed!
```

---

## ✅ Success Indicators

You'll know it's working when:

1. **Console shows:** `✅ Published to Instagram! Media ID: XXXXX`
2. **API returns:** `{"success": true, "media_id": "XXXXX"}`
3. **Instagram feed:** Post appears with image and caption

---

## 🎉 Next Steps

Once posting works:

1. Test with different images
2. Test with different captions
3. Test scheduling (posts at specific times)
4. Test analytics (fetch engagement metrics)

---

**Need help?** Check the backend console for detailed error messages!
