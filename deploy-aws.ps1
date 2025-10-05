# AWS Elastic Beanstalk Quick Deploy Script
# Run this from the root of your repository

Write-Host "=== AWS Elastic Beanstalk Deployment ===" -ForegroundColor Green
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check AWS CLI
try {
    $awsVersion = aws --version 2>&1
    Write-Host "✓ AWS CLI installed: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ AWS CLI not installed" -ForegroundColor Red
    Write-Host "Install from: https://awscli.amazonaws.com/AWSCLIV2.msi" -ForegroundColor Yellow
    exit 1
}

# Check EB CLI
try {
    $ebVersion = eb --version 2>&1
    Write-Host "✓ EB CLI installed: $ebVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ EB CLI not installed" -ForegroundColor Red
    Write-Host "Install with: pip install awsebcli --upgrade --user" -ForegroundColor Yellow
    exit 1
}

# Check Docker
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "✓ Docker installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not installed or not running" -ForegroundColor Red
    Write-Host "Install Docker Desktop and make sure it's running" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "All prerequisites met!" -ForegroundColor Green
Write-Host ""

# Navigate to API directory
Set-Location -Path "api"
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host ""

# Step 1: Initialize EB (if not already done)
if (!(Test-Path ".elasticbeanstalk")) {
    Write-Host "Step 1: Initializing Elastic Beanstalk..." -ForegroundColor Yellow
    Write-Host "Please answer the prompts:" -ForegroundColor Cyan
    Write-Host "  - Region: 10 (eu-north-1)" -ForegroundColor Cyan
    Write-Host "  - Application Name: resumerag-api" -ForegroundColor Cyan
    Write-Host "  - Using Docker: Y" -ForegroundColor Cyan
    Write-Host "  - CodeCommit: n" -ForegroundColor Cyan
    Write-Host "  - SSH: n" -ForegroundColor Cyan
    Write-Host ""
    
    eb init
    
    Write-Host "✓ EB initialized" -ForegroundColor Green
} else {
    Write-Host "✓ EB already initialized" -ForegroundColor Green
}

Write-Host ""

# Step 2: Create environment
Write-Host "Step 2: Would you like to create a new EB environment?" -ForegroundColor Yellow
Write-Host "This will take 5-10 minutes and may incur AWS costs." -ForegroundColor Cyan
$createEnv = Read-Host "Create environment? (y/n)"

if ($createEnv -eq "y") {
    Write-Host "Creating environment 'resumerag-prod'..." -ForegroundColor Yellow
    eb create resumerag-prod --instance-type t3.micro --single
    
    Write-Host ""
    Write-Host "✓ Environment created!" -ForegroundColor Green
    
    # Step 3: Set environment variables
    Write-Host ""
    Write-Host "Step 3: Setting environment variables..." -ForegroundColor Yellow
    
    eb setenv `
        DATABASE_URL="YOUR_DATABASE_URL_FROM_RDS" `
        OPENAI_API_KEY="YOUR_OPENAI_API_KEY" `
        SECRET_KEY="YOUR_SECRET_KEY" `
        PII_ENC_KEY="YOUR_PII_ENC_KEY" `
        ALGORITHM="HS256" `
        ENVIRONMENT="production" `
        CORS_ALLOWED_ORIGINS="*" `
        PGVECTOR_DIM="1536" `
        USE_WORKER="false"
    
    Write-Host "✓ Environment variables set" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Deployment Complete! ===" -ForegroundColor Green
Write-Host ""

# Get status
Write-Host "Getting environment status..." -ForegroundColor Yellow
eb status

Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  eb status          - View environment status" -ForegroundColor White
Write-Host "  eb logs            - View application logs" -ForegroundColor White
Write-Host "  eb deploy          - Deploy code changes" -ForegroundColor White
Write-Host "  eb open            - Open app in browser" -ForegroundColor White
Write-Host "  eb ssh             - SSH into instance" -ForegroundColor White
Write-Host ""
Write-Host "Check your app: eb open" -ForegroundColor Green
Write-Host "View logs: eb logs" -ForegroundColor Green
