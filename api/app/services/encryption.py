"""
PII encryption/decryption service using Fernet (AES-128-CBC)
"""
import os
from cryptography.fernet import Fernet, InvalidToken
from typing import Optional


# Get encryption key from environment
# In production, this should be securely managed (AWS Secrets Manager, Azure Key Vault, etc.)
PII_ENC_KEY = os.getenv("PII_ENC_KEY", "")

if not PII_ENC_KEY:
    # Generate a key for development (WARNING: DO NOT use in production)
    # In production, you MUST set PII_ENC_KEY environment variable
    print("WARNING: PII_ENC_KEY not set. Generating temporary key for development.")
    print("WARNING: In production, you MUST set PII_ENC_KEY from secure secrets management.")
    PII_ENC_KEY = Fernet.generate_key().decode()

# Create cipher suite
try:
    cipher_suite = Fernet(PII_ENC_KEY.encode() if isinstance(PII_ENC_KEY, str) else PII_ENC_KEY)
except Exception as e:
    print(f"ERROR: Invalid PII_ENC_KEY format. Must be a valid Fernet key.")
    print(f"Generate a new key with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")
    raise e


def encrypt_pii(plaintext: str) -> bytes:
    """
    Encrypt PII data
    
    Args:
        plaintext: The plain text to encrypt
        
    Returns:
        Encrypted bytes
    """
    if not plaintext:
        return b""
    
    return cipher_suite.encrypt(plaintext.encode())


def decrypt_pii(ciphertext: bytes) -> Optional[str]:
    """
    Decrypt PII data
    
    Args:
        ciphertext: The encrypted bytes to decrypt
        
    Returns:
        Decrypted string or None if decryption fails
    """
    if not ciphertext:
        return None
    
    try:
        return cipher_suite.decrypt(ciphertext).decode()
    except InvalidToken:
        # Token is invalid or key has changed
        return None
    except Exception:
        return None


def rotate_encryption(old_key: str, new_key: str, ciphertext: bytes) -> bytes:
    """
    Rotate encryption key by decrypting with old key and re-encrypting with new key
    
    Args:
        old_key: The old encryption key
        new_key: The new encryption key
        ciphertext: The data encrypted with old key
        
    Returns:
        Data encrypted with new key
    """
    old_cipher = Fernet(old_key.encode() if isinstance(old_key, str) else old_key)
    new_cipher = Fernet(new_key.encode() if isinstance(new_key, str) else new_key)
    
    # Decrypt with old key
    plaintext = old_cipher.decrypt(ciphertext)
    
    # Encrypt with new key
    return new_cipher.encrypt(plaintext)
