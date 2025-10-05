# Stop all ResumeRAG containers

Write-Host "🛑 Stopping ResumeRAG services..." -ForegroundColor Yellow

Set-Location -Path "$PSScriptRoot\infra"

docker-compose down

Write-Host ""
Write-Host "✅ All services stopped!" -ForegroundColor Green
