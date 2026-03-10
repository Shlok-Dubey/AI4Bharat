# Database Options - Quick Guide

## Current: SQLite

**Location:** `ai-content-agent/backend/ai_content_agent.db`

**View Database:**
1. Download DB Browser for SQLite: https://sqlitebrowser.org/dl/
2. Open the `.db` file
3. Browse tables and data

**Or use Python:**
```bash
cd backend
.\venv\Scripts\activate
python -c "from database_sqlite import get_db; from models.user import User; db = next(get_db()); print(f'Users: {db.query(User).count()}')"
```

---

## Option: Amazon DynamoDB

### Why DynamoDB?
- ✅ Fully managed (no maintenance)
- ✅ Auto-scaling
- ✅ High availability
- ✅ Fast performance
- ✅ Pay per use

### Cost:
- Free tier: 25GB, enough for 1000+ users
- After: ~$5-20/month

### When to Use:
- Production deployment
- Need scalability
- AWS-native architecture

---

## Recommendation

### For Development:
**Use SQLite** (current setup)
- Fast and easy
- No AWS costs
- Perfect for testing

### For Production:
**Use DynamoDB**
- Scalable
- Managed
- Production-ready

### Best Approach:
**Dual Support** (I can implement)
- SQLite for local dev
- DynamoDB for production
- Switch with config

---

## Quick Actions

### View SQLite Database:
1. Download: https://sqlitebrowser.org/dl/
2. Open: `backend/ai_content_agent.db`
3. Browse tables

### Migrate to DynamoDB:
Let me know and I'll implement:
1. DynamoDB adapter
2. Table creation scripts
3. Migration tools
4. Dual database support

---

**For detailed guides:**
- `VIEW_DATABASE.md` - How to view SQLite
- `MIGRATE_TO_DYNAMODB.md` - DynamoDB migration

**Want DynamoDB? Just say "yes" and I'll implement it!** 🚀
