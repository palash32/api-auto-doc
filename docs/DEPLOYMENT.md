# Deployment Guide - API Auto-Documentation Platform

## Overview
This guide walks you through deploying the API Auto-Documentation Platform to production.

---

## Prerequisites

### Required Accounts
- [ ] GitHub account (for OAuth)
- [ ] Google Cloud account (for Gemini API)
- [ ] Vercel account (for frontend)
- [ ] Railway/Render account (for backend)
- [ ] PostgreSQL database (Railway/Supabase/Neon)

### Required Tools
- [ ] Git
- [ ] Node.js 18+
- [ ] Python 3.11+
- [ ] npm or yarn

---

## Part 1: Environment Setup

### Backend Environment Variables

Create a `.env` file in `backend/` with these variables:

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Google Gemini AI
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-pro

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-oauth-client-id
GITHUB_CLIENT_SECRET=your-github-oauth-client-secret

# GitHub Webhooks
GITHUB_WEBHOOK_SECRET=your-webhook-secret-key

# Application
FRONTEND_URL=https://your-frontend-domain.vercel.app
ENVIRONMENT=production
CORS_ORIGINS=["https://your-frontend-domain.vercel.app"]
```

### Frontend Environment Variables

Create `.env.local` in `frontend/`:

```env
NEXT_PUBLIC_API_URL=https://your-backend-domain.railway.app
```

---

## Part 2: GitHub OAuth Setup

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Create new OAuth App:
   - **Application name:** API Auto-Documentation
   - **Homepage URL:** `https://your-frontend-domain.vercel.app`
   - **Authorization callback URL:** `https://your-frontend-domain.vercel.app/auth/callback`
3. Copy Client ID and Client Secret
4. Add to backend `.env` file

---

## Part 3: Database Setup

### Option A: Railway PostgreSQL
```bash
# Railway CLI
railway login
railway init
railway add postgresql
railway variables # Copy DATABASE_URL
```

### Option B: Supabase
1. Create project on supabase.com
2. Copy connection string from Settings → Database
3. Add to `.env` as `DATABASE_URL`

### Run Migrations
```bash
cd backend
alembic upgrade head
```

---

## Part 4: Deploy Backend (Railway)

### Via Railway CLI
```bash
cd backend

# Login and init
railway login
railway init

# Link to project
railway link

# Set environment variables
railway variables set GEMINI_API_KEY=your-key
railway variables set JWT_SECRET_KEY=your-secret
# ... set all other variables

# Deploy
railway up
```

### Via GitHub Integration
1. Push code to GitHub
2. Connect Railway to repository
3. Set environment variables in Railway dashboard
4. Deploy automatically on push

---

## Part 5: Deploy Frontend (Vercel)

### Via Vercel CLI
```bash
cd frontend

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Production deployment
vercel --prod
```

### Via Vercel Dashboard
1. Connect GitHub repository
2. Set Environment Variables:
   - `NEXT_PUBLIC_API_URL=https://your-backend.railway.app`
3. Deploy

---

## Part 6: Post-Deployment Checklist

### Verify Deployment
- [ ] Frontend loads at production URL
- [ ] Backend API responding at `/health`
- [ ] GitHub OAuth login works
- [ ] Can add repository
- [ ] Repository scan completes
- [ ] API documentation displays
- [ ] Webhook integration works

### Security Checklist
- [ ] All secrets in environment variables (not in code)
- [ ] CORS configured correctly
- [ ] HTTPS enabled on both frontend and backend
- [ ] JWT secret is strong (32+ characters)
- [ ] Database connection uses SSL
- [ ] Webhook secret configured

### Monitoring Setup
- [ ] Check Railway/Vercel logs
- [ ] Set up error alerting (optional: Sentry)
- [ ] Monitor database usage
- [ ] Monitor API response times

---

## Part 7: GitHub Webhook Configuration

For each repository you want to auto-document:

1. Go to repo Settings → Webhooks → Add webhook
2. **Payload URL:** `https://your-backend.railway.app/api/webhooks/github`
3. **Content type:** `application/json`
4. **Secret:** Same as `GITHUB_WEBHOOK_SECRET` in backend `.env`
5. **Events:** Just the push event
6. Click "Add webhook"

---

## Troubleshooting

### Frontend can't reach backend
- Check `NEXT_PUBLIC_API_URL` is correct
- Verify CORS_ORIGINS includes frontend URL
- Check backend is running

### OAuth callback not working
- Verify callback URL in GitHub OAuth app matches frontend URL
- Check FRONTEND_URL in backend .env

### Database connection fails
- Verify DATABASE_URL format: `postgresql://user:pass@host:port/db`
- Check database allows connections from deployment IP
- Ensure SSL mode if required

### Webhooks not triggering
- Verify webhook secret matches
- Check webhook delivery in GitHub repo settings
- Review backend logs for errors

---

## Scaling Considerations

### When you hit 100+ users:
- [ ] Upgrade database plan
- [ ] Add Redis for caching
- [ ] Consider Celery for background tasks
- [ ] Set up CDN for static assets

### Monitoring & Alerts:
- Railway/Vercel built-in monitoring
- Optional: Sentry for error tracking
- Optional: UptimeRobot for uptime monitoring

---

## Cost Estimates

### Development (Free Tier)
- Railway: Free $5 credit/month
- Vercel: Free for personal
- Supabase: Free tier
- Gemini: Free tier (1500 requests/day)

### Production (\~$50/month)
- Railway Hobby: $20/month
- Vercel Pro: $20/month (optional)
- Database: $10/month
- Domain: $1/month

---

## Support

**Issues?** Check:
1. Environment variables are set correctly
2. All services are running
3. Logs for error messages
4. `docs/TESTING_CHECKLIST.md` for verification

**Need help?** Check the README for development setup.
