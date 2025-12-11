# Quick Start Script for Windows
Write-Host "Starting API Auto-Documentation Platform..." -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
docker --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Docker is running" -ForegroundColor Green
Write-Host ""

# Check environment files
Write-Host "Checking environment files..." -ForegroundColor Yellow
if (-not (Test-Path ".\.env")) {
    Write-Host "[WARNING] .env file not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item ".\.env.example" ".\.env"
    Write-Host "[NOTE] Please edit .env and add your GEMINI_API_KEY" -ForegroundColor Cyan
}

if (-not (Test-Path ".\backend\.env")) {
    Write-Host "[WARNING] backend/.env not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item ".\backend\.env.example" ".\backend\.env"
}

if (-not (Test-Path ".\frontend\.env.local")) {
    Write-Host "[WARNING] frontend/.env.local not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item ".\frontend\.env.example" ".\frontend\.env.local"
}
Write-Host "[OK] Environment files ready" -ForegroundColor Green
Write-Host ""

# Start Docker Compose
Write-Host "Starting services with Docker Compose..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[SUCCESS] All services started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access your platform:" -ForegroundColor Cyan
    Write-Host "   Frontend:  http://localhost:3000" -ForegroundColor White
    Write-Host "   Backend:   http://localhost:8000" -ForegroundColor White
    Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Make sure you have added your GEMINI_API_KEY to .env" -ForegroundColor White
    Write-Host "   2. Open http://localhost:3000 in your browser" -ForegroundColor White
    Write-Host "   3. Add a GitHub repository to test API discovery" -ForegroundColor White
    Write-Host ""
    Write-Host "To view logs:" -ForegroundColor Cyan
    Write-Host "   docker-compose logs -f" -ForegroundColor White
    Write-Host ""
    Write-Host "To stop all services:" -ForegroundColor Cyan
    Write-Host "   docker-compose down" -ForegroundColor White
    Write-Host ""
}
else {
    Write-Host "[ERROR] Failed to start services. Check the error above." -ForegroundColor Red
    Write-Host "Try: docker-compose logs" -ForegroundColor Yellow
}
