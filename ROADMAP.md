# API Documentation Platform - 8-Week MVP Roadmap
**Apple PM Philosophy: "Focus. Simplicity. Excellence."**

## 🎯 MVP Scope (What We're Building)

### ✅ IN SCOPE (v1.0)
- GitHub OAuth login
- Python FastAPI auto-discovery only
- AI-generated docs (Gemini Pro)
- Basic health checks (4-hour intervals)
- Beautiful UI (Apple-grade polish)
- Search & filter (client-side)

### ❌ OUT OF SCOPE (v2.0+)
- Multi-language support
- Real-time monitoring
- Team collaboration
- Visual dependency maps
- RBAC
- Natural language search

**Tagline:** "Scan. Document. Done. For Python APIs."

---

## 📅 4-Phase Development Plan

### Phase 1: FOUNDATION (Weeks 1-2)
**Goal:** Rock-solid infrastructure

#### Week 1: Backend Skeleton
**Task 1.1: Database Setup** (Day 1)
- PostgreSQL schema: users, repositories, api_endpoints
- SQLAlchemy ORM + Alembic migrations
- Indexes on foreign keys
- Test: `alembic upgrade head` works

**Task 1.2: GitHub OAuth Flow** (Days 2-3)
- `/auth/github/login` - redirect to GitHub
- `/auth/github/callback` - exchange code for token
- `/auth/me` - protected endpoint
- Store encrypted access tokens
- Test: Login flow works end-to-end

**Task 1.3: Repository Scanner Foundation** (Days 4-5)
- Python AST parser for FastAPI endpoints
- Extract: path, method, docstring
- Handle syntax errors gracefully
- Test: Parse sample FastAPI repo

#### Week 2: AI Integration & Basic Frontend
**Task 1.4: Gemini AI Doc Generator** (Days 6-7)
- Generate endpoint descriptions
- Temperature=0.3 (low hallucination)
- Redis caching
- Retry logic with exponential backoff
- Test: Generate docs for 5 test endpoints

**Task 1.5: Frontend Setup** (Days 8-10)
- Next.js 14 dashboard page
- Repository list with stats
- API endpoint table
- React Query for data fetching
- Test: Dashboard loads with mock data <1s

---

### Phase 2: CORE FEATURES (Weeks 3-5)
**Goal:** End-to-end functionality

#### Week 3: Repository Scanning Pipeline
**Task 2.1: GitHub Repository Cloner** (Days 11-12)
- Clone to temp directory
- Shallow clone (depth=1)
- Validate repo size <100MB
- Auto-cleanup after 1 hour
- Test: Clone public and private repos

**Task 2.2: Celery Task Queue** (Days 13-14)
- Background scanning tasks
- Progress updates via Redis
- Task status endpoint
- Error handling and retries
- Test: Trigger scan, poll status

#### Week 4: API Endpoints
**Task 2.3: RESTful API Endpoints** (Days 15-17)
- GET/POST `/api/repositories`
- GET `/api/repositories/{id}/endpoints`
- PATCH `/api/endpoints/{id}` (manual edits)
- Pagination and filtering
- Test: Full CRUD operations

**Task 2.4: Basic Health Monitoring** (Days 18-19)
- Ping endpoints, measure latency
- Update status: healthy/warning/error
- Scheduled checks every 4 hours (Celery Beat)
- Store health history (30 days)
- Test: Manual and scheduled health checks

#### Week 5: Frontend Integration
**Task 2.5: Connect Frontend to Backend** (Days 20-22)
- API client with TypeScript types
- Dashboard with real data
- "Scan Repository" modal with progress
- Expandable endpoint rows
- Search and filter
- Test: Complete user flow works

---

### Phase 3: POLISH & UX (Weeks 6-7)
**Goal:** Apple-quality experience

#### Week 6: UI Polish
**Task 3.1: Design System** (Days 23-25)
- Consistent color palette
- Typography hierarchy
- Reusable components (StatusBadge, MethodBadge, EmptyState)
- 8px grid spacing
- Test: No random colors/sizes

**Task 3.2: Micro-Interactions** (Days 26-27)
- Button hover effects (scale, shadow)
- Loading skeletons with shimmer
- Toast notifications (Framer Motion)
- Status indicator animations (pulse)
- Test: 60fps animations, no jank

#### Week 7: Onboarding
**Task 3.3: Guided Onboarding** (Days 28-29)
- 3-step flow: Welcome → Select repos → Processing
- Confetti on success
- Empty states
- Test: New user completes onboarding

**Task 3.4: Error Handling** (Day 30)
- Error boundaries
- User-friendly messages
- Retry buttons
- Form validation
- Test: Break the app, should never crash

---

### Phase 4: LAUNCH (Week 8)
**Goal:** Ship with confidence

#### Week 8: Testing & Deployment
**Task 4.1: Testing** (Days 31-32)
- Backend: pytest, 70%+ coverage
- Frontend: Jest + React Testing Library
- E2E: Playwright critical flows
- Manual testing checklist
- Test: All tests pass on CI

**Task 4.2: Production Deployment** (Days 33-35)
- Frontend: Vercel
- Backend: Railway (Web + Worker + PostgreSQL + Redis)
- Environment variables
- SSL/HTTPS
- Monitoring: Sentry + UptimeRobot
- Test: Production works end-to-end

---

## 📊 Quality Gates (Must Pass Before Next Task)

### Gate 1: Code Runs Locally
✅ No syntax errors  
✅ Server starts without crashes  
✅ Page renders without errors

### Gate 2: Feature Works End-to-End
✅ Manual test passes  
✅ No errors in logs  
✅ Edge cases handled

### Gate 3: Code Quality
✅ TypeScript: no 'any' types  
✅ Python: type hints  
✅ No console.log/print  
✅ Functions have docstrings

### Gate 4: User Experience
✅ Loading states visible  
✅ Error messages user-friendly  
✅ Mobile responsive  
✅ Immediate feedback on actions

### Gate 5: Performance
✅ Page loads <2s (3G throttled)  
✅ Animations at 60fps  
✅ API responses <500ms

---

## 📈 Progress Tracking

### Daily Log Template
```markdown
## 2025-11-25

### Completed
- ✅ Task 1.1: Database setup
  - Commit: abc123f
  - Quality gates: 5/5 passed

### Blockers
- None

### Tomorrow
- Task 1.2: GitHub OAuth (4-6 hours)
```

### Weekly Review Checklist
- [ ] Tasks completed vs. planned
- [ ] Quality metrics (coverage, bugs, performance)
- [ ] Risk assessment (behind schedule? technical debt?)
- [ ] Next week priorities

---

## 🎯 Success Definition

### MVP is DONE when:
✅ Stranger can signup → scan → view docs (no help needed)  
✅ Handles 10 concurrent users  
✅ Runs without daily manual fixes  
✅ First paying customer successful  
✅ 99%+ uptime for 7 days

### MVP is NOT done if:
❌ Manual fixes needed daily  
❌ Error rate >5%  
❌ Embarrassed to show it  
❌ "One more feature" syndrome

---

## 💰 Budget Breakdown

### Development ($1-2/month)
- Railway free tier
- Gemini Pro free tier
- Domain: $1/month

### Launch ($50-75/month)
- Railway Hobby: $15/month
- Database upgrade: $10/month
- Sentry: $26/month

### Scale at $2,500 MRR ($500/month)
- Railway Pro: $80/month
- Database 4GB: $50/month
- Monitoring: $100/month
- Support: $39/month
- Marketing: $200/month

---

## ⏱️ Realistic Timeline

**Original:** 8 weeks  
**Realistic:** 10-12 weeks (includes bugs, learning, life)

**Buffer allocation:**
- Weeks 1-2: +2 days (learning curve)
- Weeks 3-5: +3 days (AI hallucinations)
- Weeks 6-7: +2 days (polish takes longer)
- Week 8: +3 days (deployment surprises)

**Total:** 66 days (9.5 weeks)

**Rule:** Whatever estimate, multiply by 1.5x

---

## 🚀 Post-Launch: First 30 Days

### Week 1: Survive
- Monitor errors 24/7
- Fix critical bugs <4 hours
- Support emails <12 hours
- Goal: Keep first 10 users

### Week 2: Learn
- User interviews (5 active users)
- Track feature usage
- Goal: Understand what matters

### Week 3: Improve
- Fix top 3 complaints
- Add most-requested feature (<1 week work)
- Goal: Increase activation rate

### Week 4: Grow
- Share success stories
- Referral incentive
- Goal: 50 users

---

## 🍎 The Apple Standard

**Ship when:**
1. Solves ONE problem really well
2. You'd pay for it yourself
3. Core flow works flawlessly
4. You're 80% proud (not 100% - that's perfectionism)

**Then:** Get users, get feedback, iterate.

---

**Remember:** Every giant product started as a messy MVP. Your job is to ship, learn, and improve. Not perfection.
