# Security Testing Checklist

This checklist helps verify that all Phase 2 security features are working correctly.

## Pre-Testing Setup

- [ ] Application is running (Docker Compose or manual)
- [ ] Database migrations completed (002_security_hardening)
- [ ] Environment variables configured (PII_ENC_KEY, etc.)
- [ ] Test user accounts created (user, recruiter, admin)
- [ ] Testing tools available (curl, Postman, or httpx)

## 1. Authentication Tests

### 1.1 User Registration with Refresh Token

**Test:** Register new user and verify refresh token is returned

```powershell
$response = Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/auth/register" `
    -ContentType "application/json" `
    -Body '{"email":"test1@example.com","password":"TestPass123!"}'

# Verify
$response.access_token -ne $null  # Should be true
$response.refresh_token -ne $null  # Should be true
$response.token_type -eq "bearer"  # Should be true
```

**Expected:** ✅ All assertions pass  
**If Failed:** Check Token schema includes refresh_token field

---

### 1.2 User Login with Refresh Token

**Test:** Login existing user and verify refresh token

```powershell
$response = Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/auth/login" `
    -ContentType "application/json" `
    -Body '{"email":"test1@example.com","password":"TestPass123!"}'

# Save tokens
$access_token = $response.access_token
$refresh_token = $response.refresh_token
```

**Expected:** ✅ Both tokens returned  
**If Failed:** Check auth.py login endpoint returns refresh token

---

### 1.3 Refresh Token Rotation

**Test:** Use refresh token to get new tokens, verify old token is revoked

```powershell
# First refresh (should work)
$response1 = Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/auth/refresh" `
    -ContentType "application/json" `
    -Body "{`"refresh_token`":`"$refresh_token`"}"

$new_refresh_token = $response1.refresh_token

# Try to reuse old token (should fail)
try {
    $response2 = Invoke-RestMethod -Method Post `
        -Uri "http://localhost:8000/api/auth/refresh" `
        -ContentType "application/json" `
        -Body "{`"refresh_token`":`"$refresh_token`"}"
    Write-Host "❌ FAILED: Old token still works!"
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "✅ PASSED: Old token revoked"
    }
}
```

**Expected:** ✅ First refresh works, second fails with 401  
**If Failed:** Check token rotation logic in auth.py refresh endpoint

---

### 1.4 Token Revocation

**Test:** Revoke token and verify it cannot be used

```powershell
# Use new token to get another refresh
$response = Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/auth/refresh" `
    -ContentType "application/json" `
    -Body "{`"refresh_token`":`"$new_refresh_token`"}"

$token_to_revoke = $response.refresh_token

# Revoke it
Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/auth/revoke" `
    -ContentType "application/json" `
    -Body "{`"refresh_token`":`"$token_to_revoke`"}"

# Try to use revoked token
try {
    Invoke-RestMethod -Method Post `
        -Uri "http://localhost:8000/api/auth/refresh" `
        -ContentType "application/json" `
        -Body "{`"refresh_token`":`"$token_to_revoke`"}"
    Write-Host "❌ FAILED: Revoked token still works!"
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "✅ PASSED: Revoked token rejected"
    }
}
```

**Expected:** ✅ Revoked token cannot be used  
**If Failed:** Check revoke endpoint sets revoked=true

---

### 1.5 Revoke All Tokens

**Test:** Revoke all tokens for a user

```powershell
# Create multiple tokens by refreshing
# ... (get multiple refresh tokens)

# Revoke all
Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/auth/revoke-all" `
    -Headers @{"Authorization"="Bearer $access_token"}

# Try to use any refresh token (should all fail)
# Test with each token created above
```

**Expected:** ✅ All refresh tokens revoked  
**If Failed:** Check revoke-all updates all user tokens

---

## 2. Account Lockout Tests

### 2.1 Failed Login Lockout

**Test:** Account locks after MAX_FAILED_ATTEMPTS (default: 5)

```powershell
# Register test user
Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/auth/register" `
    -ContentType "application/json" `
    -Body '{"email":"lockout@example.com","password":"CorrectPass123!"}'

# Make 5 failed attempts
for ($i=1; $i -le 5; $i++) {
    try {
        Invoke-RestMethod -Method Post `
            -Uri "http://localhost:8000/api/auth/login" `
            -ContentType "application/json" `
            -Body "{`"email`":`"lockout@example.com`",`"password`":`"wrong$i`"}"
    } catch {
        Write-Host "Attempt $i failed (expected)"
    }
}

# 6th attempt with correct password should fail
try {
    Invoke-RestMethod -Method Post `
        -Uri "http://localhost:8000/api/auth/login" `
        -ContentType "application/json" `
        -Body '{"email":"lockout@example.com","password":"CorrectPass123!"}'
    Write-Host "❌ FAILED: Account not locked!"
} catch {
    if ($_.Exception.Response.StatusCode -eq 403) {
        $error_msg = ($_.ErrorDetails.Message | ConvertFrom-Json).error.code
        if ($error_msg -eq "ACCOUNT_LOCKED") {
            Write-Host "✅ PASSED: Account locked correctly"
        }
    }
}
```

**Expected:** ✅ Account locked with 403 and ACCOUNT_LOCKED error  
**If Failed:** Check failed_login_count tracking and lockout logic

---

### 2.2 Lockout Duration

**Test:** Account unlocks after LOCKOUT_DURATION_MINUTES

```powershell
# Wait for lockout to expire (default: 15 minutes)
# For testing, you can temporarily set LOCKOUT_DURATION_MINUTES=1 in .env

# After waiting, try to login with correct password
$response = Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/auth/login" `
    -ContentType "application/json" `
    -Body '{"email":"lockout@example.com","password":"CorrectPass123!"}'

if ($response.access_token) {
    Write-Host "✅ PASSED: Account unlocked after duration"
}
```

**Expected:** ✅ Login succeeds after waiting  
**If Failed:** Check locked_until comparison in auth logic

---

### 2.3 Successful Login Resets Counter

**Test:** Failed count resets on successful login

```powershell
# Register new user
Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/auth/register" `
    -ContentType "application/json" `
    -Body '{"email":"reset@example.com","password":"Pass123!"}'

# Make 3 failed attempts
for ($i=1; $i -le 3; $i++) {
    try {
        Invoke-RestMethod -Method Post `
            -Uri "http://localhost:8000/api/auth/login" `
            -ContentType "application/json" `
            -Body '{"email":"reset@example.com","password":"wrong"}'
    } catch {}
}

# Successful login
Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/auth/login" `
    -ContentType "application/json" `
    -Body '{"email":"reset@example.com","password":"Pass123!"}'

# Make 4 more failed attempts (should not lock yet if counter reset)
for ($i=1; $i -le 4; $i++) {
    try {
        Invoke-RestMethod -Method Post `
            -Uri "http://localhost:8000/api/auth/login" `
            -ContentType "application/json" `
            -Body '{"email":"reset@example.com","password":"wrong"}'
    } catch {}
}

# This should work (only 4 failures since last success)
$response = Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/auth/login" `
    -ContentType "application/json" `
    -Body '{"email":"reset@example.com","password":"Pass123!"}'

if ($response.access_token) {
    Write-Host "✅ PASSED: Counter reset on success"
}
```

**Expected:** ✅ Login succeeds (counter was reset)  
**If Failed:** Check handle_successful_login resets counter

---

## 3. PII Encryption Tests

### 3.1 Encryption/Decryption Roundtrip

**Test:** Encrypt and decrypt data successfully

```python
# Run in Python
from app.services.encryption import encrypt_pii, decrypt_pii

plaintext = "john.doe@example.com"
ciphertext = encrypt_pii(plaintext)
decrypted = decrypt_pii(ciphertext)

assert ciphertext != plaintext.encode(), "Data not encrypted!"
assert decrypted == plaintext, "Decryption failed!"
print("✅ PASSED: Encryption/decryption works")
```

**Expected:** ✅ Data encrypted and decrypts correctly  
**If Failed:** Check PII_ENC_KEY is valid Fernet key

---

### 3.2 Empty String Handling

**Test:** Empty strings handled correctly

```python
from app.services.encryption import encrypt_pii, decrypt_pii

# Empty string
cipher_empty = encrypt_pii("")
assert cipher_empty == b"", "Empty string not handled"

# None/empty decryption
plain_empty = decrypt_pii(b"")
assert plain_empty is None, "Empty decryption not handled"

print("✅ PASSED: Empty strings handled")
```

**Expected:** ✅ Empty strings handled gracefully  
**If Failed:** Check empty string checks in encryption.py

---

## 4. Upload Security Tests

### 4.1 Valid File Upload

**Test:** Valid files are accepted

```powershell
# Create test PDF
$pdfContent = "%PDF-1.4`n%âãÏÓ`nTest content"
$pdfPath = "test.pdf"
[IO.File]::WriteAllText($pdfPath, $pdfContent)

# Upload
$response = Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/resumes" `
    -Headers @{"Idempotency-Key"="test-upload-1"; "Authorization"="Bearer $access_token"} `
    -Form @{
        file = Get-Item $pdfPath
        visibility = "private"
    }

if ($response.id) {
    Write-Host "✅ PASSED: Valid file accepted"
}

Remove-Item $pdfPath
```

**Expected:** ✅ File accepted and processed  
**If Failed:** Check validate_file_upload allows PDF

---

### 4.2 Invalid File Extension Rejected

**Test:** Invalid extensions are rejected

```powershell
# Create test .exe file
$exePath = "malware.exe"
"MZ" | Out-File $exePath

# Try to upload
try {
    $response = Invoke-RestMethod -Method Post `
        -Uri "http://localhost:8000/api/resumes" `
        -Headers @{"Idempotency-Key"="test-invalid-1"; "Authorization"="Bearer $access_token"} `
        -Form @{file = Get-Item $exePath; visibility = "private"}
    Write-Host "❌ FAILED: Invalid extension accepted!"
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "✅ PASSED: Invalid extension rejected"
    }
}

Remove-Item $exePath
```

**Expected:** ✅ Upload rejected with 400 and INVALID_FILE_TYPE  
**If Failed:** Check file extension validation

---

### 4.3 File Size Limit Enforced

**Test:** Oversized files are rejected

```powershell
# Create large file (51 MB)
$largePath = "large.pdf"
$largeContent = "A" * (51 * 1024 * 1024)
[IO.File]::WriteAllText($largePath, $largeContent)

# Try to upload
try {
    $response = Invoke-RestMethod -Method Post `
        -Uri "http://localhost:8000/api/resumes" `
        -Headers @{"Idempotency-Key"="test-large-1"; "Authorization"="Bearer $access_token"} `
        -Form @{file = Get-Item $largePath; visibility = "private"}
    Write-Host "❌ FAILED: Large file accepted!"
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "✅ PASSED: Large file rejected"
    }
}

Remove-Item $largePath
```

**Expected:** ✅ Upload rejected with 400 and FILE_TOO_LARGE  
**If Failed:** Check file size validation

---

### 4.4 Malware Pattern Detection

**Test:** EICAR test signature is detected

```powershell
# Create EICAR test file
$eicarPath = "eicar.txt"
$eicar = "X5O!P%@AP[4\PZX54(P^)7CC)7}`$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!`$H+H*"
[IO.File]::WriteAllText($eicarPath, $eicar)

# Try to upload
try {
    $response = Invoke-RestMethod -Method Post `
        -Uri "http://localhost:8000/api/resumes" `
        -Headers @{"Idempotency-Key"="test-eicar-1"; "Authorization"="Bearer $access_token"} `
        -Form @{file = Get-Item $eicarPath; visibility = "private"}
    Write-Host "❌ FAILED: Malware not detected!"
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "✅ PASSED: Malware detected"
    }
}

Remove-Item $eicarPath
```

**Expected:** ✅ Upload rejected with 400 and MALICIOUS_FILE  
**If Failed:** Check malware pattern scanning

---

### 4.5 Filename Sanitization

**Test:** Dangerous filenames are sanitized

```python
from app.services.upload_security import sanitize_filename

# Directory traversal
assert sanitize_filename("../../etc/passwd") == "passwd"

# Dangerous characters
assert sanitize_filename("file<>name.pdf") == "file__name.pdf"

# Length limit
long_name = "a" * 300 + ".pdf"
result = sanitize_filename(long_name)
assert len(result) <= 255
assert result.endswith(".pdf")

print("✅ PASSED: Filename sanitization works")
```

**Expected:** ✅ All assertions pass  
**If Failed:** Check sanitize_filename function

---

## 5. PII Access Auditing Tests

### 5.1 PII Access is Logged

**Test:** Accessing PII creates audit log entry

```powershell
# Upload resume
$response = Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/resumes" `
    -Headers @{"Idempotency-Key"="test-pii-1"; "Authorization"="Bearer $recruiter_token"} `
    -Form @{file = Get-Item "test_resume.txt"; visibility = "private"}
$resume_id = $response.id

# Access with PII
Invoke-RestMethod -Method Get `
    -Uri "http://localhost:8000/api/resumes/$resume_id?include_pii=true" `
    -Headers @{"Authorization"="Bearer $recruiter_token"}

# Check audit log (as admin)
$logs = Invoke-RestMethod -Method Get `
    -Uri "http://localhost:8000/api/admin/pii-logs?resume_id=$resume_id" `
    -Headers @{"Authorization"="Bearer $admin_token"}

if ($logs.items.Count -gt 0) {
    Write-Host "✅ PASSED: PII access logged"
} else {
    Write-Host "❌ FAILED: PII access not logged"
}
```

**Expected:** ✅ Audit log entry created  
**If Failed:** Check log_pii_access called in resume detail endpoint

---

### 5.2 PII Access Permission Check

**Test:** Users without permission cannot access PII

```powershell
# User tries to access another user's resume with PII
try {
    Invoke-RestMethod -Method Get `
        -Uri "http://localhost:8000/api/resumes/$other_user_resume?include_pii=true" `
        -Headers @{"Authorization"="Bearer $user_token"}
    Write-Host "❌ FAILED: Unauthorized PII access allowed!"
} catch {
    if ($_.Exception.Response.StatusCode -eq 403) {
        Write-Host "✅ PASSED: PII access denied correctly"
    }
}
```

**Expected:** ✅ 403 Forbidden  
**If Failed:** Check has_pii_access_permission logic

---

## 6. Admin Endpoint Tests

### 6.1 Admin Can Access Audit Logs

**Test:** Admin role can access /api/admin/pii-logs

```powershell
$logs = Invoke-RestMethod -Method Get `
    -Uri "http://localhost:8000/api/admin/pii-logs" `
    -Headers @{"Authorization"="Bearer $admin_token"}

if ($logs.items) {
    Write-Host "✅ PASSED: Admin can access logs"
}
```

**Expected:** ✅ 200 OK with logs  
**If Failed:** Check admin authorization

---

### 6.2 Non-Admin Cannot Access Audit Logs

**Test:** Regular user gets 403

```powershell
try {
    Invoke-RestMethod -Method Get `
        -Uri "http://localhost:8000/api/admin/pii-logs" `
        -Headers @{"Authorization"="Bearer $user_token"}
    Write-Host "❌ FAILED: Non-admin accessed logs!"
} catch {
    if ($_.Exception.Response.StatusCode -eq 403) {
        Write-Host "✅ PASSED: Non-admin denied"
    }
}
```

**Expected:** ✅ 403 Forbidden  
**If Failed:** Check require_admin dependency

---

## 7. CI Security Scanning Tests

### 7.1 Bandit Scan

**Test:** Python security linter runs

```powershell
cd api
pip install bandit
bandit -r app -ll

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PASSED: Bandit scan passed"
} else {
    Write-Host "⚠️ WARNING: Bandit found issues"
}
```

**Expected:** ✅ No HIGH/CRITICAL issues  
**If Failed:** Review and fix Bandit findings

---

### 7.2 Safety Scan

**Test:** Dependency vulnerability scanner

```powershell
cd api
pip install safety
safety check --file requirements.txt

# Check output
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PASSED: Safety scan passed"
} else {
    Write-Host "⚠️ WARNING: Safety found vulnerabilities"
}
```

**Expected:** ✅ No known vulnerabilities  
**If Failed:** Update vulnerable dependencies

---

## 8. Database Schema Tests

### 8.1 New Tables Exist

**Test:** Phase 2 tables created

```sql
-- Run in psql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('refresh_tokens', 'pii_store', 'pii_access_log');
```

**Expected:** ✅ All 3 tables exist  
**If Failed:** Run migration: `alembic upgrade head`

---

### 8.2 User Table Updated

**Test:** Security columns added to users

```sql
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('failed_login_count', 'last_failed_login', 'locked_until');
```

**Expected:** ✅ All 3 columns exist  
**If Failed:** Run migration: `alembic upgrade head`

---

## Summary

### Quick Check Script

Save this as `test_phase2_security.ps1`:

```powershell
# Phase 2 Security Quick Test
Write-Host "=== Phase 2 Security Tests ===" -ForegroundColor Cyan

# Test 1: Refresh token
Write-Host "`n1. Testing refresh token..." -ForegroundColor Yellow
# ... (add test code)

# Test 2: Account lockout
Write-Host "`n2. Testing account lockout..." -ForegroundColor Yellow
# ... (add test code)

# Test 3: File validation
Write-Host "`n3. Testing file validation..." -ForegroundColor Yellow
# ... (add test code)

# Test 4: Admin endpoint
Write-Host "`n4. Testing admin endpoint..." -ForegroundColor Yellow
# ... (add test code)

Write-Host "`n=== Tests Complete ===" -ForegroundColor Cyan
```

### Checklist Summary

✅ All tests passing = Phase 2 fully functional  
⚠️ Some tests failing = Review specific failures  
❌ Many tests failing = Check migration and configuration

## Test Coverage Report

Generate with pytest:

```powershell
cd tests
pytest test_security.py --cov=app --cov-report=html
```

Open `htmlcov/index.html` to view coverage report.

Target: >80% coverage for security-critical code.
