# ResumeRAG - Local Testing Guide

## ✅ Application Status

**Last Verified:** October 4, 2025

### Running Services

- ✅ **Backend API**: http://localhost:8000
  - FastAPI with auto-reload enabled
  - Health endpoint: http://localhost:8000/api/health
  - Interactive docs: http://localhost:8000/docs
  
- ✅ **Frontend**: http://localhost:3001
  - React + Vite development server
  - Hot module replacement enabled
  
- ✅ **Database**: PostgreSQL 15 + pgvector (port 5433)
  - Container: `resumerag-postgres`
  - Database: `resumerag`
  - Vector extension: enabled
  
- ✅ **Cache**: Redis 7 (port 6379)
  - Container: `resumerag-redis`
  - Used for: rate limiting, query caching

---

## 🧪 Manual Testing Steps

### 1. Test Health Endpoint

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/health"
```

**Expected Response:**
```json
{
  "status": "ok",
  "time": "2025-10-04T13:50:00Z"
}
```

---

### 2. Test API Metadata

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/_meta"
```

**Expected Response:**
```json
{
  "name": "ResumeRAG",
  "version": "1.0.0",
  "api_root": "/api",
  "endpoints": [...],
  "features": {
    "idempotency": true,
    "rate_limit": true,
    "pagination": true
  }
}
```

---

### 3. Test Frontend Access

1. Open browser to: http://localhost:3001
2. Verify pages load:
   - `/` - Upload page
   - `/search` - Search page
   - `/jobs` - Jobs page

---

### 4. Test Resume Upload (via Frontend)

1. Navigate to http://localhost:3001
2. Click "Upload Resume"
3. Select a resume file (PDF, TXT, or DOCX)
4. Choose visibility (Public/Private)
5. Click "Upload"
6. Verify success message and resume ID

**Test Files Available:**
- `c:\Users\herok\Documents\ResumeRAG\test_resume.txt`
- `infra/seed-resumes/alice_resume.txt`
- `infra/seed-resumes/bob_resume.txt`
- `infra/seed-resumes/carol_resume.txt`

---

### 5. Test Resume Upload (via API)

```powershell
# Using PowerShell
$idempotencyKey = [guid]::NewGuid().ToString()
$headers = @{
    "Idempotency-Key" = $idempotencyKey
}

# Upload using Invoke-WebRequest
Invoke-WebRequest -Uri "http://localhost:8000/api/resumes" `
    -Method Post `
    -Headers $headers `
    -Form @{
        file = Get-Item "test_resume.txt"
        visibility = "public"
    }
```

---

### 6. Test Semantic Search

**Via Frontend:**
1. Navigate to http://localhost:3001/search
2. Enter query: "Python engineer with React experience"
3. Click "Search"
4. Verify results display

**Via API:**
```powershell
$body = @{
    query = "Python engineer with React experience"
    k = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/ask" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

---

### 7. Test User Registration

**Via Frontend:**
1. Navigate to http://localhost:3001
2. Click "Register" (if available)
3. Enter email and password
4. Submit form

**Via API:**
```powershell
$body = @{
    email = "test@example.com"
    password = "SecurePass123!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "refresh_token": "abc123..."
}
```

---

### 8. Test Job Creation & Matching

**Create Job:**
```powershell
$idempotencyKey = [guid]::NewGuid().ToString()
$body = @{
    title = "Senior Python Engineer"
    description = "Looking for Python expert with FastAPI and React experience"
    company = "TechCorp"
    location = "San Francisco, CA"
} | ConvertTo-Json

$headers = @{
    "Idempotency-Key" = $idempotencyKey
    "Authorization" = "Bearer YOUR_ACCESS_TOKEN"
    "Content-Type" = "application/json"
}

Invoke-RestMethod -Uri "http://localhost:8000/api/jobs" `
    -Method Post `
    -Headers $headers `
    -Body $body
```

**Match Candidates:**
```powershell
$body = @{ k = 10 } | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/jobs/{job_id}/match" `
    -Method Post `
    -Headers $headers `
    -Body $body
```

---

## 🔍 Verification Checklist

### Backend API
- [ ] Health endpoint responds with 200 OK
- [ ] API metadata returns version 1.0.0
- [ ] OpenAPI docs load at /docs
- [ ] Resume listing returns empty array initially
- [ ] Resume upload creates new record
- [ ] Semantic search returns relevant results
- [ ] User registration creates account
- [ ] JWT authentication works
- [ ] Job creation succeeds
- [ ] Candidate matching returns scored results

### Frontend
- [ ] Homepage loads without errors
- [ ] Upload form displays correctly
- [ ] File upload triggers API call
- [ ] Search page accepts queries
- [ ] Search results display properly
- [ ] Jobs page shows job listings
- [ ] Candidate details page renders
- [ ] Navigation between pages works
- [ ] Error messages display for failed operations

### Database
- [ ] Tables created via migrations
- [ ] pgvector extension enabled
- [ ] User records stored correctly
- [ ] Resume data encrypted (PII fields)
- [ ] Embeddings stored in vector format
- [ ] Queries execute without errors

### Observability
- [ ] Prometheus metrics available at /metrics
- [ ] Structured logs output to console
- [ ] Request IDs present in logs
- [ ] OpenTelemetry traces generated
- [ ] Rate limiting enforced (60 req/min)

---

## 🐛 Common Issues & Fixes

### Issue: Backend not responding

**Symptoms:** 
- Connection refused errors
- Timeouts on API calls

**Fix:**
```powershell
# Restart backend
cd api
C:/Users/herok/Documents/ResumeRAG/.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

---

### Issue: Database connection fails

**Symptoms:**
- "Connection refused" on port 5433
- SQLAlchemy connection errors

**Fix:**
```powershell
# Check if PostgreSQL container is running
docker ps | Select-String "resumerag-postgres"

# Restart if needed
docker start resumerag-postgres

# Verify connection
docker exec resumerag-postgres psql -U postgres -d resumerag -c "SELECT 1"
```

---

### Issue: Frontend not loading

**Symptoms:**
- Blank page
- 404 errors

**Fix:**
```powershell
# Restart frontend
cd frontend
npm run dev
```

---

### Issue: Redis connection fails

**Symptoms:**
- Rate limiting not working
- Cache misses

**Fix:**
```powershell
# Check if Redis is running
docker ps | Select-String "resumerag-redis"

# Restart if needed
docker start resumerag-redis
```

---

### Issue: Vector search fails

**Symptoms:**
- SQL syntax errors with "<->" operator
- "extension does not exist" errors

**Fix:**
```powershell
# Enable pgvector extension
docker exec resumerag-postgres psql -U postgres -d resumerag -c "CREATE EXTENSION IF NOT EXISTS vector"
```

---

## 📊 Performance Expectations

### API Response Times
- Health check: < 10ms
- Resume upload: < 500ms (parsing time)
- Semantic search: < 200ms (with <1000 resumes)
- Job matching: < 300ms (with <100 jobs)
- List resumes: < 50ms

### Database Queries
- Vector similarity search: < 100ms
- User lookup: < 10ms
- Resume fetch: < 20ms

### Frontend Load Times
- Initial page load: < 2s
- Page navigation: < 500ms
- Search results render: < 1s

---

## 📝 Test Data

### Sample Resumes
Located in `infra/seed-resumes/`:
- `alice_resume.txt` - Senior Python Engineer
- `bob_resume.txt` - Full-stack Developer
- `carol_resume.txt` - DevOps Engineer

### Test Users
```
Email: admin@resumerag.com
Password: Admin@123
Role: ADMIN

Email: recruiter@resumerag.com
Password: Recruiter@123
Role: RECRUITER
```

---

## 🚀 Next Steps

After verifying local testing:

1. **Run automated tests**:
   ```powershell
   cd api
   pytest -v
   ```

2. **Check test coverage**:
   ```powershell
   pytest --cov=app --cov-report=html
   ```

3. **Lint code**:
   ```powershell
   black --check app/
   ```

4. **Build for production**:
   ```powershell
   cd frontend
   npm run build
   ```

5. **Deploy** using `docs/DEPLOYMENT.md`

---

## 📞 Support

- **Documentation**: See `docs/` folder
- **API Reference**: `docs/API_REFERENCE.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Deployment**: `docs/DEPLOYMENT.md`

---

**Last Updated:** October 4, 2025
