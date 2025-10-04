# Security Guide

## Overview

ResumeRAG Phase 2 implements comprehensive security hardening features to protect sensitive resume data and ensure production-readiness.

## Authentication & Authorization

### JWT + Refresh Tokens

**Access Tokens**
- Short-lived JWT tokens (default: 30 minutes)
- Used for API authentication
- Included in `Authorization: Bearer <token>` header

**Refresh Tokens**
- Long-lived tokens (default: 7 days)
- Used to obtain new access tokens
- Stored hashed (SHA256) in database
- Support token rotation and revocation

**Token Rotation**
```
POST /api/auth/refresh
Body: {"refresh_token": "<token>"}
Response: {"access_token": "<new>", "refresh_token": "<new>"}
```

Each refresh invalidates the old refresh token and issues a new one, preventing token reuse.

**Token Revocation**
```
# Revoke single token
POST /api/auth/revoke
Body: {"refresh_token": "<token>"}

# Revoke all user tokens (logout everywhere)
POST /api/auth/revoke-all
Headers: Authorization: Bearer <access_token>
```

### Account Lockout

**Protection Against Brute Force**
- After 5 failed login attempts, account is locked for 15 minutes
- Lockout duration configurable via `LOCKOUT_DURATION_MINUTES`
- Failed attempt counter resets on successful login

**Environment Variables**
```env
MAX_FAILED_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
```

### Role-Based Access Control (RBAC)

**Roles**
- `user`: Basic access, can only view own resumes
- `recruiter`: Can view all resumes and PII
- `admin`: Full system access including audit logs

## PII Protection

### PII Encryption at Rest

All sensitive PII fields are encrypted using Fernet (AES-128-CBC) symmetric encryption.

**Encrypted Fields**
- Email addresses
- Phone numbers
- Social Security Numbers (SSNs)
- Other personally identifiable information

**Setup Required**

Generate encryption key:
```bash
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Add to `.env`:
```env
PII_ENC_KEY=<your-generated-key>
```

⚠️ **CRITICAL**: In production, manage `PII_ENC_KEY` via secure secrets management:
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Google Cloud Secret Manager

**DO NOT** commit `PII_ENC_KEY` to version control!

### PII Access Auditing

Every PII access is logged to the `pii_access_log` table with:
- Actor user ID and email
- Resume ID accessed
- Action performed (VIEW_PII, EXPORT_PII, etc.)
- Timestamp
- Optional reason and request correlation ID

**Admin Audit Endpoint**
```
GET /api/admin/pii-logs?resume_id=<id>&actor_user_id=<id>&limit=100&offset=0
Headers: Authorization: Bearer <admin_token>
```

**Access Control**
- Users can view PII for their own resumes
- Recruiters can view PII for any resume
- Admins can view PII for any resume
- All PII access attempts are logged

### PII Redaction

Resume endpoints support PII redaction based on user role:

```
GET /api/resumes/{resume_id}?include_pii=false  # Default, PII redacted
GET /api/resumes/{resume_id}?include_pii=true   # Requires permission, logs access
```

Without `include_pii=true`:
- Email: `john.doe@example.com` → `j***e@e***.com`
- Phone: `555-123-4567` → `***-***-4567`
- SSN: `123-45-6789` → `***-**-6789`

## Upload Security

### File Validation

All uploaded files are validated before processing:

**Allowed File Types**
- `.pdf` - PDF documents
- `.docx` - Microsoft Word documents
- `.txt` - Plain text files
- `.zip` - ZIP archives containing resumes

**Checks Performed**
1. File extension validation
2. Content-type header validation
3. File size limit (default: 50 MB)
4. Empty file rejection
5. Malware pattern scanning (basic EICAR detection)

**Configuration**
```env
MAX_FILE_SIZE=52428800  # 50 MB in bytes
```

### Filename Sanitization

All uploaded filenames are sanitized to prevent:
- Directory traversal attacks (`../../etc/passwd`)
- Dangerous characters (`<>:"|?*`)
- Overly long filenames (>255 characters)

### Malware Scanning

**Basic Protection** (Built-in)
- EICAR test signature detection
- Pattern-based malicious content detection

**Advanced Protection** (Optional)
For production, integrate ClamAV or VirusTotal:

1. Install ClamAV:
```bash
apt-get install clamav clamav-daemon
pip install clamd
```

2. Enable in `upload_security.py` (see commented code)

3. Configure `clamd` connection settings

## Rate Limiting

Token bucket rate limiting per user:
- 60 requests per minute per authenticated user
- Configurable via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW`

```env
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60
```

## Secrets Management

### Development
```env
SECRET_KEY=your-secret-key-here
PII_ENC_KEY=<generated-fernet-key>
```

### Production

**DO NOT** use environment files in production. Use secrets management:

**AWS Secrets Manager**
```python
import boto3
secrets = boto3.client('secretsmanager')
secret = secrets.get_secret_value(SecretId='resumerag/pii-enc-key')
PII_ENC_KEY = secret['SecretString']
```

**Azure Key Vault**
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://<vault>.vault.azure.net", credential=credential)
PII_ENC_KEY = client.get_secret("pii-enc-key").value
```

**Environment Variables**
For containerized deployments, inject secrets as environment variables at runtime (never in Dockerfile).

## Database Security

### Connection Security
- Use SSL/TLS for PostgreSQL connections in production
- Configure `DATABASE_URL` with `sslmode=require`

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?sslmode=require
```

### Migration Security
- Alembic migrations include security schema changes
- Run migrations in maintenance windows
- Backup database before applying migrations

## API Security Headers

Recommended headers for reverse proxy (nginx, ALB, etc.):

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Content-Security-Policy "default-src 'self'" always;
```

## Security Checklist for Production

- [ ] Generate and securely store `SECRET_KEY`
- [ ] Generate and securely store `PII_ENC_KEY`
- [ ] Configure secrets management (AWS/Azure/Vault)
- [ ] Enable SSL/TLS for PostgreSQL
- [ ] Enable SSL/TLS for Redis
- [ ] Configure CORS with specific origins (not `*`)
- [ ] Enable ClamAV or VirusTotal for malware scanning
- [ ] Configure rate limiting for your workload
- [ ] Set up monitoring and alerting for failed logins
- [ ] Review and configure account lockout settings
- [ ] Enable database backups
- [ ] Set up audit log retention policies
- [ ] Configure logging and SIEM integration
- [ ] Perform security testing (penetration testing, vulnerability scanning)
- [ ] Review and update dependencies regularly

## Compliance

### GDPR Considerations
- PII encryption at rest
- PII access auditing
- Right to be forgotten (implement resume deletion)
- Data export capabilities

### SOC 2 Considerations
- Access logging and monitoring
- Encryption in transit and at rest
- Role-based access control
- Audit trail maintenance

## Incident Response

If a security incident occurs:

1. **Immediate Actions**
   - Revoke all refresh tokens: Use `/api/auth/revoke-all` for affected users
   - Rotate `PII_ENC_KEY` if compromised (see key rotation procedure)
   - Review audit logs: `/api/admin/pii-logs`

2. **Investigation**
   - Check `pii_access_log` table for unauthorized access
   - Review failed login attempts in `users` table
   - Analyze rate limiter logs in Redis

3. **Recovery**
   - Reset affected user passwords
   - Notify affected users
   - Update secrets and redeploy

## Key Rotation Procedure

**Rotating PII Encryption Key**

1. Generate new key:
```bash
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

2. Update secrets manager with new key as `PII_ENC_KEY_NEW`

3. Run key rotation script (TODO: implement):
```python
from app.services.encryption import rotate_encryption
# Re-encrypt all PII with new key
```

4. Replace `PII_ENC_KEY` with `PII_ENC_KEY_NEW`

5. Remove `PII_ENC_KEY_NEW`

**Rotating JWT Secret**

1. Generate new secret
2. Update `SECRET_KEY` in secrets manager
3. Restart application
4. All existing access tokens become invalid (users need to refresh)

## Security Contact

For security issues, please report to: security@yourcompany.com

**DO NOT** create public GitHub issues for security vulnerabilities.
