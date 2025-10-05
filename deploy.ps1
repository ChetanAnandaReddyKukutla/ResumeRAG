# Quick Deployment Script for Render + Vercel

Write-Host "🚀 ResumeRAG Deployment Helper" -ForegroundColor Cyan
Write-Host ""

# Check if git is clean
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "⚠️  Warning: You have uncommitted changes" -ForegroundColor Yellow
    Write-Host "Commit and push before deploying" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "📋 Deployment Checklist:" -ForegroundColor Cyan
Write-Host ""

$openaiKey = Read-Host "Do you have an OpenAI API key? (y/n)"
if ($openaiKey -eq 'y') {
    Write-Host "✅ OpenAI API key ready" -ForegroundColor Green
} else {
    Write-Host "❌ Get one from: https://platform.openai.com/api-keys" -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "🎯 Recommended Deployment: Render (Backend) + Vercel (Frontend)" -ForegroundColor Cyan
Write-Host ""

Write-Host "Backend Deployment (Render):" -ForegroundColor Yellow
Write-Host "1. Go to: https://dashboard.render.com/" -ForegroundColor White
Write-Host "2. Click 'New +' → 'Blueprint'" -ForegroundColor White
Write-Host "3. Connect your GitHub repo: ChetanAnandaReddyKukutla/ResumeRAG" -ForegroundColor White
Write-Host "4. Render will read render.yaml and create all services" -ForegroundColor White
Write-Host "5. Add your OPENAI_API_KEY in environment variables" -ForegroundColor White
Write-Host ""

Write-Host "Frontend Deployment (Vercel):" -ForegroundColor Yellow
Write-Host "1. Go to: https://vercel.com/new" -ForegroundColor White
Write-Host "2. Import Git Repository → ChetanAnandaReddyKukutla/ResumeRAG" -ForegroundColor White
Write-Host "3. Settings:" -ForegroundColor White
Write-Host "   - Framework: Vite" -ForegroundColor White
Write-Host "   - Root Directory: frontend" -ForegroundColor White
Write-Host "   - Build Command: npm run build" -ForegroundColor White
Write-Host "   - Output Directory: dist" -ForegroundColor White
Write-Host "4. Add environment variable:" -ForegroundColor White
Write-Host "   VITE_API_URL=<your-render-backend-url>" -ForegroundColor White
Write-Host "5. Click Deploy!" -ForegroundColor White
Write-Host ""

Write-Host "Alternative: Railway (One-Click Docker Deploy):" -ForegroundColor Yellow
Write-Host "1. Go to: https://railway.app" -ForegroundColor White
Write-Host "2. New Project → Deploy from GitHub" -ForegroundColor White
Write-Host "3. Select ResumeRAG repo" -ForegroundColor White
Write-Host "4. Railway auto-detects docker-compose.yml" -ForegroundColor White
Write-Host "5. Add OPENAI_API_KEY in variables" -ForegroundColor White
Write-Host "6. Deploy!" -ForegroundColor White
Write-Host ""

Write-Host "📚 Full deployment guide: DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
Write-Host ""

$deploy = Read-Host "Open deployment guides in browser? (y/n)"
if ($deploy -eq 'y') {
    Start-Process "https://dashboard.render.com"
    Start-Process "https://vercel.com/new"
    Write-Host "✅ Opened deployment dashboards" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 Good luck with your deployment!" -ForegroundColor Green
