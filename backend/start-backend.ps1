# API Auto-Documentation Platform - Backend Startup Script
Write-Host ""
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host " API Auto-Documentation Platform - Backend Server" -ForegroundColor Green
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host ""

# Check databases
Write-Host "Checking database services..." -ForegroundColor Yellow
$postgresCheck = docker ps --filter "name=apidoc-postgres" --format "{{.Names}}"
$redisCheck = docker ps --filter "name=apidoc-redis" --format "{{.Names}}"

if (-not $postgresCheck) {
    Write-Host "Starting PostgreSQL..." -ForegroundColor Yellow
    docker run -d --name apidoc-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=apidoc -p 5432:5432 postgres:16-alpine | Out-Null
    Start-Sleep -Seconds 3
}

if (-not $redisCheck) {
    Write-Host "Starting Redis..." -ForegroundColor Yellow
    docker run -d --name apidoc-redis -p 6379:6379 redis:7-alpine | Out-Null
    Start-Sleep -Seconds 2
}

Write-Host "OK PostgreSQL on localhost:5432" -ForegroundColor Green
Write-Host "OK Redis on localhost:6379" -ForegroundColor Green
Write-Host ""

# Set environment variables
Write-Host "Configuring environment..." -ForegroundColor Yellow

$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/apidoc"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:CELERY_BROKER_URL = "redis://localhost:6379/0"
$env:CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
$env:GEMINI_MODEL = "gemini-pro"
$env:JWT_SECRET_KEY = "dev-jwt-secret-key-12345-change-in-production"
$env:JWT_ALGORITHM = "HS256"
$env:JWT_ACCESS_TOKEN_EXPIRE_MINUTES = "30"
$env:JWT_REFRESH_TOKEN_EXPIRE_DAYS = "7"
$env:FRONTEND_URL = "http://localhost:3000"
$env:ENVIRONMENT = "development"
Remove-Item Env:\CORS_ORIGINS -ErrorAction SilentlyContinue
$env:PROMETHEUS_ENABLED = "true"

# Check for Gemini API key
if (Test-Path ".env.disabled") {
    $envContent = Get-Content ".env.disabled"
    $geminiLine = $envContent | Select-String "GEMINI_API_KEY="
    if ($geminiLine) {
        $keyValue = $geminiLine -replace "GEMINI_API_KEY=", ""
        $keyValue = $keyValue.Trim()
        if ($keyValue -and $keyValue -ne "your-gemini-api-key-here") {
            $env:GEMINI_API_KEY = $keyValue
            Write-Host "OK Gemini API key loaded from .env.disabled" -ForegroundColor Green
        }
    }
}

if (-not $env:GEMINI_API_KEY -or $env:GEMINI_API_KEY -eq "your-gemini-api-key-here") {
    Write-Host ""
    Write-Host "Enter your Gemini API Key:" -ForegroundColor Cyan
    Write-Host "(Or press Enter to skip - AI features will not work)" -ForegroundColor Gray
    $apiKey = Read-Host "API Key"
    if ($apiKey) {
        $env:GEMINI_API_KEY = $apiKey
    }
    else {
        $env:GEMINI_API_KEY = "placeholder"
        Write-Host "WARNING: Gemini API key not set" -ForegroundColor Yellow
    }
}

Write-Host "OK Environment configured" -ForegroundColor Green
Write-Host ""

# Sync root .env to backend .env
if (Test-Path "..\.env") {
    Write-Host "Syncing .env from root directory..." -ForegroundColor Yellow
    Copy-Item "..\.env" -Destination ".env" -Force
    # Remove CORS_ORIGINS and ALLOWED_HOSTS from .env to avoid parsing errors
    (Get-Content ".env") | Where-Object { $_ -notmatch "^CORS_ORIGINS=" -and $_ -notmatch "^ALLOWED_HOSTS=" } | Set-Content ".env"
    
    $checkEnv = Get-Content ".env" | Select-String "GITHUB_CLIENT_ID="
    Write-Host "DEBUG: Content in backend/.env: $checkEnv" -ForegroundColor Magenta
    
    Write-Host "OK .env synced and sanitized" -ForegroundColor Green
}

# Start server
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host " Starting Backend Server on http://localhost:8000" -ForegroundColor Green
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "DEBUG: Final env:GITHUB_CLIENT_ID = $env:GITHUB_CLIENT_ID" -ForegroundColor Magenta
Write-Host ""
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
