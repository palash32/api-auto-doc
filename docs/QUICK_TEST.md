# Quick Test Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Start the Platform

```powershell
# Run the startup script
.\start.ps1
```

Or manually:
```powershell
docker-compose up -d
```

### Step 2: Set Your Gemini API Key

Edit the `.env` file and add your Gemini API key:
```bash
GEMINI_API_KEY=AIzaSy...your-key-here
```

Get your key at: https://makersuite.google.com/app/apikey

### Step 3: Open the Platform

Visit **http://localhost:3000** in your browser

### Step 4: Test API Discovery

1. Click **"Add Repository"** button
2. Enter a public GitHub repository URL (e.g., `https://github.com/tiangolo/fastapi`)
3. Wait for the scan to complete
4. View discovered APIs in the dashboard!

---

## 🧪 What to Test

### 1. Repository Scanning
- ✅ Add a repository with FastAPI endpoints
- ✅ Check if APIs are discovered correctly
- ✅ View AI-generated documentation

### 2. API Documentation
- ✅ Click on an discovered API endpoint
- ✅ Verify the documentation looks good
- ✅ Check if parameters are detected

### 3. GitHub Integration
- ✅ Test with Python repositories (FastAPI, Flask)
- ✅ Test with Node.js repositories (Express)

---

## 📊 Check Services Status

```powershell
# View all running containers
docker-compose ps

# View backend logs
docker-compose logs -f backend

# View frontend logs
docker-compose logs -f frontend
```

---

## 🐛 Troubleshooting

### Service won't start?
```powershell
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Full reset
docker-compose down
docker-compose up -d
```

### Can't connect to database?
```powershell
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart database
docker-compose restart postgres
```

### Frontend errors?
```powershell
# Check if backend is accessible
curl http://localhost:8000/health

# Restart frontend
docker-compose restart frontend
```

---

## 🎯 Test Public Repositories

Try scanning these repositories to test the platform:

1. **FastAPI Official Repo**
   ```
   https://github.com/tiangolo/fastapi
   ```

2. **Your Own Repositories** (if public)

3. **Sample Express.js API**
   ```
   https://github.com/expressjs/express
   ```

---

## 📝 Expected Results

After scanning a repository, you should see:
- ✅ List of discovered API endpoints
- ✅ HTTP methods (GET, POST, PUT, DELETE)
- ✅ Endpoint paths
- ✅ AI-generated descriptions
- ✅ Repository details

---

## 🚀 Next Steps

Once basic testing works:
1. Configure GitHub OAuth for private repos
2. Test web hook integration
3. Try the monitoring features
4. Explore the dependency graph

---

## 💡 Pro Tips

- **Scan smaller repos first** - Faster results
- **Check Docker logs** if something fails
- **Use a real Python/Node.js project** - Better AI documentation
- **Free Gemini tier has rate limits** - Don't scan too many repos at once

---

## 🛑 Stop the Platform

```powershell
docker-compose down
```

To remove all data:
```powershell
docker-compose down -v
```

---

**Happy Testing! 🎉**

Need help? Check:
- Backend API docs: http://localhost:8000/docs
- Logs: `docker-compose logs -f`
- GitHub Issues: Report problems on GitHub
