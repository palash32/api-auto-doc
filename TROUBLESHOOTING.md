# Emergency Troubleshooting Guide

## 🚨 Common Problems & Solutions

### Problem: Task Taking Way Longer Than Expected

**Decision Tree:**
```
Is it a core MVP feature?
├─ YES → Simplify the requirement
│   Example: "Multi-language" → "Python only"
│
└─ NO → Skip it, add to v2.0 backlog
    Example: "Team collaboration" → Not needed for first 10 customers
```

**When to simplify vs skip:**
- **Simplify:** Authentication (need it, but OAuth-only is enough)
- **Skip:** Advanced features (versioning, custom dashboards)

---

### Problem: Code Works Locally, Breaks in Production

**Debugging Checklist:**

1. **Check environment variables:**
```bash
railway variables  # List all env vars
# Compare with local .env
```

2. **Check logs:**
```bash
railway logs --tail 100
# Look for ERROR or CRITICAL
```

3. **Check database connection:**
```bash
railway run psql $DATABASE_URL
# Can you connect? Run: SELECT 1;
```

4. **Check external APIs:**
```bash
curl -I https://api.github.com
# Is GitHub API accessible?
```

5. **Check CORS:**
```javascript
// Backend should allow your frontend domain:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  // NOT "*"
)
```

**If still stuck:** Post in Railway Discord with:
- Error logs
- Steps to reproduce
- What you've tried

---

### Problem: Running Out of Money Before Launch

**Immediate Actions:**
1. **Pause paid services** (keep only hosting + domain)
2. **Validate with free tier:** Get 10 users, collect feedback
3. **Pre-sell:** Offer lifetime deal ($99 one-time) for cash now
4. **Scope cut:** Launch with absolute minimum features
5. **Side hustle:** Freelance 2 weeks, then resume

**Prevention:** Set spending alerts on all services

---

### Problem: Motivation Dropping, Feels Overwhelming

**Recovery Plan:**
1. **Take 2 days completely off** (no coding)
2. **Day 3: Do easiest task** (something satisfying like UI polish)
3. **Share progress publicly** (Twitter, Reddit - accountability)
4. **Remember why you started** (re-read your goals)
5. **Talk to users** (their excitement is contagious)

**Prevent Burnout:**
- Max 6 hours coding per day
- 1 full day off per week
- Celebrate small wins
- Sleep 7-8 hours

---

### Problem: Database Migration Failed

**Diagnosis:**
```bash
# Check migration history
alembic current

# Check pending migrations
alembic heads

# View migration SQL
alembic upgrade head --sql
```

**Common Fixes:**

**Issue: "Table already exists"**
```bash
# Mark migration as applied without running
alembic stamp head
```

**Issue: "Column does not exist"**
```bash
# Rollback one migration
alembic downgrade -1

# Fix the migration file

# Re-apply
alembic upgrade head
```

**Issue: "Foreign key constraint failed"**
```sql
-- Check what's blocking
SELECT * FROM table_name WHERE id = 'xxx';

-- Delete blocking rows or fix migration order
```

---

### Problem: Frontend Build Failing

**Common Errors:**

**Error: "Module not found"**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Error: "Type error in page.tsx"**
```bash
# Check TypeScript
npm run type-check

# Fix errors shown, then build again
npm run build
```

**Error: "Environment variable not defined"**
```bash
# Check .env.local exists
ls .env.local

# Restart dev server
npm run dev
```

---

### Problem: Celery Tasks Not Running

**Diagnosis:**
```bash
# Check worker is running
ps aux | grep celery

# Check Redis connection
redis-cli ping
# Should return: PONG

# Check Celery logs
celery -A backend.celery_app worker --loglevel=debug
```

**Common Fixes:**

**Issue: "Connection refused to Redis"**
```bash
# Check REDIS_URL environment variable
echo $REDIS_URL

# Test connection
redis-cli -u $REDIS_URL ping
```

**Issue: "Task not found"**
```python
# Make sure task is imported in celery_app.py
from backend.tasks.scan_repo_task import scan_repository_task
```

**Issue: "Task stuck in pending"**
```bash
# Check worker is consuming from correct queue
celery -A backend.celery_app inspect active

# Purge stuck tasks
celery -A backend.celery_app purge
```

---

### Problem: High API Error Rate (>5%)

**Investigation:**
```bash
# Check error distribution in logs
grep "ERROR" logs.txt | cut -d' ' -f5 | sort | uniq -c

# Common patterns:
# - 401: Authentication issues
# - 404: Broken endpoints
# - 500: Server crashes
# - 504: Timeouts
```

**Fixes by Error Type:**

**401 Unauthorized:**
- Check JWT_SECRET_KEY matches between deployments
- Verify token expiry settings
- Check clock sync (JWT depends on time)

**500 Internal Server:**
- Check Sentry for stack traces
- Look for unhandled exceptions
- Add more try/catch blocks

**504 Timeout:**
- Increase timeout settings
- Optimize slow database queries
- Add caching for expensive operations

---

### Problem: Out of Disk Space

**Check Usage:**
```bash
# Railway
railway run df -h

# Local
df -h
```

**Common Culprits:**

**Logs filling disk:**
```bash
# Rotate logs
find /var/log -name "*.log" -mtime +7 -delete
```

**Temp directories:**
```bash
# Clean old scans
find /tmp/scans -mtime +1 -delete
```

**Database too large:**
```sql
-- Check table sizes
SELECT 
  table_name,
  pg_size_pretty(pg_total_relation_size(table_name::regclass))
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(table_name::regclass) DESC;

-- Archive old data
DELETE FROM health_checks WHERE checked_at < NOW() - INTERVAL '30 days';
VACUUM FULL;
```

---

### Problem: Gemini API Rate Limited

**Error:** "429 Too Many Requests"

**Immediate Fix:**
```python
# Add exponential backoff
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def generate_docs(...):
    # Your Gemini call here
```

**Long-term Fix:**
- Implement Redis caching (cache for 7 days)
- Batch requests where possible
- Monitor quota usage in Google Cloud Console

---

## 🔍 Debug Toolkit

### Essential Commands

**Check if services are running:**
```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000

# Database
psql $DATABASE_URL -c "SELECT 1;"

# Redis
redis-cli ping
```

**View logs in real-time:**
```bash
# Backend
tail -f logs/app.log

# Celery
celery -A backend.celery_app events

# Railway
railway logs --tail
```

**Performance profiling:**
```bash
# Frontend (Lighthouse)
npm run build
npx lighthouse http://localhost:3000 --view

# Backend (API timing)
curl -w "@curl-format.txt" http://localhost:8000/api/test
```

**Database queries:**
```sql
-- Slow queries
SELECT query, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Active connections
SELECT * FROM pg_stat_activity;

-- Lock contention
SELECT * FROM pg_locks;
```

---

## 📞 Getting Help

### Before Posting (Checklist)
- [ ] Have you googled the error message?
- [ ] Have you checked the docs?
- [ ] Have you tried the solution above?
- [ ] Can you reproduce it consistently?
- [ ] Do you have error logs?

### Where to Ask
- **FastAPI:** Reddit r/FastAPI
- **Next.js:** Next.js Discord
- **Railway:** Railway Discord (fast response)
- **General:** StackOverflow (high quality, slower)
- **Urgent:** Twitter DMs to founders (use sparingly)

### How to Ask
**Good Question:**
```
I'm getting "Connection refused" when my FastAPI app tries to connect to PostgreSQL on Railway.

Error log:
[paste relevant 10 lines]

What I've tried:
1. Verified DATABASE_URL is set
2. Can connect via `railway run psql`
3. Works locally with same connection string

Environment:
- Railway (production)
- FastAPI 0.109.0
- PostgreSQL 14
```

**Bad Question:**
```
My app doesn't work. Help?
```

---

**Remember:** Most problems have been solved before. Google first, ask humans second, give up never.
