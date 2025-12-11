# Quick Start Guide

## 🚀 Start the Backend (Easiest Method)

### Windows PowerShell:

```powershell
cd "C:\Users\UniSpark\API Auto-Documentation Platform\backend"
.\start-backend.ps1
```

The script will:
1. ✅ Check & start PostgreSQL and Redis if needed
2. 🔑 Prompt for your Gemini API key (first time only)
3. ⚙️ Set all environment variables automatically
4. 🌐 Start the backend server on http://localhost:8000

### Access Your API:
- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

---

## 📋 What's Running

After starting, you'll have:
- ✅ **PostgreSQL** on localhost:5432
- ✅ **Redis** on localhost:6379  
- ✅ **Backend API** on localhost:8000

## 🔑 Your Gemini API Key

Get your free API key from:
https://makersuite.google.com/app/apikey

The script will ask for it the first time you run it.

## 🛑 Stop the Server

Press `Ctrl+C` in the terminal to stop the backend.

To stop databases:
```powershell
docker stop apidoc-postgres apidoc-redis
```

---

## 🎯 Next Steps

1. **Test the API**: Visit http://localhost:8000/docs
2. **Start Frontend** (in a new terminal):
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
3. **Access Full App**: http://localhost:3000

## ❓ Troubleshooting

### "Docker not running"
Start Docker Desktop and wait for it to initialize.

### "Port 8000 already in use"
Kill existing processes on port 8000:
```powershell
netstat -ano | findstr :8000
# Note the PID, then:
taskkill /PID <PID> /F
```

### "Cannot find python"
Make sure Python 3.13+ is installed and in your PATH.
