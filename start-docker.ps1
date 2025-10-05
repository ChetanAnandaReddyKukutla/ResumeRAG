# ResumeRAG - Full Stack Startup Script
# This script starts all services using Docker Compose

Write-Host "🚀 Starting ResumeRAG Full Stack Application..." -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Error: Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Navigate to infra directory
Set-Location -Path "$PSScriptRoot\infra"

Write-Host "📦 Building and starting containers..." -ForegroundColor Yellow
Write-Host ""

# Stop any existing containers
docker-compose down

# Build and start all services
docker-compose up --build -d

Write-Host ""
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service health
Write-Host ""
Write-Host "📊 Service Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "✅ ResumeRAG is starting up!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Application URLs:" -ForegroundColor Cyan
Write-Host "   Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "   Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "   MinIO:     http://localhost:9001" -ForegroundColor White
Write-Host ""
Write-Host "📝 To view logs:          docker-compose -f infra/docker-compose.yml logs -f" -ForegroundColor Yellow
Write-Host "🛑 To stop services:      docker-compose -f infra/docker-compose.yml down" -ForegroundColor Yellow
Write-Host "🔄 To restart services:   docker-compose -f infra/docker-compose.yml restart" -ForegroundColor Yellow
Write-Host ""
Write-Host "⏰ Services may take 30-60 seconds to fully initialize..." -ForegroundColor Gray
