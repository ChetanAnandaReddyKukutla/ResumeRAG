import re
from typing import Optional, Dict, Any


def redact_email(text: str) -> str:
    """Redact email addresses in text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.sub(email_pattern, '[REDACTED]', text)


def redact_phone(text: str) -> str:
    """Redact phone numbers in text"""
    # Pattern for various phone formats
    phone_patterns = [
        r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\d{3}-\d{3}-\d{4}',
        r'\(\d{3}\)\s*\d{3}-\d{4}',
    ]
    
    result = text
    for pattern in phone_patterns:
        result = re.sub(pattern, '[REDACTED]', result)
    
    return result


def redact_ssn(text: str) -> str:
    """Redact social security numbers"""
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    return re.sub(ssn_pattern, '[REDACTED]', text)


def redact_pii(text: str) -> str:
    """Redact all PII from text"""
    text = redact_email(text)
    text = redact_phone(text)
    text = redact_ssn(text)
    return text


def redact_metadata(metadata: Dict[str, Any], user_role: str = "user") -> Dict[str, Any]:
    """
    Redact PII from metadata based on user role
    
    Args:
        metadata: Metadata dictionary
        user_role: Role of requesting user (recruiter can see unredacted)
    
    Returns:
        Metadata with PII redacted if necessary
    """
    if user_role == "recruiter":
        return metadata
    
    redacted = metadata.copy()
    
    if "email" in redacted and redacted["email"]:
        redacted["email"] = "[REDACTED]"
    
    if "phone" in redacted and redacted["phone"]:
        redacted["phone"] = "[REDACTED]"
    
    return redacted


def redact_snippet_text(text: str, user_role: str = "user") -> str:
    """
    Redact PII from snippet text based on user role
    
    Args:
        text: Text to redact
        user_role: Role of requesting user
    
    Returns:
        Text with PII redacted if necessary
    """
    if user_role == "recruiter":
        return text
    
    return redact_pii(text)
