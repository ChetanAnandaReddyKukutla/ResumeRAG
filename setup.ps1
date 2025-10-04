# ResumeRAG Setup and Run Script for Windows PowerShell

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "ResumeRAG Phase 1 MVP - Quick Start" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python installed: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check if Docker is installed
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
$dockerVersion = docker --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker installed: $dockerVersion" -ForegroundColor Green
    $useDocker = $true
} else {
    Write-Host "! Docker not found. Will use local setup." -ForegroundColor Yellow
    $useDocker = $false
}

Write-Host ""
Write-Host "Choose setup method:" -ForegroundColor Cyan
Write-Host "1. Docker Compose (recommended)" -ForegroundColor White
Write-Host "2. Local development setup" -ForegroundColor White
$choice = Read-Host "Enter choice (1 or 2)"

if ($choice -eq "1" -and $useDocker) {
    Write-Host ""
    Write-Host "Starting Docker Compose setup..." -ForegroundColor Cyan
    
    # Start Docker Compose
    Set-Location infra
    docker-compose up -d
    
    Write-Host ""
    Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Run migrations
    Write-Host "Running database migrations..." -ForegroundColor Yellow
    docker exec resumerag_api alembic upgrade head
    
    # Seed database
    Write-Host "Seeding database..." -ForegroundColor Yellow
    docker exec resumerag_api python scripts/seed_data.py
    
    Write-Host ""
    Write-Host "✓ ResumeRAG is running!" -ForegroundColor Green
    Write-Host "  API: http://localhost:8000" -ForegroundColor White
    Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
    Write-Host ""
    Write-Host "To stop: cd infra && docker-compose down" -ForegroundColor Yellow
    
} elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "Setting up local development environment..." -ForegroundColor Cyan
    
    # Check PostgreSQL
    Write-Host ""
    Write-Host "⚠ Prerequisites for local setup:" -ForegroundColor Yellow
    Write-Host "  1. PostgreSQL 14+ with pgvector extension" -ForegroundColor White
    Write-Host "  2. Redis server running" -ForegroundColor White
    Write-Host "  3. Node.js 18+ installed" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Do you have these prerequisites? (y/n)"
    
    if ($continue -ne "y") {
        Write-Host "Please install prerequisites and run this script again." -ForegroundColor Red
        exit 1
    }
    
    # Backend setup
    Write-Host ""
    Write-Host "Setting up backend..." -ForegroundColor Cyan
    Set-Location api
    
    # Create virtual environment
    if (-not (Test-Path "venv")) {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        python -m venv venv
    }
    
    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    .\venv\Scripts\Activate.ps1
    
    # Install dependencies
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    
    # Copy .env file if it doesn't exist
    if (-not (Test-Path "..\.env")) {
        Write-Host "Creating .env file..." -ForegroundColor Yellow
        Copy-Item ..\infra\env.example ..\.env
        Write-Host "⚠ Please edit .env file with your database credentials!" -ForegroundColor Yellow
    }
    
    # Run migrations
    Write-Host "Running database migrations..." -ForegroundColor Yellow
    alembic upgrade head
    
    # Seed database
    Write-Host "Seeding database..." -ForegroundColor Yellow
    Set-Location ..
    python scripts\seed_data.py
    
    # Frontend setup
    Write-Host ""
    Write-Host "Setting up frontend..." -ForegroundColor Cyan
    Set-Location frontend
    
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
        npm install
    }
    
    Write-Host ""
    Write-Host "✓ Setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To start the application:" -ForegroundColor Cyan
    Write-Host "  1. Start API: cd api && .\venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload" -ForegroundColor White
    Write-Host "  2. Start Frontend: cd frontend && npm run dev" -ForegroundColor White
    Write-Host ""
    Write-Host "API will be at: http://localhost:8000" -ForegroundColor White
    Write-Host "Frontend will be at: http://localhost:3000" -ForegroundColor White
    
} else {
    Write-Host "Invalid choice. Exiting." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Test Users:" -ForegroundColor Cyan
Write-Host "  - recruiter@example.com / Recruiter@123 (recruiter)" -ForegroundColor White
Write-Host "  - alice@example.com / Alice@123 (user)" -ForegroundColor White
Write-Host "  - bob@example.com / Bob@123 (user)" -ForegroundColor White
Write-Host ""
