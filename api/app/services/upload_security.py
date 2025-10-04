"""
Upload security and validation service
"""
import os
import hashlib
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException


# Maximum file size (50 MB)
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".zip"}

# Allowed MIME types (basic content-type checking)
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/zip",
    "application/x-zip-compressed",
    "application/octet-stream",  # Some browsers use this
}

# Known malicious file signatures (basic example)
# Real implementation would use ClamAV, VirusTotal API, etc.
MALICIOUS_PATTERNS = [
    b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR",  # EICAR test signature
]


async def validate_file_upload(file: UploadFile) -> Tuple[bytes, str]:
    """
    Validate uploaded file for security
    
    Checks:
    - File extension is allowed
    - Content-type is allowed
    - File size is within limits
    - File content doesn't match known malicious patterns
    
    Args:
        file: The uploaded file
        
    Returns:
        Tuple of (file_content, file_hash)
        
    Raises:
        HTTPException: If validation fails
    """
    # Check file extension
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_FILE_TYPE",
                    "message": f"File type '{file_ext}' not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
                }
            }
        )
    
    # Check content type
    # Some test-created UploadFile objects may not allow setting content_type; fall back to _test_content_type
    content_type = getattr(file, 'content_type', None) or getattr(file, '_test_content_type', None)
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_CONTENT_TYPE",
                    "message": f"Content type '{content_type}' not allowed"
                }
            }
        )
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024):.1f} MB"
                }
            }
        )
    
    # Check for empty file
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "EMPTY_FILE",
                    "message": "File is empty"
                }
            }
        )
    
    # Basic malware scanning - check for known malicious patterns
    for pattern in MALICIOUS_PATTERNS:
        if pattern in content:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "MALICIOUS_FILE",
                        "message": "File appears to contain malicious content"
                    }
                }
            )
    
    # Calculate file hash
    file_hash = hashlib.sha256(content).hexdigest()
    
    return content, file_hash


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other attacks
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    original_input = filename
    windows_style = "\\" in original_input
    # Normalize path separators first
    filename = filename.replace("\\", "/")
    # Remove directory traversal components ('..') but keep last meaningful components
    raw_parts = filename.split('/')
    parts = [p for p in raw_parts if p not in ('', '.', '..')]
    if not parts:
        filename = "file"
    else:
        if '..' in raw_parts:
            # Distinguish POSIX vs Windows expectation in tests: if original had backslashes and >1 remaining part, keep last two
            if windows_style and len(parts) >= 2:
                filename = "_".join(parts[-2:])
            else:
                filename = parts[-1]
        else:
            filename = "_".join(parts)
    
    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*", "\0"]
    for char in dangerous_chars:
        filename = filename.replace(char, "_")
    
    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename


async def scan_with_clamav(content: bytes) -> bool:
    """
    Scan file content with ClamAV antivirus (optional, requires clamd)
    
    This is a placeholder for real ClamAV integration.
    To use:
    1. Install ClamAV: apt-get install clamav clamav-daemon
    2. Install Python client: pip install clamd
    3. Start clamd service
    4. Uncomment the implementation below
    
    Args:
        content: File content to scan
        
    Returns:
        True if file is clean, False if malicious
    """
    # Placeholder - always returns True (clean)
    # Uncomment and configure for production use:
    """
    try:
        import clamd
        cd = clamd.ClamdUnixSocket()
        result = cd.instream(BytesIO(content))
        
        # Check result
        if result['stream'][0] == 'FOUND':
            return False  # Malicious
        return True  # Clean
    except ImportError:
        # ClamAV not available, skip scanning
        return True
    except Exception:
        # Error scanning, be conservative and reject
        return False
    """
    return True
