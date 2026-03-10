# How to View the Database

## Method 1: DB Browser for SQLite (Easiest - GUI)

### Download and Install
1. Go to https://sqlitebrowser.org/dl/
2. Download "DB Browser for SQLite" for Windows
3. Install it

### Open Database
1. Launch DB Browser for SQLite
2. Click "Open Database"
3. Navigate to: `ai-content-agent/backend/ai_content_agent.db`
4. Click Open

### View Tables
- Click "Browse Data" tab
- Select table from dropdown (users, campaigns, generated_content, etc.)
- See all data in table format

### Run Queries
- Click "Execute SQL" tab
- Type SQL queries
- Click "Execute" (F5)

**Example Queries:**
```sql
-- View all users
SELECT * FROM users;

-- View all campaigns
SELECT * FROM campaigns;

-- View generated content
SELECT * FROM generated_content;

-- View scheduled posts
SELECT * FROM scheduled_posts;

-- View analytics
SELECT * FROM post_analytics;

-- View OAuth accounts
SELECT provider, provider_account_id FROM oauth_accounts;
```

---

## Method 2: Command Line (SQLite CLI)

### Install SQLite CLI
Download from: https://www.sqlite.org/download.html

### Open Database
```bash
cd ai-content-agent/backend
sqlite3 ai_content_agent.db
```

### Common Commands
```sql
-- List all tables
.tables

-- Show table structure
.schema users

-- View data
SELECT * FROM users;
SELECT * FROM campaigns;
SELECT * FROM generated_content;

-- Exit
.quit
```

---

## Method 3: Python Script (Quick View)

### Create view_db.py
```bash
cd ai-content-agent/backend
```

Create file `view_db.py`:
```python
from database_sqlite import get_db
from models.user import User, OAuthAccount
from models.campaign import Campaign, CampaignAsset
from models.content import GeneratedContent, ScheduledPost, PostAnalytics

db = next(get_db())

print("=" * 60)
print("DATABASE OVERVIEW")
print("=" * 60)

# Users
users = db.query(User).all()
print(f"\n👥 Users: {len(users)}")
for user in users:
    print(f"  - {user.email}")

# OAuth Accounts
oauth = db.query(OAuthAccount).all()
print(f"\n🔗 OAuth Accounts: {len(oauth)}")
for acc in oauth:
    print(f"  - {acc.provider}: {acc.provider_account_id}")

# Campaigns
campaigns = db.query(Campaign).all()
print(f"\n📋 Campaigns: {len(campaigns)}")
for camp in campaigns:
    print(f"  - {camp.name} ({camp.product_name})")

# Generated Content
content = db.query(GeneratedContent).all()
print(f"\n📝 Generated Content: {len(content)}")
for c in content:
    print(f"  - {c.platform} {c.content_type}: {c.content_text[:50]}...")

# Scheduled Posts
scheduled = db.query(ScheduledPost).all()
print(f"\n📅 Scheduled Posts: {len(scheduled)}")
for post in scheduled:
    print(f"  - {post.status}: {post.scheduled_for}")

# Analytics
analytics = db.query(PostAnalytics).all()
print(f"\n📊 Analytics: {len(analytics)}")
for a in analytics:
    print(f"  - {a.likes} likes, {a.comments} comments, {a.views} views")

print("\n" + "=" * 60)
```

### Run it
```bash
.\venv\Scripts\activate
python view_db.py
```

---

## Method 4: VS Code Extension

### Install Extension
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search "SQLite"
4. Install "SQLite" by alexcvzz

### View Database
1. Right-click `ai_content_agent.db` in VS Code
2. Select "Open Database"
3. Click "SQLite Explorer" in sidebar
4. Expand tables to view data

---

## Quick Database Queries

### Check Historical Data
```sql
SELECT 
    sp.published_at,
    sp.status,
    pa.likes,
    pa.comments,
    pa.views,
    pa.engagement_rate
FROM scheduled_posts sp
LEFT JOIN post_analytics pa ON pa.post_id = sp.id
WHERE sp.status = 'published'
ORDER BY sp.published_at DESC;
```

### Check Best Performing Times
```sql
SELECT 
    strftime('%H:00', sp.published_at) as hour,
    AVG(pa.engagement_rate) as avg_engagement,
    COUNT(*) as post_count
FROM scheduled_posts sp
JOIN post_analytics pa ON pa.post_id = sp.id
WHERE sp.status = 'published'
GROUP BY hour
ORDER BY avg_engagement DESC;
```

### Check Campaign Status
```sql
SELECT 
    c.name,
    c.product_name,
    COUNT(DISTINCT gc.id) as total_content,
    COUNT(DISTINCT CASE WHEN gc.status = 'approved' THEN gc.id END) as approved,
    COUNT(DISTINCT sp.id) as scheduled
FROM campaigns c
LEFT JOIN generated_content gc ON gc.campaign_id = c.id
LEFT JOIN scheduled_posts sp ON sp.content_id = gc.id
GROUP BY c.id;
```

---

## Recommended: DB Browser for SQLite

**Best for:**
- Visual browsing
- Easy queries
- Editing data
- Exporting data

**Download:** https://sqlitebrowser.org/dl/

---

## Database Location

```
ai-content-agent/
└── backend/
    └── ai_content_agent.db  ← Your database file
```

---

## Tables in Database

- `users` - User accounts
- `oauth_accounts` - Instagram/social media connections
- `campaigns` - Marketing campaigns
- `campaign_assets` - Uploaded images
- `generated_content` - AI-generated posts
- `scheduled_posts` - Scheduled posts
- `post_analytics` - Engagement metrics

---

**Easiest way: Download DB Browser for SQLite!** 🎯
