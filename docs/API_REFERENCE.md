# ResumeRAG API Reference

Complete API documentation for ResumeRAG backend endpoints.

**Base URL (Production)**: `https://api.resumerag.example.com`  
**Base URL (Local)**: `http://localhost:8000`

**OpenAPI Interactive Docs**: `https://api.resumerag.example.com/docs`

---

## 📋 Table of Contents

- [Authentication](#authentication)
  - [Register User](#register-user)
  - [Login](#login)
  - [Refresh Token](#refresh-token)
  - [Logout](#logout)
  - [Get Current User](#get-current-user)
- [Resumes](#resumes)
  - [Upload Resume](#upload-resume)
  - [List Resumes](#list-resumes)
  - [Get Resume Details](#get-resume-details)
  - [Delete Resume](#delete-resume)
  - [Update Visibility](#update-visibility)
- [Semantic Search](#semantic-search)
  - [Ask Question](#ask-question)
- [Jobs](#jobs)
  - [Create Job](#create-job)
  - [List Jobs](#list-jobs)
  - [Get Job Details](#get-job-details)
  - [Match Candidates](#match-candidates)
- [Admin](#admin)
  - [Get PII Access Logs](#get-pii-access-logs)
- [Meta](#meta)
  - [Health Check](#health-check)
  - [API Metadata](#api-metadata)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)

---

## Authentication

All authenticated endpoints require a JWT access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Authentication Flow

1. **Register** → Get `access_token` + `refresh_token`
2. **Login** → Get `access_token` + `refresh_token`
3. **Use** `access_token` for API calls (valid 30 minutes)
4. **Refresh** → Exchange `refresh_token` for new `access_token` (valid 7 days)
5. **Logout** → Invalidate `refresh_token`

---

### Register User

**POST** `/api/auth/register`

Create a new user account.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (`201 Created`):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "a1b2c3d4e5f6..."
}
```

**Errors**:
- `400 BAD_REQUEST` - Invalid email or weak password
- `409 CONFLICT` - Email already registered

**Example**:
```bash
curl -X POST https://api.resumerag.example.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'
```

---

### Login

**POST** `/api/auth/login`

Authenticate and get access tokens.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (`200 OK`):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "a1b2c3d4e5f6..."
}
```

**Errors**:
- `401 UNAUTHORIZED` - Invalid credentials
- `403 FORBIDDEN` - Account locked (too many failed attempts)
  - **Account Lockout**: After 5 failed login attempts, account is locked for 15 minutes

**Example**:
```bash
curl -X POST https://api.resumerag.example.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'
```

---

### Refresh Token

**POST** `/api/auth/refresh`

Get a new access token using refresh token.

**Request Body**:
```json
{
  "refresh_token": "a1b2c3d4e5f6..."
}
```

**Response** (`200 OK`):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors**:
- `401 UNAUTHORIZED` - Invalid or expired refresh token

**Example**:
```bash
curl -X POST https://api.resumerag.example.com/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"a1b2c3d4e5f6..."}'
```

---

### Logout

**POST** `/api/auth/logout`

Invalidate refresh token (requires authentication).

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "refresh_token": "a1b2c3d4e5f6..."
}
```

**Response** (`200 OK`):
```json
{
  "message": "Logged out successfully"
}
```

**Example**:
```bash
curl -X POST https://api.resumerag.example.com/api/auth/logout \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"a1b2c3d4e5f6..."}'
```

---

### Get Current User

**GET** `/api/auth/me`

Get current user information (requires authentication).

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (`200 OK`):
```json
{
  "id": "usr_abc123",
  "email": "user@example.com",
  "role": "user"
}
```

**Example**:
```bash
curl -X GET https://api.resumerag.example.com/api/auth/me \
  -H "Authorization: Bearer eyJhbGci..."
```

---

## Resumes

### Upload Resume

**POST** `/api/resumes`

Upload and parse a resume file.

**Headers**:
```
Authorization: Bearer <access_token> (optional)
Idempotency-Key: <unique_key>
```

**Request** (multipart/form-data):
- `file` (file, required) - Resume file (PDF, TXT, DOCX)
- `visibility` (string, optional) - `"private"` or `"public"` (default: `"private"`)
- `owner_id` (string, optional) - Custom owner ID (if not authenticated)

**Response** (`201 Created`):
```json
{
  "id": "res_xyz789",
  "filename": "alice_resume.pdf",
  "status": "pending",
  "message": "Resume uploaded successfully. Processing in background."
}
```

**Errors**:
- `400 BAD_REQUEST` - Invalid file type or size (max 10MB)
- `409 CONFLICT` - Idempotency key conflict (duplicate request)
- `413 PAYLOAD_TOO_LARGE` - File exceeds size limit
- `415 UNSUPPORTED_MEDIA_TYPE` - Invalid file type

**Supported Formats**: `.pdf`, `.txt`, `.doc`, `.docx`

**Security**:
- File content scanning (malware detection)
- Filename sanitization
- Size limit enforcement (10MB)
- PII encryption at rest

**Example**:
```bash
# Generate idempotency key
IDEMPOTENCY_KEY=$(uuidgen)

curl -X POST https://api.resumerag.example.com/api/resumes \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -F "file=@alice_resume.pdf" \
  -F "visibility=private"
```

---

### List Resumes

**GET** `/api/resumes`

List resumes with filtering.

**Query Parameters**:
- `status` (string, optional) - Filter by status: `pending`, `completed`, `failed`
- `visibility` (string, optional) - Filter by visibility: `private`, `public`
- `limit` (integer, optional) - Max results (default: 50, max: 100)
- `offset` (integer, optional) - Pagination offset (default: 0)

**Headers** (optional):
```
Authorization: Bearer <access_token>
```

**Response** (`200 OK`):
```json
{
  "items": [
    {
      "id": "res_xyz789",
      "filename": "alice_resume.pdf",
      "status": "completed",
      "visibility": "private",
      "owner_id": "usr_abc123",
      "uploaded_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "res_def456",
      "filename": "bob_resume.txt",
      "status": "pending",
      "visibility": "public",
      "owner_id": null,
      "uploaded_at": "2024-01-15T11:00:00Z"
    }
  ],
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

**Visibility Rules**:
- **Authenticated**: See own private resumes + all public resumes
- **Anonymous**: See only public resumes

**Example**:
```bash
# List completed resumes
curl -X GET "https://api.resumerag.example.com/api/resumes?status=completed&limit=10" \
  -H "Authorization: Bearer eyJhbGci..."
```

---

### Get Resume Details

**GET** `/api/resumes/{resume_id}`

Get detailed resume information with parsed data.

**Path Parameters**:
- `resume_id` (string, required) - Resume ID

**Headers** (optional):
```
Authorization: Bearer <access_token>
```

**Response** (`200 OK`):
```json
{
  "id": "res_xyz789",
  "filename": "alice_resume.pdf",
  "status": "completed",
  "visibility": "private",
  "owner_id": "usr_abc123",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "processed_at": "2024-01-15T10:30:15Z",
  "parsed_data": {
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "phone": "555-1234",
    "summary": "Senior software engineer with 8 years...",
    "skills": ["Python", "React", "PostgreSQL"],
    "experience": [
      {
        "title": "Senior Engineer",
        "company": "TechCorp",
        "duration": "2020-Present",
        "description": "Led development of microservices..."
      }
    ],
    "education": [
      {
        "degree": "BS Computer Science",
        "school": "University of Example",
        "year": "2015"
      }
    ]
  },
  "chunks": [
    {
      "id": "chunk_1",
      "text": "Senior software engineer with expertise in Python...",
      "chunk_index": 0
    }
  ]
}
```

**Errors**:
- `404 NOT_FOUND` - Resume not found
- `403 FORBIDDEN` - No access to private resume

**PII Access Auditing**: Access to PII fields (name, email, phone) is logged for compliance.

**Example**:
```bash
curl -X GET https://api.resumerag.example.com/api/resumes/res_xyz789 \
  -H "Authorization: Bearer eyJhbGci..."
```

---

### Delete Resume

**DELETE** `/api/resumes/{resume_id}`

Delete a resume (requires authentication and ownership).

**Path Parameters**:
- `resume_id` (string, required) - Resume ID

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (`200 OK`):
```json
{
  "message": "Resume deleted successfully"
}
```

**Errors**:
- `401 UNAUTHORIZED` - Not authenticated
- `403 FORBIDDEN` - Not the owner
- `404 NOT_FOUND` - Resume not found

**Example**:
```bash
curl -X DELETE https://api.resumerag.example.com/api/resumes/res_xyz789 \
  -H "Authorization: Bearer eyJhbGci..."
```

---

### Update Visibility

**PATCH** `/api/resumes/{resume_id}/visibility`

Update resume visibility (requires authentication and ownership).

**Path Parameters**:
- `resume_id` (string, required) - Resume ID

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "visibility": "public"
}
```

**Response** (`200 OK`):
```json
{
  "id": "res_xyz789",
  "visibility": "public"
}
```

**Example**:
```bash
curl -X PATCH https://api.resumerag.example.com/api/resumes/res_xyz789/visibility \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{"visibility":"public"}'
```

---

## Semantic Search

### Ask Question

**POST** `/api/ask`

Perform semantic search across resumes using natural language query.

**Headers** (optional):
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "query": "Find Python engineers with React experience",
  "k": 5
}
```

**Parameters**:
- `query` (string, required) - Natural language search query
- `k` (integer, optional) - Number of top results to return (default: 5, max: 20)

**Response** (`200 OK`):
```json
{
  "query": "Find Python engineers with React experience",
  "answers": [
    {
      "resume_id": "res_xyz789",
      "filename": "alice_resume.pdf",
      "score": 0.92,
      "snippets": [
        {
          "chunk_id": "chunk_1",
          "text": "Senior Python engineer with 5 years experience building React frontends...",
          "chunk_index": 0
        },
        {
          "chunk_id": "chunk_3",
          "text": "Led migration from Django templates to React SPA...",
          "chunk_index": 2
        }
      ]
    },
    {
      "resume_id": "res_def456",
      "filename": "bob_resume.txt",
      "score": 0.85,
      "snippets": [
        {
          "chunk_id": "chunk_2",
          "text": "Full-stack developer proficient in Python Flask and React...",
          "chunk_index": 1
        }
      ]
    }
  ],
  "count": 2
}
```

**Scoring**:
- Scores range from 0.0 (no match) to 1.0 (perfect match)
- Based on cosine similarity of query embedding vs. resume chunk embeddings
- Results sorted by score (descending)

**Caching**:
- Queries are cached for 1 hour to improve performance
- Cache key: hash of `(query, k)`

**Errors**:
- `400 BAD_REQUEST` - Empty query or invalid `k` value

**Example**:
```bash
curl -X POST https://api.resumerag.example.com/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"Python engineer with AWS experience","k":5}'
```

---

## Jobs

### Create Job

**POST** `/api/jobs`

Create a new job posting.

**Headers**:
```
Authorization: Bearer <access_token>
Idempotency-Key: <unique_key>
```

**Request Body**:
```json
{
  "title": "Senior Python Engineer",
  "description": "We are looking for a Senior Python Engineer with experience in FastAPI, PostgreSQL, and React. Must have 5+ years of backend development experience and strong system design skills.",
  "company": "TechCorp",
  "location": "San Francisco, CA (Remote OK)"
}
```

**Response** (`201 Created`):
```json
{
  "id": "job_abc123",
  "title": "Senior Python Engineer",
  "description": "We are looking for...",
  "company": "TechCorp",
  "location": "San Francisco, CA (Remote OK)",
  "requirements": ["python", "fastapi", "postgresql", "react"],
  "created_at": "2024-01-15T12:00:00Z"
}
```

**Requirements Extraction**:
- Automatically extracts tech keywords from description
- Common keywords: programming languages, frameworks, databases, cloud platforms

**Example**:
```bash
IDEMPOTENCY_KEY=$(uuidgen)

curl -X POST https://api.resumerag.example.com/api/jobs \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"Senior Python Engineer","description":"We need Python + React expert...","company":"TechCorp","location":"Remote"}'
```

---

### List Jobs

**GET** `/api/jobs`

List all jobs with pagination.

**Query Parameters**:
- `limit` (integer, optional) - Max results (default: 50, max: 100)
- `offset` (integer, optional) - Pagination offset (default: 0)

**Response** (`200 OK`):
```json
{
  "items": [
    {
      "id": "job_abc123",
      "title": "Senior Python Engineer",
      "company": "TechCorp",
      "location": "San Francisco, CA",
      "requirements": ["python", "fastapi", "react"],
      "created_at": "2024-01-15T12:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

**Example**:
```bash
curl -X GET "https://api.resumerag.example.com/api/jobs?limit=10" \
  -H "Authorization: Bearer eyJhbGci..."
```

---

### Get Job Details

**GET** `/api/jobs/{job_id}`

Get detailed job information.

**Path Parameters**:
- `job_id` (string, required) - Job ID

**Response** (`200 OK`):
```json
{
  "id": "job_abc123",
  "title": "Senior Python Engineer",
  "description": "We are looking for a Senior Python Engineer...",
  "company": "TechCorp",
  "location": "San Francisco, CA (Remote OK)",
  "requirements": ["python", "fastapi", "postgresql", "react"],
  "created_at": "2024-01-15T12:00:00Z"
}
```

**Example**:
```bash
curl -X GET https://api.resumerag.example.com/api/jobs/job_abc123 \
  -H "Authorization: Bearer eyJhbGci..."
```

---

### Match Candidates

**POST** `/api/jobs/{job_id}/match`

Find best matching candidates for a job.

**Path Parameters**:
- `job_id` (string, required) - Job ID

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "k": 10
}
```

**Parameters**:
- `k` (integer, optional) - Number of top candidates (default: 10, max: 50)

**Response** (`200 OK`):
```json
{
  "job_id": "job_abc123",
  "job_title": "Senior Python Engineer",
  "matches": [
    {
      "resume_id": "res_xyz789",
      "filename": "alice_resume.pdf",
      "score": 0.95,
      "matching_requirements": ["python", "react", "postgresql"],
      "evidence": [
        {
          "chunk_id": "chunk_1",
          "text": "8 years Python development, built React apps with PostgreSQL backend",
          "relevance": "high"
        },
        {
          "chunk_id": "chunk_2",
          "text": "Led FastAPI migration at TechStartup",
          "relevance": "medium"
        }
      ]
    },
    {
      "resume_id": "res_def456",
      "filename": "bob_resume.txt",
      "score": 0.88,
      "matching_requirements": ["python", "react"],
      "evidence": [
        {
          "chunk_id": "chunk_3",
          "text": "Full-stack Python engineer, React expert",
          "relevance": "high"
        }
      ]
    }
  ],
  "count": 2
}
```

**Matching Algorithm**:
1. Construct query from job description + requirements
2. Generate embedding for job query
3. Perform vector similarity search across resume chunks
4. Rank candidates by cosine similarity score
5. Extract evidence snippets showing relevant experience

**Example**:
```bash
curl -X POST https://api.resumerag.example.com/api/jobs/job_abc123/match \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{"k":10}'
```

---

## Admin

Admin endpoints require `admin` role.

### Get PII Access Logs

**GET** `/api/admin/pii-logs`

Get audit logs for PII access (admin only).

**Headers**:
```
Authorization: Bearer <admin_access_token>
```

**Query Parameters**:
- `resume_id` (string, optional) - Filter by resume ID
- `actor_user_id` (string, optional) - Filter by actor user ID
- `limit` (integer, optional) - Max results (default: 100, max: 500)
- `offset` (integer, optional) - Pagination offset (default: 0)

**Response** (`200 OK`):
```json
{
  "items": [
    {
      "id": "log_xyz123",
      "actor_user_id": "usr_abc123",
      "actor_email": "user@example.com",
      "resume_id": "res_xyz789",
      "action": "view_resume",
      "reason": "Candidate review for job_abc123",
      "request_id": "req_def456",
      "created_at": "2024-01-15T13:00:00Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

**Actions Logged**:
- `view_resume` - Accessed full resume details
- `download_resume` - Downloaded resume file
- `update_resume` - Modified resume data

**Errors**:
- `403 FORBIDDEN` - Non-admin user

**Example**:
```bash
curl -X GET "https://api.resumerag.example.com/api/admin/pii-logs?resume_id=res_xyz789" \
  -H "Authorization: Bearer <admin_token>"
```

---

## Meta

### Health Check

**GET** `/health`

Check API health status.

**Response** (`200 OK`):
```json
{
  "status": "healthy",
  "time": "2024-01-15T14:00:00Z"
}
```

**Example**:
```bash
curl -X GET https://api.resumerag.example.com/health
```

---

### API Metadata

**GET** `/api/meta`

Get API metadata and available endpoints.

**Response** (`200 OK`):
```json
{
  "name": "ResumeRAG API",
  "version": "1.0.0",
  "api_root": "/api",
  "endpoints": [
    "/api/auth/register",
    "/api/auth/login",
    "/api/resumes",
    "/api/ask",
    "/api/jobs",
    "/api/admin/pii-logs"
  ],
  "features": {
    "authentication": true,
    "semantic_search": true,
    "job_matching": true,
    "pii_encryption": true,
    "audit_logging": true,
    "rate_limiting": true,
    "observability": true
  }
}
```

**Example**:
```bash
curl -X GET https://api.resumerag.example.com/api/meta
```

---

## Error Codes

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request succeeded |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid request parameters |
| `401` | Unauthorized | Authentication required or failed |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Duplicate resource (e.g., idempotency key) |
| `413` | Payload Too Large | File size exceeds limit |
| `415` | Unsupported Media Type | Invalid file format |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |
| `503` | Service Unavailable | Service temporarily down |

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_CREDENTIALS` | 401 | Incorrect email or password |
| `TOKEN_EXPIRED` | 401 | Access token expired |
| `ACCOUNT_LOCKED` | 403 | Account locked due to failed login attempts |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `DUPLICATE_REQUEST` | 409 | Idempotency key already used |
| `FILE_TOO_LARGE` | 413 | File exceeds 10MB limit |
| `INVALID_FILE_TYPE` | 415 | Unsupported file format |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |

---

## Rate Limiting

**Default Limits**: 60 requests per minute per IP address

**Headers** (included in responses):
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1610712000
```

**Rate Limit Exceeded Response** (`429 Too Many Requests`):
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "details": {
      "retry_after": 60
    }
  }
}
```

**Tips**:
- Use exponential backoff when retrying failed requests
- Implement client-side caching where appropriate
- Use webhooks instead of polling (coming soon)

---

## Idempotency

Idempotency keys prevent duplicate operations (e.g., double uploads).

**Header**:
```
Idempotency-Key: <unique_uuid>
```

**Behavior**:
- If key is new: Process request normally
- If key exists: Return cached response (409 Conflict)

**Supported Endpoints**:
- `POST /api/resumes` (upload)
- `POST /api/jobs` (create job)

**Best Practice**: Use UUIDs for idempotency keys

```bash
# Generate UUID
IDEMPOTENCY_KEY=$(uuidgen)

# Use in request
curl -X POST https://api.resumerag.example.com/api/resumes \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -F "file=@resume.pdf"
```

---

## Security

### HTTPS Only
All API calls must use HTTPS in production.

### JWT Tokens
- **Access Token**: Valid for 30 minutes
- **Refresh Token**: Valid for 7 days
- Tokens are signed with HS256 algorithm

### PII Encryption
- Personal data (name, email, phone) encrypted at rest using Fernet (AES-128)
- Access to PII is audited for compliance

### File Upload Security
- File content scanning for malware
- Filename sanitization
- MIME type validation
- Size limit enforcement (10MB)

### Account Security
- Passwords hashed with bcrypt
- Account lockout after 5 failed login attempts (15-minute lockout)
- Refresh token rotation on use

---

## Observability

### Metrics
Prometheus metrics available at `/metrics`:
- `resume_upload_total` - Total resume uploads
- `resume_parse_duration_seconds` - Parse duration histogram
- `api_request_duration_seconds` - API latency histogram
- `cache_hit_total` / `cache_miss_total` - Cache performance

### Tracing
OpenTelemetry traces exported to configured OTLP endpoint.

**Trace Attributes**:
- `user_id` - Current user ID
- `resume_id` - Resume being processed
- `job_id` - Job being queried
- `request_id` - Unique request identifier

### Logging
Structured JSON logs with request IDs for correlation.

**Log Fields**:
- `timestamp` - ISO 8601 timestamp
- `level` - `INFO`, `WARNING`, `ERROR`
- `request_id` - Unique request ID
- `user_id` - Current user (if authenticated)
- `endpoint` - API endpoint called
- `duration_ms` - Request duration

---

## Interactive Documentation

**Swagger UI**: [`https://api.resumerag.example.com/docs`](https://api.resumerag.example.com/docs)  
**ReDoc**: [`https://api.resumerag.example.com/redoc`](https://api.resumerag.example.com/redoc)  
**OpenAPI JSON**: [`https://api.resumerag.example.com/openapi.json`](https://api.resumerag.example.com/openapi.json)

---

## SDKs & Client Libraries

*Coming soon*: Official Python and JavaScript client SDKs

**Python Example** (using `requests`):
```python
import requests

API_BASE = "https://api.resumerag.example.com"

# Login
response = requests.post(f"{API_BASE}/api/auth/login", json={
    "email": "user@example.com",
    "password": "SecurePass123!"
})
tokens = response.json()
access_token = tokens["access_token"]

# Upload resume
headers = {
    "Authorization": f"Bearer {access_token}",
    "Idempotency-Key": "unique-uuid-here"
}
files = {"file": open("resume.pdf", "rb")}
data = {"visibility": "private"}
response = requests.post(f"{API_BASE}/api/resumes", headers=headers, files=files, data=data)
print(response.json())
```

---

## Support

- **Documentation**: [Full docs at GitHub](https://github.com/yourusername/ResumeRAG/tree/main/docs)
- **Issues**: [Report bugs on GitHub](https://github.com/yourusername/ResumeRAG/issues)
- **Email**: support@resumerag.example.com

---

_Last updated: January 15, 2024_
