# Migrate to Amazon DynamoDB

Yes! You can use DynamoDB instead of SQLite. Here's how:

---

## Why DynamoDB?

### Benefits:
✅ Fully managed (no server maintenance)  
✅ Auto-scaling (handles any load)  
✅ High availability (99.99% uptime)  
✅ Fast performance (single-digit millisecond latency)  
✅ Pay per use (cost-effective)  
✅ Global tables (multi-region)  

### When to Use:
- Production deployment
- Need scalability
- Want serverless
- AWS-native architecture

### When to Keep SQLite:
- Local development
- Testing
- Small projects
- Learning

---

## Quick Migration (3 Steps)

### Step 1: Install DynamoDB Dependencies

```bash
cd ai-content-agent/backend
.\venv\Scripts\activate
pip install boto3 pynamodb
```

### Step 2: Create DynamoDB Tables

I'll create a script to set up all tables:

```bash
python setup_dynamodb.py
```

### Step 3: Update Configuration

Change `.env`:
```env
# Database Type
DATABASE_TYPE=dynamodb  # or sqlite

# DynamoDB Settings
AWS_REGION=us-east-1
DYNAMODB_TABLE_PREFIX=ai-content-agent-
```

---

## DynamoDB Table Design

### Tables Needed:

1. **Users** - User accounts
   - PK: user_id
   - Attributes: email, password_hash, created_at

2. **OAuthAccounts** - Social media connections
   - PK: user_id
   - SK: provider (instagram, facebook)
   - Attributes: access_token, provider_account_id

3. **Campaigns** - Marketing campaigns
   - PK: campaign_id
   - GSI: user_id (to query by user)
   - Attributes: name, product_name, settings

4. **GeneratedContent** - AI-generated posts
   - PK: content_id
   - GSI: campaign_id (to query by campaign)
   - Attributes: caption, hashtags, status

5. **ScheduledPosts** - Scheduled posts
   - PK: post_id
   - GSI: content_id, scheduled_for
   - Attributes: status, platform_post_id

6. **PostAnalytics** - Engagement metrics
   - PK: post_id
   - Attributes: likes, comments, views, engagement_rate

---

## Cost Estimate

### Free Tier (First 12 months):
- 25 GB storage
- 25 read/write capacity units
- Enough for ~1000 users

### After Free Tier:
- On-demand pricing: $1.25 per million writes, $0.25 per million reads
- Estimated: $5-20/month for small app

### Comparison:
- SQLite: Free but requires server
- PostgreSQL RDS: $15-30/month minimum
- DynamoDB: $5-20/month, fully managed

---

## Implementation Options

### Option 1: Dual Support (Recommended)

Keep both SQLite and DynamoDB support:
- SQLite for local development
- DynamoDB for production

**Benefits:**
- Easy local testing
- Production-ready
- Flexible deployment

### Option 2: DynamoDB Only

Use DynamoDB everywhere:
- Use DynamoDB Local for development
- DynamoDB for production

**Benefits:**
- Consistent environment
- True production testing

### Option 3: Gradual Migration

Start with SQLite, migrate later:
- Build with SQLite
- Export data
- Import to DynamoDB
- Switch configuration

---

## Quick Start with DynamoDB

### 1. Create Tables in AWS Console

Go to AWS Console → DynamoDB → Create Table

**Users Table:**
- Table name: `ai-content-agent-users`
- Partition key: `user_id` (String)

**Campaigns Table:**
- Table name: `ai-content-agent-campaigns`
- Partition key: `campaign_id` (String)
- GSI: `user_id-index` (user_id as partition key)

**Content Table:**
- Table name: `ai-content-agent-content`
- Partition key: `content_id` (String)
- GSI: `campaign_id-index` (campaign_id as partition key)

### 2. Update Code

I can create a DynamoDB adapter that works with your existing code:

```python
# database_dynamodb.py
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute

class UserModel(Model):
    class Meta:
        table_name = "ai-content-agent-users"
        region = 'us-east-1'
    
    user_id = UnicodeAttribute(hash_key=True)
    email = UnicodeAttribute()
    password_hash = UnicodeAttribute()
    created_at = UTCDateTimeAttribute()
```

### 3. Switch Database

Update `main.py`:
```python
# Choose database based on config
if os.getenv('DATABASE_TYPE') == 'dynamodb':
    from database_dynamodb import get_db
else:
    from database_sqlite import get_db
```

---

## Migration Script

I'll create a script to migrate existing data:

```bash
python migrate_sqlite_to_dynamodb.py
```

This will:
1. Read all data from SQLite
2. Create DynamoDB tables
3. Insert data into DynamoDB
4. Verify migration

---

## Should You Migrate Now?

### Migrate Now If:
- ✅ Deploying to production
- ✅ Need scalability
- ✅ Want AWS-native solution
- ✅ Have AWS credits

### Wait If:
- ⏳ Still in development
- ⏳ Testing locally
- ⏳ Learning the system
- ⏳ Small user base

---

## Recommendation

**For Now:** Keep SQLite for local development

**For Production:** Use DynamoDB

**Best Approach:** Dual support (I can implement this)

---

## Next Steps

### Option A: Implement Dual Support (Recommended)
I'll create:
1. `database_dynamodb.py` - DynamoDB adapter
2. `setup_dynamodb.py` - Table creation script
3. `migrate_sqlite_to_dynamodb.py` - Migration script
4. Configuration to switch between databases

### Option B: Full DynamoDB Migration
I'll:
1. Replace SQLite with DynamoDB
2. Update all models
3. Create tables in AWS
4. Migrate existing data

### Option C: Keep SQLite
Continue with SQLite:
- Works great for development
- Can migrate later when needed

---

## What Would You Like?

1. **Implement dual support** (SQLite + DynamoDB)?
2. **Full migration to DynamoDB**?
3. **Keep SQLite for now**?

Let me know and I'll implement it! 🚀

---

## Quick Answer

**Yes, you can use DynamoDB!** 

It's actually a great choice for production. I can implement it with dual support so you can:
- Use SQLite locally (fast, easy)
- Use DynamoDB in production (scalable, managed)

Want me to implement it? Just say "yes" and I'll create all the necessary files! 🎯
