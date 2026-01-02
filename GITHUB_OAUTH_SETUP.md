# GitHub OAuth Configuration Guide

## Step 1: Create a GitHub OAuth App

1. **Go to GitHub Settings**
   - Visit: https://github.com/settings/developers
   - Click on "OAuth Apps" in the left sidebar
   - Click "New OAuth App"

2. **Fill in Application Details**
   ```
   Application Name: API Auto-Documentation Platform (Local Dev)
   Homepage URL: http://localhost:3000
   Authorization callback URL: http://localhost:3000/api/auth/callback/github
   ```

3. **Register the Application**
   - Click "Register application"
   - You'll be redirected to your app's settings page

4. **Get Your Credentials**
   - **Client ID**: Copy this value (visible on the page)
   - **Client Secret**: Click "Generate a new client secret" and copy it immediately
   
   ⚠️ **IMPORTANT**: Save the Client Secret somewhere safe - you won't be able to see it again!

## Step 2: Configure Environment Variables

Open your `.env` file and update these values:

```bash
# GitHub OAuth (for repository integration)
GITHUB_CLIENT_ID=your_actual_client_id_here
GITHUB_CLIENT_SECRET=your_actual_client_secret_here
GITHUB_REDIRECT_URI=http://localhost:3000/api/auth/callback/github
```

**Example:**
```bash
GITHUB_CLIENT_ID=Iv1.a1b2c3d4e5f6g7h8
GITHUB_CLIENT_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
GITHUB_REDIRECT_URI=http://localhost:3000/api/auth/callback/github
```

## Step 3: Restart Your Services

After updating the `.env` file, restart all services:

**Option 1: Using PowerShell (Recommended)**
```powershell
# Stop all services (Ctrl+C in each terminal)
# Then restart:

# Terminal 1 - Scanner
cd "services/scanner"
.\scanner.exe

# Terminal 2 - Gateway  
cd "services/gateway"
npm run dev

# Terminal 3 - Frontend
cd "frontend"
npm run dev
```

**Option 2: Using the start script**
```powershell
# Make sure all services are stopped first
.\start.ps1
```

## Step 4: Test GitHub OAuth

1. Open http://localhost:3000 in your browser
2. Click "Sign in with GitHub" or "Connect Repository"
3. You'll be redirected to GitHub to authorize the app
4. After authorization, you'll be redirected back to your app
5. You should now be able to add repositories!

## Troubleshooting

### "OAuth App not found" error
- Check that your `GITHUB_CLIENT_ID` in `.env` exactly matches the one from GitHub
- Make sure there are no extra spaces or quotes

### "Redirect URI mismatch" error
- Verify the callback URL in GitHub OAuth app settings matches exactly:
  - GitHub setting: `http://localhost:3000/api/auth/callback/github`
  - .env setting: `GITHUB_REDIRECT_URI=http://localhost:3000/api/auth/callback/github`

### Services not picking up new environment variables
- Make sure you completely stopped and restarted the services
- Check that the `.env` file is in the root directory
- Verify there are no syntax errors in the `.env` file (no extra quotes, spaces, etc.)

### Still not working?
- Check the browser console (F12) for errors
- Check the Gateway service logs for error messages
- Ensure all services are running on the correct ports:
  - Frontend: http://localhost:3000
  - Gateway: http://localhost:8000
  - Scanner: http://localhost:3001

## What Happens After Setup

Once GitHub OAuth is configured, you'll be able to:
- ✅ Authenticate with your GitHub account
- ✅ Access your public and private repositories
- ✅ Clone repositories for scanning
- ✅ Use your GitHub token for API rate limit increases
- ✅ Scan repositories that require authentication

## Security Notes

- **Never commit** your `.env` file to git (it's already in `.gitignore`)
- **Keep your Client Secret private** - treat it like a password
- For production, create a separate OAuth app with production URLs
- Consider using environment-specific OAuth apps (dev, staging, prod)

## Production Setup

When deploying to production, create a new OAuth app with:
```
Homepage URL: https://your-production-domain.com
Authorization callback URL: https://your-production-domain.com/api/auth/callback/github
```

Then update your production environment variables accordingly.
