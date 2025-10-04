# Upgrading from Phase 1 to Phase 2 - Migration Guide

## Overview

This guide walks through the process of upgrading an existing ResumeRAG Phase 1 installation to Phase 2 with security enhancements.

**Estimated Time:** 30-60 minutes  
**Downtime Required:** ~5-10 minutes  
**Risk Level:** Low (fully reversible)

## Pre-Migration Checklist

- [ ] Review Phase 2 features in [PHASE2_SUMMARY.md](PHASE2_SUMMARY.md)
- [ ] Review security documentation in [SECURITY.md](SECURITY.md)
- [ ] Backup your database
- [ ] Backup your `.env` file
- [ ] Review current system health
- [ ] Schedule maintenance window (if production)
- [ ] Notify users of potential brief downtime

## Step 1: Backup Current System

### Database Backup

**PostgreSQL:**
```powershell
# Create backup directory
mkdir backups

# Backup database
pg_dump -h localhost -U postgres -d resumerag > backups/resumerag_pre_phase2_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql

# Verify backup
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Database backup successful"
} else {
    Write-Host "✗ Database backup failed - DO NOT PROCEED"
    exit 1
}
```

### Application Backup

```powershell
# Backup current codebase
cd ..
Copy-Item -Recurse ResumeRAG "ResumeRAG_phase1_backup_$(Get-Date -Format 'yyyyMMdd')"

# Backup environment file
Copy-Item ResumeRAG/infra/.env "ResumeRAG_phase1_env_backup_$(Get-Date -Format 'yyyyMMdd').env"
```

## Step 2: Update Codebase

### Option A: Git Pull (if using Git)

```powershell
cd ResumeRAG
git fetch origin
git checkout phase2  # or appropriate branch
git pull origin phase2
```

### Option B: Manual File Update

If you have the Phase 2 code separately:
```powershell
# Copy new/updated files (adjust paths as needed)
Copy-Item -Force phase2_code/api/app/* ResumeRAG/api/app/ -Recurse
Copy-Item -Force phase2_code/api/alembic/versions/002* ResumeRAG/api/alembic/versions/
# ... repeat for other changed files
```

## Step 3: Update Dependencies

```powershell
cd ResumeRAG/api

# Update Python dependencies
pip install -r requirements.txt --upgrade

# Verify cryptography is installed (required for PII encryption)
pip show cryptography
```

## Step 4: Generate Encryption Keys

### Generate PII Encryption Key

```powershell
# Generate Fernet key for PII encryption
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Example output: AjCqT7pZxGJDKnYnvLZpHCGvLYvqKFnHPzGrLxZLhR4=
# SAVE THIS KEY SECURELY - YOU WILL NEED IT!
```

⚠️ **CRITICAL:** Save this key securely! Loss of this key means you cannot decrypt any encrypted PII data.

### Generate New JWT Secret (Recommended)

```powershell
# Generate random secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Example output: 7kZG2h9Xp4nQvCmR3tYwLbJ8fD5aH6sU1eVrP0zA
```

## Step 5: Update Environment Configuration

Edit `infra/.env` and add the new Phase 2 variables:

```env
# EXISTING VARIABLES (keep these)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/resumerag
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<your-existing-or-new-secret>
# ... other existing variables ...

# NEW PHASE 2 VARIABLES (add these)

# Refresh Token Configuration
REFRESH_TOKEN_EXPIRE_DAYS=7

# PII Encryption (REQUIRED)
PII_ENC_KEY=<your-generated-fernet-key>

# Account Security
MAX_FAILED_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# Upload Security
MAX_FILE_SIZE=52428800  # 50 MB
```

### Environment Variables Summary

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | 7 | Refresh token lifetime in days |
| `PII_ENC_KEY` | **Yes** | None | Fernet encryption key for PII |
| `MAX_FAILED_ATTEMPTS` | No | 5 | Login attempts before lockout |
| `LOCKOUT_DURATION_MINUTES` | No | 15 | Account lockout duration |
| `MAX_FILE_SIZE` | No | 52428800 | Max upload size in bytes |

## Step 6: Stop Application

```powershell
# If using Docker Compose
cd infra
docker-compose down

# If running manually
# Stop your uvicorn/gunicorn processes
Stop-Process -Name "uvicorn" -Force
```

## Step 7: Run Database Migration

```powershell
cd api

# Check current migration status
alembic current

# Should show: 001 (Phase 1)

# Preview the migration
alembic upgrade --sql head > migration_preview.sql
# Review migration_preview.sql to see what will happen

# Run the migration
alembic upgrade head

# Verify migration
alembic current
# Should now show: 002 (Phase 2)
```

### Expected Migration Output

```
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, Security hardening
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
```

### Verify Migration Success

```sql
-- Connect to database
psql -h localhost -U postgres -d resumerag

-- Check new tables exist
\dt refresh_tokens
\dt pii_store
\dt pii_access_log

-- Check new columns in users table
\d users

-- Expected: failed_login_count, last_failed_login, locked_until

-- Exit psql
\q
```

## Step 8: Start Application

```powershell
# If using Docker Compose
cd infra
docker-compose up -d

# Wait for services to start
Start-Sleep -Seconds 10

# Check logs
docker-compose logs -f api

# If running manually
cd api
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Step 9: Verify Phase 2 Features

### Test 1: Health Check

```powershell
curl http://localhost:8000/api/health
# Expected: {"status":"healthy","time":"..."}
```

### Test 2: Refresh Token Flow

```powershell
# Register new user
$resp = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/auth/register" `
    -ContentType "application/json" `
    -Body '{"email":"test@example.com","password":"TestPass123!"}'

# Check response has refresh_token
if ($resp.refresh_token) {
    Write-Host "✓ Refresh token present in response"
} else {
    Write-Host "✗ Refresh token missing - PHASE 2 NOT WORKING"
}
```

### Test 3: New Tables Exist

```powershell
# Check if new tables exist
psql -h localhost -U postgres -d resumerag -c "SELECT COUNT(*) FROM refresh_tokens;"
# Should return 0 (or count of existing tokens)

psql -h localhost -U postgres -d resumerag -c "SELECT COUNT(*) FROM pii_access_log;"
# Should return 0

psql -h localhost -U postgres -d resumerag -c "SELECT COUNT(*) FROM pii_store;"
# Should return 0
```

### Test 4: Admin Endpoint

```powershell
# Get admin token (you'll need to create an admin user first or update a user's role)
$admin_token = "<your-admin-token>"

$resp = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/admin/pii-logs" `
    -Headers @{"Authorization"="Bearer $admin_token"}

Write-Host "✓ Admin endpoint accessible"
```

### Test 5: Account Lockout

```powershell
# Attempt 5 failed logins
for ($i=1; $i -le 5; $i++) {
    try {
        Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/auth/login" `
            -ContentType "application/json" `
            -Body '{"email":"test@example.com","password":"wrong"}'
    } catch {
        Write-Host "Attempt $i failed (expected)"
    }
}

# 6th attempt should return 403
try {
    Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/auth/login" `
        -ContentType "application/json" `
        -Body '{"email":"test@example.com","password":"wrong"}'
    Write-Host "✗ Account lockout NOT working"
} catch {
    if ($_.Exception.Response.StatusCode -eq 403) {
        Write-Host "✓ Account lockout working"
    }
}
```

## Step 10: Update Frontend (if applicable)

### Update Token Storage

```javascript
// OLD (Phase 1)
localStorage.setItem('token', accessToken);

// NEW (Phase 2)
// Store both tokens
sessionStorage.setItem('access_token', accessToken);
sessionStorage.setItem('refresh_token', refreshToken);
```

### Add Token Refresh Logic

```javascript
// Add automatic refresh before token expires
async function ensureValidToken() {
  const token = sessionStorage.getItem('access_token');
  // Decode JWT to check expiration
  const payload = JSON.parse(atob(token.split('.')[1]));
  const expiresAt = payload.exp * 1000; // Convert to milliseconds
  
  // Refresh if expires in < 5 minutes
  if (Date.now() > expiresAt - 5 * 60 * 1000) {
    await refreshToken();
  }
}

async function refreshToken() {
  const refreshToken = sessionStorage.getItem('refresh_token');
  const response = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({refresh_token: refreshToken})
  });
  
  if (response.ok) {
    const data = await response.json();
    sessionStorage.setItem('access_token', data.access_token);
    sessionStorage.setItem('refresh_token', data.refresh_token);
  } else {
    // Refresh failed, redirect to login
    window.location.href = '/login';
  }
}
```

### Add PII Toggle UI

```jsx
// Add to resume detail page
const [showPII, setShowPII] = useState(false);
const [canViewPII, setCanViewPII] = useState(false);

// Check if user can view PII (recruiter or admin)
useEffect(() => {
  const role = getUserRole(); // from token
  setCanViewPII(['recruiter', 'admin'].includes(role));
}, []);

// Add toggle in UI
{canViewPII && (
  <label>
    <input 
      type="checkbox" 
      checked={showPII} 
      onChange={(e) => setShowPII(e.target.checked)} 
    />
    Show PII (will be logged)
  </label>
)}

// Update fetch call
const url = `/api/resumes/${id}?include_pii=${showPII}`;
```

## Step 11: Update CI/CD Pipeline

If using GitHub Actions or similar:

```yaml
# Add to .github/workflows/ci.yml

# ... existing jobs ...

security:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Run Bandit
      run: |
        pip install bandit
        bandit -r api/app -ll
    - name: Run Safety
      run: |
        pip install safety
        safety check --file api/requirements.txt
```

## Step 12: Production Secrets Management

If deploying to production, **DO NOT** use .env files. Use proper secrets management:

### AWS Secrets Manager

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# In app initialization
secrets = get_secret('resumerag/production')
PII_ENC_KEY = secrets['PII_ENC_KEY']
SECRET_KEY = secrets['SECRET_KEY']
```

### Azure Key Vault

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://resumerag-kv.vault.azure.net", 
    credential=credential
)

PII_ENC_KEY = client.get_secret("pii-enc-key").value
SECRET_KEY = client.get_secret("secret-key").value
```

## Rollback Procedure

If something goes wrong, you can rollback:

### Step 1: Stop Application

```powershell
docker-compose down
# or stop your running processes
```

### Step 2: Rollback Database

```powershell
# Rollback migration
cd api
alembic downgrade 001

# Or restore from backup
psql -h localhost -U postgres -d resumerag < backups/resumerag_pre_phase2_*.sql
```

### Step 3: Restore Code

```powershell
cd ..
Remove-Item -Recurse -Force ResumeRAG
Copy-Item -Recurse ResumeRAG_phase1_backup_* ResumeRAG
```

### Step 4: Restore Environment

```powershell
Copy-Item ResumeRAG_phase1_env_backup_*.env ResumeRAG/infra/.env
```

### Step 5: Restart Application

```powershell
cd ResumeRAG/infra
docker-compose up -d
```

## Post-Migration Tasks

### Immediate (Day 1)

- [ ] Monitor application logs for errors
- [ ] Test all critical user flows
- [ ] Verify new security features working
- [ ] Check database performance with new indexes
- [ ] Monitor failed login attempts
- [ ] Review PII access logs

### Short-term (Week 1)

- [ ] Update user documentation
- [ ] Train support staff on new features
- [ ] Set up monitoring alerts
- [ ] Review and adjust lockout thresholds
- [ ] Test token refresh in production
- [ ] Verify audit logs retention

### Medium-term (Month 1)

- [ ] Review PII access patterns
- [ ] Analyze account lockout frequency
- [ ] Tune rate limiting if needed
- [ ] Plan key rotation schedule
- [ ] Conduct security audit
- [ ] Update incident response plan

## Troubleshooting

### Issue: Migration Fails

**Symptoms:** `alembic upgrade head` fails

**Solutions:**
1. Check database connection: `psql -h localhost -U postgres -d resumerag`
2. Verify pgvector extension: `SELECT * FROM pg_extension WHERE extname='vector';`
3. Check current version: `alembic current`
4. Review migration SQL: `alembic upgrade --sql head`
5. Check for conflicting columns: `\d users` in psql

### Issue: PII_ENC_KEY Not Set

**Symptoms:** Application starts but errors on encryption operations

**Solutions:**
1. Verify key is in `.env`: `cat infra/.env | grep PII_ENC_KEY`
2. Restart application after adding key
3. Generate new key if needed (see Step 4)
4. Check key format (should be base64 encoded Fernet key)

### Issue: Refresh Tokens Not Working

**Symptoms:** `/api/auth/refresh` returns 401

**Solutions:**
1. Verify refresh_tokens table exists: `\dt refresh_tokens` in psql
2. Check token not expired or revoked
3. Verify SECRET_KEY matches across restarts
4. Check logs for specific error messages

### Issue: Account Lockout Too Aggressive

**Symptoms:** Users getting locked out too frequently

**Solutions:**
1. Increase `MAX_FAILED_ATTEMPTS` in `.env` (e.g., to 10)
2. Decrease `LOCKOUT_DURATION_MINUTES` (e.g., to 5)
3. Reset lockout for specific user:
   ```sql
   UPDATE users 
   SET failed_login_count=0, locked_until=NULL 
   WHERE email='user@example.com';
   ```

### Issue: Admin Endpoint Returns 403

**Symptoms:** Cannot access `/api/admin/pii-logs` even with token

**Solutions:**
1. Verify user role is 'admin':
   ```sql
   SELECT email, role FROM users WHERE email='admin@example.com';
   ```
2. Update user role if needed:
   ```sql
   UPDATE users SET role='admin' WHERE email='admin@example.com';
   ```
3. Get new token after role change

## Monitoring Recommendations

### Key Metrics

1. **Authentication Metrics**
   - Failed login attempts per hour
   - Account lockouts per day
   - Refresh token rotations per hour
   - Token revocations per day

2. **PII Access Metrics**
   - PII access requests per hour
   - PII access by user role
   - PII access denials per day

3. **Upload Security Metrics**
   - Malicious file attempts per day
   - File size rejections per day
   - Invalid file type attempts per day

### Recommended Alerts

```
WARN: Failed logins > 100 per hour from single IP
CRITICAL: Account lockouts > 50 per hour (possible attack)
CRITICAL: PII access > 1000 per hour from single user
WARN: Malicious file attempts > 10 per hour
CRITICAL: Database connection errors
WARN: Token refresh failures > 100 per hour
```

## Support

If you encounter issues not covered in this guide:

1. Check application logs: `docker-compose logs api`
2. Review [PHASE2_SUMMARY.md](PHASE2_SUMMARY.md)
3. Review [SECURITY.md](SECURITY.md)
4. Check database logs: `docker-compose logs postgres`
5. Search closed issues on GitHub
6. Open new issue with:
   - Migration step where it failed
   - Error messages
   - Database version
   - Python version
   - OS and environment details

## Success Criteria

✅ Migration is successful when:

- [ ] All services start without errors
- [ ] Health check returns 200
- [ ] User registration returns refresh_token
- [ ] User login returns refresh_token
- [ ] Token refresh endpoint works
- [ ] Account lockout triggers after 5 failures
- [ ] Admin PII logs endpoint accessible
- [ ] No errors in application logs
- [ ] All existing Phase 1 features still work
- [ ] Database queries complete successfully
- [ ] Frontend connects and authenticates

🎉 **Congratulations! Your ResumeRAG installation is now Phase 2 security-hardened!**

## Next Steps

1. Review [SECURITY.md](SECURITY.md) for production best practices
2. Set up proper secrets management (AWS/Azure/Vault)
3. Configure monitoring and alerting
4. Plan security audit and penetration testing
5. Update disaster recovery documentation
6. Train team on new security features
