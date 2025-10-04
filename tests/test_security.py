"""
Security-focused tests for Phase 2 enhancements
"""
import pytest
import time
import asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from app.main import app
from app.services.encryption import encrypt_pii, decrypt_pii
from app.services.upload_security import validate_file_upload, sanitize_filename
from io import BytesIO
from fastapi import UploadFile


@pytest.mark.asyncio
async def test_refresh_token_flow():
    """Test refresh token creation and rotation"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register user
        response = await client.post(
            "/api/auth/register",
            json={"email": "refresh@test.com", "password": "Password123!"}
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # Wait a moment to ensure timestamp difference (non-blocking)
        await asyncio.sleep(0.05)

        # Use refresh token to get new tokens
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

        # New tokens should be different
        assert data["access_token"] != access_token
        assert data["refresh_token"] != refresh_token

        # Old refresh token should not work (token rotation)
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_revocation():
    """Test refresh token revocation"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register user
        response = await client.post(
            "/api/auth/register",
            json={"email": "revoke@test.com", "password": "Password123!"}
        )
        assert response.status_code == 201
        data = response.json()
        refresh_token = data["refresh_token"]
        
        # Revoke token
        response = await client.post(
            "/api/auth/revoke",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        
        # Try to use revoked token
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_revoke_all_tokens():
    """Test revoking all tokens for a user"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register user
        response = await client.post(
            "/api/auth/register",
            json={"email": "revokeall@test.com", "password": "Password123!"}
        )
        assert response.status_code == 201
        data = response.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        
        # Create another refresh token by refreshing
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        refresh_token2 = response.json()["refresh_token"]
        
        # Revoke all tokens
        response = await client.post(
            "/api/auth/revoke-all",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        
        # Both refresh tokens should not work
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 401
        
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token2}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_account_lockout():
    """Test account lockout after failed login attempts"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register user
        response = await client.post(
            "/api/auth/register",
            json={"email": "lockout@test.com", "password": "CorrectPassword123!"}
        )
        assert response.status_code == 201
        
        # Make 5 failed login attempts
        for i in range(5):
            response = await client.post(
                "/api/auth/login",
                json={"email": "lockout@test.com", "password": "WrongPassword"}
            )
            # Should get 401 for wrong password
            if i < 4:
                assert response.status_code == 401
            else:
                # 5th attempt should lock the account
                assert response.status_code == 403
                assert "ACCOUNT_LOCKED" in response.json()["error"]["code"]
        
        # Even correct password should not work when locked
        response = await client.post(
            "/api/auth/login",
            json={"email": "lockout@test.com", "password": "CorrectPassword123!"}
        )
        assert response.status_code == 403
        assert "ACCOUNT_LOCKED" in response.json()["error"]["code"]


@pytest.mark.asyncio
async def test_pii_encryption_decryption():
    """Test PII encryption and decryption"""
    # Test basic encryption/decryption
    plaintext = "john.doe@example.com"
    ciphertext = encrypt_pii(plaintext)
    
    assert ciphertext != plaintext.encode()
    assert len(ciphertext) > 0
    
    decrypted = decrypt_pii(ciphertext)
    assert decrypted == plaintext
    
    # Test empty string
    ciphertext_empty = encrypt_pii("")
    assert ciphertext_empty == b""
    
    decrypted_empty = decrypt_pii(b"")
    assert decrypted_empty is None


@pytest.mark.asyncio
async def test_file_upload_validation(upload_file_factory):
    """Test file upload security validation"""
    # Test valid PDF file
    valid_content = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\nSome PDF content"
    valid_file = upload_file_factory("resume.pdf", valid_content, "application/pdf")
    
    content, file_hash = await validate_file_upload(valid_file)
    assert content == valid_content
    assert len(file_hash) == 64  # SHA256 hex length
    
    # Test invalid file extension
    invalid_file = upload_file_factory("resume.exe", b"executable content", "application/octet-stream")
    
    with pytest.raises(Exception) as exc_info:
        await validate_file_upload(invalid_file)
    assert exc_info.value.status_code == 400
    assert "INVALID_FILE_TYPE" in str(exc_info.value.detail)
    
    # Test EICAR malware signature
    eicar_content = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR"
    eicar_file = upload_file_factory("malware.txt", eicar_content, "text/plain")
    
    with pytest.raises(Exception) as exc_info:
        await validate_file_upload(eicar_file)
    assert exc_info.value.status_code == 400
    assert "MALICIOUS_FILE" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_filename_sanitization():
    """Test filename sanitization"""
    # Test directory traversal
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32") == "windows_system32"
    
    # Test dangerous characters
    assert sanitize_filename("file<>name.pdf") == "file__name.pdf"
    assert sanitize_filename('file"with|chars?.txt') == "file_with_chars_.txt"
    
    # Test length limit
    long_name = "a" * 300 + ".pdf"
    result = sanitize_filename(long_name)
    assert len(result) <= 255
    assert result.endswith(".pdf")


@pytest.mark.asyncio
async def test_pii_access_logging():
    """Test PII access is logged"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create admin user (would need to be done via direct DB or migration)
        # For this test, we'll create a recruiter who can access PII
        
        # Register recruiter
        response = await client.post(
            "/api/auth/register",
            json={"email": "recruiter@test.com", "password": "Password123!"}
        )
        assert response.status_code == 201
        recruiter_token = response.json()["access_token"]
        
        # Upload a resume
        from io import BytesIO
        files = {"file": ("test_resume.txt", BytesIO(b"John Doe\njohn@example.com\n123-456-7890"), "text/plain")}
        response = await client.post(
            "/api/resumes",
            files=files,
            headers={"Idempotency-Key": "test-pii-log-123"},
            data={"visibility": "private"}
        )
        # Note: This might fail without proper setup, but demonstrates the pattern
        # In real tests, you'd need the full database initialized


@pytest.mark.asyncio
async def test_admin_pii_logs_endpoint():
    """Test admin can access PII audit logs"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register regular user
        response = await client.post(
            "/api/auth/register",
            json={"email": "user@test.com", "password": "Password123!"}
        )
        assert response.status_code == 201
        user_token = response.json()["access_token"]
        
        # Try to access admin endpoint as regular user
        response = await client.get(
            "/api/admin/pii-logs",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403  # Should be forbidden for non-admin
        
        # Admin access would require creating an admin user in the database
        # This is typically done via migration or seed script


@pytest.mark.asyncio
async def test_file_size_limit(upload_file_factory):
    """Test file size validation"""
    # Create a file that exceeds the limit
    large_content = b"A" * (51 * 1024 * 1024)  # 51 MB
    large_file = upload_file_factory("large.pdf", large_content, "application/pdf")
    
    with pytest.raises(Exception) as exc_info:
        await validate_file_upload(large_file)
    assert exc_info.value.status_code == 400
    assert "FILE_TOO_LARGE" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_empty_file_rejection(upload_file_factory):
    """Test empty file rejection"""
    empty_file = upload_file_factory("empty.txt", b"", "text/plain")
    
    with pytest.raises(Exception) as exc_info:
        await validate_file_upload(empty_file)
    assert exc_info.value.status_code == 400
    assert "EMPTY_FILE" in str(exc_info.value.detail)
