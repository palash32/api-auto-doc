# Testing Guide - Pre-Deployment

Use this guide to test your application before deploying to production.

## Services Status

### Backend
- **URL:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### Frontend  
- **URL:** http://localhost:3000

---

## Quick 10-Minute Test

Follow `docs/QUICK_TEST.md` for the complete flow:

### 1. Test Homepage
- ✅ Visit http://localhost:3000
- ✅ Verify beautiful landing page loads
- ✅ Check "Login with GitHub" button

### 2. Test Authentication
- ✅ Click "Login with GitHub"
- ✅ Authorize app
- ✅ Redirect to dashboard

### 3. Test Repository Adding
- ✅ Click "Add Repository"
- ✅ Enter repository URL
- ✅ Wait for scan
- ✅ Verify API count updates

### 4. Test API Viewer
- ✅ Navigate to /apis
- ✅ Select repository
- ✅ Search for endpoints
- ✅ Filter by method
- ✅ Click endpoint to view details

### 5. Test Editing
- ✅ Click "Edit Documentation"
- ✅ Change summary
- ✅ Add tags
- ✅ Save
- ✅ Verify persistence

---

## Check for Issues

### Common Issues

**Frontend won't load:**
- Check terminal for errors
- Verify `npm run dev` is running
- Check port 3000 not in use

**Backend API not responding:**
- Check http://localhost:8000/health
- Verify `.env` file exists
- Check database file exists

**OAuth not working:**
- Verify `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in `.env`
- Check callback URL matches GitHub OAuth settings

---

## Browser Console Debugging

Open browser DevTools (F12) and check:
- **Console** - No errors
- **Network** - API calls succeed (200 status)
- **Application > Local Storage** - Token stored after login

---

## Success Criteria

✅ Homepage loads without errors  
✅ Can log in with GitHub  
✅ Can add repository  
✅ Repository scan completes  
✅ Can view endpoints in /apis  
✅ Can search/filter endpoints  
✅ Can edit documentation  
✅ Changes persist after reload  

---

## Found a Bug?

Document in `docs/TESTING_CHECKLIST.md` under "Critical Bugs Found"

---

**Ready to deploy when all tests pass!** 🚀
