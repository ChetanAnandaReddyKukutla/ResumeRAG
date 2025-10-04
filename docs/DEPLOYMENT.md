# Deployment Guide

Complete guide for deploying ResumeRAG to production environments.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Backend Deployment (Render)](#backend-deployment-render)
- [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
- [Database Setup](#database-setup)
- [CI/CD Pipeline](#cicd-pipeline)
- [Post-Deployment Validation](#post-deployment-validation)
- [Troubleshooting](#troubleshooting)

---

## Overview

ResumeRAG deployment consists of three main components:

1. **Backend API** - FastAPI application (Render/Railway/Google Cloud Run)
2. **Frontend** - React application (Vercel/Netlify)
3. **Services** - PostgreSQL, Redis (managed services)

**Recommended Stack**:
- Backend: [Render](https://render.com) (free tier available)
- Frontend: [Vercel](https://vercel.com) (free tier for hobby projects)
- Database: [Supabase](https://supabase.com) or [Neon](https://neon.tech) (PostgreSQL with pgvector)
- Redis: [Upstash](https://upstash.com) or Redis Cloud (free tier)

---

## Prerequisites

### Required Accounts
- GitHub account (for CI/CD)
- Render account (or alternative: Railway, GCP)
- Vercel account
- PostgreSQL provider account (Supabase/Neon)
- Redis provider account (Upstash)

### Required Tools
- Git
- Docker (for local testing)
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend build)

---

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/resumerag
PGVECTOR_EXTENSION=true

# Redis
REDIS_URL=redis://default:password@host:6379/0

# Security
SECRET_KEY=your-secret-key-min-32-chars
FERNET_KEY=your-fernet-key-base64-32-bytes

# JWT Configuration
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ALLOWED_ORIGINS=https://resumerag-demo.vercel.app,http://localhost:5173

# File Upload
UPLOAD_DIR=/tmp/uploads
MAX_FILE_SIZE_MB=10

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Observability
ENVIRONMENT=production
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_EXPORTER_OTLP_INSECURE=true

# Optional: S3 Storage (for production file storage)
S3_BUCKET=resumerag-uploads
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### Frontend (.env)

```bash
# API Endpoint
VITE_API_BASE_URL=https://resumerag-api.onrender.com

# Optional: Analytics
VITE_GA_TRACKING_ID=G-XXXXXXXXXX
```

### Generate Secrets

```bash
# Generate SECRET_KEY (Python)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate FERNET_KEY (Python)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Backend Deployment (Render)

### Option 1: Web Dashboard

1. **Sign up at [Render](https://render.com)**

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository: `ResumeRAG`

3. **Configure Service**
   - **Name**: `resumerag-api`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `api`
   - **Environment**: `Python 3.11`
   - **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or Starter for production)

4. **Add Environment Variables**
   - Go to "Environment" tab
   - Add all variables from [Backend .env section](#backend-env)
   - Use "Add from .env" feature if available

5. **Deploy**
   - Click "Create Web Service"
   - Wait for build (5-10 minutes)
   - Check logs for errors

6. **Note Your API URL**
   - Example: `https://resumerag-api.onrender.com`
   - Test: `https://resumerag-api.onrender.com/api/health`

### Option 2: render.yaml (Infrastructure as Code)

Create `render.yaml` in project root:

```yaml
services:
  - type: web
    name: resumerag-api
    env: python
    region: oregon
    plan: free
    buildCommand: cd api && pip install -r requirements.txt && alembic upgrade head
    startCommand: cd api && uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: REDIS_URL
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: FERNET_KEY
        generateValue: true
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: CORS_ALLOWED_ORIGINS
        value: https://resumerag-demo.vercel.app
    healthCheckPath: /api/health

databases:
  - name: resumerag-db
    plan: free
    databaseName: resumerag
    user: resumerag
```

Deploy:
```bash
# Install Render CLI
brew install render  # macOS
# or download from https://render.com/docs/cli

# Login
render login

# Deploy
render blueprint deploy
```

### Option 3: Docker Deployment (Railway/GCP)

**Railway**:
1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Initialize: `railway init`
4. Deploy: `railway up`

**Google Cloud Run**:
```bash
# Build Docker image
docker build -t gcr.io/your-project/resumerag-api ./api

# Push to GCR
docker push gcr.io/your-project/resumerag-api

# Deploy
gcloud run deploy resumerag-api \
  --image gcr.io/your-project/resumerag-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Frontend Deployment (Vercel)

### Option 1: Vercel Dashboard

1. **Sign up at [Vercel](https://vercel.com)**

2. **Import Project**
   - Click "Add New..." → "Project"
   - Import from GitHub: `ResumeRAG`

3. **Configure Project**
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

4. **Environment Variables**
   - Add `VITE_API_BASE_URL=https://resumerag-api.onrender.com`

5. **Deploy**
   - Click "Deploy"
   - Wait for build (2-5 minutes)
   - Access at: `https://resumerag-demo.vercel.app`

### Option 2: Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy (from frontend directory)
cd frontend
vercel --prod

# Set environment variable
vercel env add VITE_API_BASE_URL production
# Enter: https://resumerag-api.onrender.com
```

### Option 3: vercel.json Configuration

Create `vercel.json` in `frontend/`:

```json
{
  "version": 2,
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "vite",
  "outputDirectory": "dist",
  "env": {
    "VITE_API_BASE_URL": "https://resumerag-api.onrender.com"
  },
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

Deploy:
```bash
vercel --prod
```

---

## Database Setup

### Option 1: Supabase (Recommended)

1. **Create Project at [Supabase](https://supabase.com)**
   - Name: `resumerag`
   - Region: Choose closest to API server
   - Database password: Generate strong password

2. **Enable pgvector Extension**
   ```sql
   -- Run in SQL Editor
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. **Get Connection String**
   - Go to Settings → Database
   - Copy "Connection string" (URI format)
   - Example: `postgresql://postgres:password@db.xxx.supabase.co:5432/postgres`

4. **Convert to asyncpg format**
   ```
   postgresql+asyncpg://postgres:password@db.xxx.supabase.co:5432/postgres
   ```

5. **Run Migrations**
   ```bash
   # Set DATABASE_URL
   export DATABASE_URL="postgresql+asyncpg://..."
   
   # Run Alembic migrations
   cd api
   alembic upgrade head
   ```

### Option 2: Neon

1. **Create Project at [Neon](https://neon.tech)**
2. **Enable pgvector**:
   ```sql
   CREATE EXTENSION vector;
   ```
3. **Get connection string** from dashboard
4. **Run migrations** as above

### Option 3: Self-Hosted PostgreSQL

Using Docker:
```bash
docker run -d \
  --name resumerag-postgres \
  -e POSTGRES_DB=resumerag \
  -e POSTGRES_USER=resumerag \
  -e POSTGRES_PASSWORD=your-password \
  -p 5432:5432 \
  pgvector/pgvector:pg14
```

---

## Redis Setup

### Option 1: Upstash (Recommended)

1. **Create Database at [Upstash](https://upstash.com)**
   - Name: `resumerag-cache`
   - Region: Same as API
   - Type: Redis

2. **Get Connection String**
   - Copy "REDIS_URL" from dashboard
   - Example: `redis://default:password@xxx.upstash.io:6379`

3. **Add to Environment Variables**

### Option 2: Redis Cloud

1. **Create Database at [Redis Cloud](https://redis.com/try-free/)**
2. **Get connection string**
3. **Add to environment variables**

### Option 3: Self-Hosted Redis

Using Docker:
```bash
docker run -d \
  --name resumerag-redis \
  -p 6379:6379 \
  redis:7-alpine
```

---

## CI/CD Pipeline

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: pgvector/pgvector:pg14
        env:
          POSTGRES_DB: test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd api
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key-for-ci-only
          FERNET_KEY: test-fernet-key-32-bytes-base64==
        run: |
          cd api
          pytest -v
  
  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Render
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: |
          curl -X POST \
            -H "Authorization: Bearer $RENDER_API_KEY" \
            https://api.render.com/deploy/srv-xxxxx
      
      - name: Wait for deployment
        run: sleep 60
      
      - name: Health check
        run: |
          curl -f https://resumerag-api.onrender.com/api/health || exit 1
  
  deploy-frontend:
    needs: deploy-backend
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./frontend
          vercel-args: '--prod'
```

**Setup Secrets in GitHub**:
1. Go to repository Settings → Secrets → Actions
2. Add:
   - `RENDER_API_KEY` - From Render dashboard
   - `VERCEL_TOKEN` - From Vercel account settings
   - `VERCEL_ORG_ID` - From Vercel project settings
   - `VERCEL_PROJECT_ID` - From Vercel project settings

---

## Post-Deployment Validation

### 1. Health Checks

```bash
# Backend health
curl https://resumerag-api.onrender.com/api/health
# Expected: {"status":"ok"}

# Frontend
curl -I https://resumerag-demo.vercel.app
# Expected: HTTP/2 200

# API metadata
curl https://resumerag-api.onrender.com/api/_meta
# Expected: JSON with features list

# OpenAPI spec
curl https://resumerag-api.onrender.com/docs/openapi.yaml
# Expected: YAML content

# Hackathon manifest
curl https://resumerag-api.onrender.com/.well-known/hackathon.json
# Expected: JSON manifest
```

### 2. Functional Tests

```bash
# Register user
curl -X POST https://resumerag-api.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User",
    "role": "user"
  }'

# Login
curl -X POST https://resumerag-api.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!"
  }'
# Save access_token from response

# Upload resume (with token)
curl -X POST https://resumerag-api.onrender.com/api/resumes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Idempotency-Key: test-upload-$(date +%s)" \
  -F "file=@test-resume.pdf" \
  -F "visibility=private"
```

### 3. Performance Tests

```bash
# Response time check
time curl https://resumerag-api.onrender.com/api/health

# Load test (using Apache Bench)
ab -n 100 -c 10 https://resumerag-api.onrender.com/api/health
```

### 4. Monitoring Setup

- **Prometheus**: Verify `/metrics` endpoint accessible
- **Grafana**: Import dashboards (see OPERATIONS.md)
- **Logs**: Check structured JSON logs in Render/Vercel dashboards
- **Alerts**: Configure alert rules for error rates, latency

---

## Troubleshooting

### Backend Issues

**Problem**: API returns 502/503

**Solutions**:
1. Check Render logs: `render logs resumerag-api`
2. Verify database connection: Check `DATABASE_URL`
3. Verify Redis connection: Check `REDIS_URL`
4. Check build logs for errors
5. Restart service: Render dashboard → Manual Deploy

**Problem**: Database migration fails

**Solutions**:
```bash
# Check current revision
alembic current

# Reset (⚠️ destroys data)
alembic downgrade base
alembic upgrade head

# Or create clean database
# Drop and recreate database, then migrate
```

**Problem**: High memory usage / crashes

**Solutions**:
1. Upgrade to paid plan (512 MB → 2 GB)
2. Optimize worker count: `--workers 1` for free tier
3. Check for memory leaks in logs

### Frontend Issues

**Problem**: API calls fail with CORS errors

**Solutions**:
1. Verify `CORS_ALLOWED_ORIGINS` includes frontend URL
2. Check browser console for exact error
3. Test API directly (curl) to isolate issue

**Problem**: Environment variables not working

**Solutions**:
1. Verify variables start with `VITE_`
2. Rebuild after adding variables: `vercel --prod`
3. Check build logs: Vercel dashboard → Deployments → Logs

**Problem**: 404 on routes (e.g., /search)

**Solutions**:
- Add to `vercel.json`:
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

### Database Issues

**Problem**: pgvector extension not found

**Solutions**:
```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify
SELECT * FROM pg_extension WHERE extname = 'vector';
```

**Problem**: Connection pool exhausted

**Solutions**:
1. Increase `pool_size` in SQLAlchemy config
2. Add connection pooling (PgBouncer)
3. Optimize queries to reduce connection time

---

## Production Checklist

Before going live, verify:

- [ ] All environment variables set correctly
- [ ] Database migrations applied: `alembic current`
- [ ] Secrets generated (not using defaults)
- [ ] CORS configured for production frontend URL
- [ ] Health check endpoint returning 200
- [ ] SSL/TLS enabled (HTTPS)
- [ ] Rate limiting tested
- [ ] File upload size limits configured
- [ ] Logs structured and readable
- [ ] Metrics endpoint accessible
- [ ] Backup strategy in place (database)
- [ ] Monitoring dashboards configured
- [ ] Error alerting set up (email/Slack)
- [ ] Documentation updated with live URLs
- [ ] Load testing completed (100+ concurrent users)
- [ ] Security scan passed (no critical vulnerabilities)

---

## Rollback Procedure

If deployment fails:

1. **Render**: Click "Rollback" in dashboard
2. **Vercel**: Select previous deployment, click "Promote to Production"
3. **Database**: Restore from backup (see provider docs)
4. **Notify Users**: Status page / email

---

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Railway Documentation](https://docs.railway.app)

---

_Last updated: October 4, 2025_
