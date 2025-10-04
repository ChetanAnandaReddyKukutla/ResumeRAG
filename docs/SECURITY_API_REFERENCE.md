# Security API Quick Reference

## Authentication Endpoints

### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response 201:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "refresh_token": "abc123..."
}
```

### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response 200:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "refresh_token": "abc123..."
}

Error 403 (Account Locked):
{
  "error": {
    "code": "ACCOUNT_LOCKED",
    "message": "Account locked for 15 minutes due to too many failed login attempts."
  }
}
```

### Refresh Access Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "abc123..."
}

Response 200:
{
  "access_token": "eyJ...",  # New token
  "token_type": "bearer",
  "refresh_token": "xyz789..."  # New refresh token (old one is revoked)
}

Error 401 (Invalid/Expired):
{
  "error": {
    "code": "INVALID_REFRESH_TOKEN",
    "message": "Invalid or expired refresh token"
  }
}
```

### Revoke Single Token (Logout)
```http
POST /api/auth/revoke
Content-Type: application/json

{
  "refresh_token": "abc123..."
}

Response 200:
{
  "message": "Token revoked successfully"
}
```

### Revoke All Tokens (Logout Everywhere)
```http
POST /api/auth/revoke-all
Authorization: Bearer eyJ...

Response 200:
{
  "message": "All refresh tokens revoked successfully"
}
```

## Resume Endpoints (Updated)

### Get Resume with PII
```http
GET /api/resumes/{resume_id}?include_pii=true
Authorization: Bearer eyJ...

Response 200:
{
  "id": "resume_123",
  "name": "John Doe",
  "email": "john.doe@example.com",  # Unredacted (if permitted)
  "phone": "555-123-4567",  # Unredacted (if permitted)
  "parsed_text_snippets": [...],
  "uploaded_at": "2024-01-15T10:00:00Z",
  "status": "completed"
}

Error 403 (No Permission):
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Not authorized to view PII for this resume"
  }
}
```

**PII Access Permissions:**
- ✅ User can view their own resumes with PII
- ✅ Recruiter can view any resume with PII
- ✅ Admin can view any resume with PII
- ❌ User cannot view other users' resumes with PII

**Audit Logging:**
Every request with `include_pii=true` that is permitted is logged to the audit trail.

### Get Resume without PII (Default)
```http
GET /api/resumes/{resume_id}
Authorization: Bearer eyJ...

Response 200:
{
  "id": "resume_123",
  "name": "John Doe",
  "email": "j***e@e***.com",  # Redacted
  "phone": "***-***-4567",  # Redacted
  "parsed_text_snippets": [...],
  "uploaded_at": "2024-01-15T10:00:00Z",
  "status": "completed"
}
```

## Admin Endpoints (New)

### Get PII Access Audit Logs
```http
GET /api/admin/pii-logs?resume_id=resume_123&limit=100&offset=0
Authorization: Bearer eyJ...  # Must be admin user

Response 200:
{
  "items": [
    {
      "id": "pii_log_abc",
      "actor_user_id": "user_456",
      "actor_email": "recruiter@company.com",
      "resume_id": "resume_123",
      "action": "VIEW_PII",
      "reason": "Resume review for job match",
      "request_id": "req_789",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}

Error 403 (Not Admin):
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Admin access required"
  }
}
```

**Query Parameters:**
- `resume_id` (optional) - Filter by specific resume
- `actor_user_id` (optional) - Filter by specific user who accessed PII
- `limit` (optional, default: 100, max: 1000) - Results per page
- `offset` (optional, default: 0) - Pagination offset

## Error Codes

### Authentication Errors
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_CREDENTIALS` | 401 | Wrong email or password |
| `ACCOUNT_LOCKED` | 403 | Too many failed login attempts |
| `INVALID_REFRESH_TOKEN` | 401 | Refresh token expired or revoked |
| `USER_NOT_FOUND` | 401 | User associated with token not found |
| `USER_EXISTS` | 400 | Email already registered |

### Authorization Errors
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_AUTHENTICATED` | 401 | No or invalid access token |

### Upload Security Errors
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_FILE_TYPE` | 400 | File extension not allowed |
| `INVALID_CONTENT_TYPE` | 400 | Content-Type header not allowed |
| `FILE_TOO_LARGE` | 400 | File exceeds size limit |
| `EMPTY_FILE` | 400 | File has no content |
| `MALICIOUS_FILE` | 400 | File contains malicious patterns |

## Security Best Practices

### Token Management

**Do:**
- ✅ Store access tokens in memory only (not localStorage)
- ✅ Store refresh tokens in httpOnly cookies or secure storage
- ✅ Implement automatic token refresh before expiration
- ✅ Handle 401 errors by attempting refresh
- ✅ Clear tokens on logout

**Don't:**
- ❌ Store tokens in localStorage (XSS vulnerable)
- ❌ Send tokens in URL parameters
- ❌ Log tokens in console or error messages
- ❌ Share tokens between users

### Client-Side Token Refresh Pattern

```javascript
async function fetchWithAuth(url, options = {}) {
  // Add access token
  options.headers = {
    ...options.headers,
    'Authorization': `Bearer ${getAccessToken()}`
  };
  
  let response = await fetch(url, options);
  
  // If 401, try to refresh
  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      // Retry with new token
      options.headers['Authorization'] = `Bearer ${getAccessToken()}`;
      response = await fetch(url, options);
    } else {
      // Refresh failed, redirect to login
      window.location.href = '/login';
    }
  }
  
  return response;
}

async function refreshAccessToken() {
  try {
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        refresh_token: getRefreshToken()
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      setAccessToken(data.access_token);
      setRefreshToken(data.refresh_token);
      return true;
    }
    return false;
  } catch (error) {
    return false;
  }
}
```

### PII Access

**When to use `include_pii=true`:**
- Recruiter reviewing candidate for interview
- User viewing their own resume details
- Admin conducting security audit

**When to use `include_pii=false` (default):**
- Listing multiple resumes
- Searching/browsing candidates
- Public-facing displays
- Any scenario where full PII is not required

**Always:**
- Check user permission before showing PII toggle
- Log reason for PII access when possible
- Implement client-side redaction as backup
- Monitor PII access patterns for anomalies

### File Upload

**Client-Side Validation (Pre-flight):**
```javascript
function validateFileUpload(file) {
  // Check extension
  const allowedExt = ['.pdf', '.docx', '.txt', '.zip'];
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
  if (!allowedExt.includes(ext)) {
    throw new Error(`File type ${ext} not allowed`);
  }
  
  // Check size (50 MB)
  if (file.size > 50 * 1024 * 1024) {
    throw new Error('File too large (max 50 MB)');
  }
  
  return true;
}
```

**Note:** Client-side validation is for UX only. Server-side validation is mandatory.

## Environment Variables

```env
# Authentication
SECRET_KEY=<your-secret-jwt-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# PII Encryption (REQUIRED in production)
# Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
PII_ENC_KEY=<your-fernet-key>

# Account Security
MAX_FAILED_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# Upload Security
MAX_FILE_SIZE=52428800  # 50 MB in bytes
```

## Testing Security Features

### Test Account Lockout
```bash
# PowerShell
for ($i=1; $i -le 5; $i++) {
  curl -X POST http://localhost:8000/api/auth/login `
       -H "Content-Type: application/json" `
       -d "{\"email\":\"test@example.com\",\"password\":\"wrong$i\"}"
}

# 6th attempt should return 403 ACCOUNT_LOCKED
curl -X POST http://localhost:8000/api/auth/login `
     -H "Content-Type: application/json" `
     -d "{\"email\":\"test@example.com\",\"password\":\"correct\"}"
```

### Test Token Rotation
```bash
# Get initial tokens
$resp = curl -X POST http://localhost:8000/api/auth/register `
             -H "Content-Type: application/json" `
             -d "{\"email\":\"test@example.com\",\"password\":\"Pass123!\"}"
$tokens = $resp | ConvertFrom-Json
$refresh1 = $tokens.refresh_token

# Refresh (should work)
$resp = curl -X POST http://localhost:8000/api/auth/refresh `
             -H "Content-Type: application/json" `
             -d "{\"refresh_token\":\"$refresh1\"}"
$tokens = $resp | ConvertFrom-Json
$refresh2 = $tokens.refresh_token

# Old token should fail
curl -X POST http://localhost:8000/api/auth/refresh `
     -H "Content-Type: application/json" `
     -d "{\"refresh_token\":\"$refresh1\"}"  # Should return 401
```

### Test PII Access Logging
```bash
# Create resume and access with PII
$token = "<your-access-token>"
curl -X GET "http://localhost:8000/api/resumes/resume_123?include_pii=true" `
     -H "Authorization: Bearer $token"

# Check audit logs (admin only)
$admin_token = "<admin-access-token>"
curl -X GET "http://localhost:8000/api/admin/pii-logs" `
     -H "Authorization: Bearer $admin_token"
```

## Monitoring & Alerting

**Key Metrics to Monitor:**
1. Failed login attempts per user
2. Account lockouts per hour
3. PII access frequency per user
4. Refresh token rotation rate
5. Malicious file upload attempts

**Recommended Alerts:**
- ⚠️ 10+ failed logins from same IP in 5 minutes
- ⚠️ 100+ PII accesses from single user in 1 hour
- ⚠️ 5+ malicious file upload attempts in 1 hour
- 🚨 Failed refresh token validations (possible token theft)
- 🚨 PII access from unusual geographic locations

## Compliance Checklist

- [ ] PII_ENC_KEY generated and stored in secrets manager
- [ ] SECRET_KEY rotated from default
- [ ] CORS configured with specific origins (not `*`)
- [ ] SSL/TLS enabled for all connections
- [ ] Audit log retention policy defined
- [ ] Incident response plan documented
- [ ] Security testing completed
- [ ] Penetration testing performed
- [ ] Dependency vulnerabilities resolved
- [ ] Production monitoring configured
