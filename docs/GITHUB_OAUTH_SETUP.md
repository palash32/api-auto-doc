# GitHub OAuth Setup Guide

## Issue: GitHub Authentication Not Working

The platform requires GitHub OAuth credentials to enable repository integration and user login via GitHub.

---

## 📝 Step 1: Create GitHub OAuth App

1. **Log in to GitHub**: https://github.com/settings/developers
2. **Create New OAuth App**:
   - Click "New OAuth App" (or "Register a new application")

3. **Fill in the details**:
   ```
   Application name: API Auto-Documentation Platform (Local)
   Homepage URL: http://localhost:3000
   Application description: API discovery and documentation platform
   Authorization callback URL: http://localhost:8000/api/auth/github/callback
   ```

4. **Click "Register application"**

5. **Copy your credentials**:
   - **Client ID**: You'll see this immediately (looks like: `Iv1.1a2b3c4d5e6f7g8h`)
   - **Client Secret**: Click "Generate a new client secret" and copy it immediately (looks like: `1a2b3c4d5e6f7g8h9i0j...`)

---

## 🔧 Step 2: Configure Environment Variables

Edit your `.env` file (in the root directory):

```bash
# GitHub OAuth
GITHUB_CLIENT_ID=Iv1.your-actual-client-id-here
GITHUB_CLIENT_SECRET=your-actual-client-secret-here
GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/github/callback
```

Also edit `backend/.env`:

```bash
# GitHub OAuth
GITHUB_CLIENT_ID=Iv1.your-actual-client-id-here
GITHUB_CLIENT_SECRET=your-actual-client-secret-here  
GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/github/callback
```

---

## 🔄 Step 3: Restart Backend

After adding credentials, restart the backend:

```powershell
docker-compose restart backend
```

Wait 5-10 seconds for it to reload.

---

## ✅ Step 4: Test GitHub OAuth

### Option A: Test Login Flow (Full OAuth)

1. Open http://localhost:3000
2. Click "Login with GitHub" or similar button
3. Should redirect to GitHub for authorization
4. After authorizing, should redirect back with token

### Option B: Test Direct Backend Endpoint

```powershell
Start-Process "http://localhost:8000/api/auth/github/login"
```

This should redirect you to GitHub's authorization page.

---

## 🔍 Troubleshooting

### Error: "GitHub OAuth not configured"

**Problem**: Backend can't find GITHUB_CLIENT_ID  
**Solution**:
1. Verify `.env` and `backend/.env` have the credentials
2. Restart backend: `docker-compose restart backend`
3. Check backend logs: `docker-compose logs backend | Select-String -Pattern "GITHUB"`

### Error: "redirect_uri_mismatch"

**Problem**: GitHub callback URL doesn't match  
**Solution**:
1. In GitHub OAuth settings, ensure callback URL is exactly:
   ```
   http://localhost:8000/api/auth/github/callback
   ```
2. No trailing slash, no extra paths

### Error: "Bad verification code"

**Problem**: OAuth code expired or already used  
**Solution**: Try the login flow again (codes expire quickly)

### Error: "Application suspended"

**Problem**: GitHub app not approved or suspended  
**Solution**: Check GitHub OAuth app status at https://github.com/settings/developers

---

## 📊 What Happens During OAuth Flow

1. **User initiates**: Clicks "Login with GitHub"
2. **Redirect to GitHub**: User sees GitHub authorization page
3. **User authorizes**: Grants permissions (read user, repos)
4. **GitHub redirects back**: Sends authorization code to `/api/auth/github/callback`
5. **Backend exchanges code**: Gets access token from GitHub
6. **Backend fetches user**: Gets user info from GitHub API
7. **Create/update user**: Stores user in database
8. **Return JWT**: Backend creates app-specific JWT token
9. **Redirect to frontend**: With JWT token in URL
10. **Frontend saves token**: Stores in localStorage/cookies

---

## 🧪 Testing Without GitHub OAuth (Alternative)

If you want to test without setting up GitHub OAuth, you can:

1. **Use plain repository URLs**: Just add public repos by URL (no authentication needed for public repos)
2. **Disable OAuth temporarily**: Comment out OAuth requirements in frontend

---

## 🔐 Security Notes

- **Never commit**: Don't commit `.env` files with real credentials to git
- **Use different apps**: Create separate GitHub OAuth apps for dev/staging/production
- **Rotate secrets**: If secrets are exposed, regenerate them in GitHub settings
- **HTTPS in production**: Use HTTPS callback URLs in production (not HTTP)

---

## 📝 Scopes Requested

The platform requests these GitHub scopes:

- `read:user` - Read user profile information
- `repo` - Read/write access to repositories (needed to clone and scan)

If you want read-only access, you can change the scope in `backend/app/api/auth.py`:
```python
scope = "read:user public_repo"  # Only public repos
```

---

## ✨ Expected Result

After successful setup:

1. ✅ `/api/auth/github/login` redirects to GitHub
2. ✅ After authorization, redirects back to app
3. ✅ User is logged in with JWT token
4. ✅ Can add private repositories (if scope allows)
5. ✅ Backend can clone and scan repositories

---

## 🔗 Useful Links

- GitHub OAuth Docs: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps
- Manage OAuth Apps: https://github.com/settings/developers
- Test OAuth Flow: https://github-oauth-playground.vercel.app/

---

## Need Help?

Check the backend logs:
```powershell
docker-compose logs -f backend
```

Look for lines containing "GitHub", "OAuth", or "authentication".
