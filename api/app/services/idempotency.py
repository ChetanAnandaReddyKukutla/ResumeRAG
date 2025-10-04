import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.future import select

from app.models import IdempotencyKey


def compute_request_hash(data: Dict[str, Any]) -> str:
    """Compute hash of request payload for idempotency check"""
    # Sort keys for consistent hashing
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


async def check_idempotency_key(
    db: AsyncSession,
    key: str,
    user_id: Optional[str],
    request_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Check if idempotency key exists and return stored response if valid
    
    Args:
        db: Database session
        key: Idempotency key
        user_id: User ID (optional)
        request_data: Request payload
    
    Returns:
        Stored response if key exists with matching request, None otherwise
    
    Raises:
        ValueError: If key exists but request differs (409 conflict)
    """
    # Clean up expired keys first
    now = datetime.utcnow()
    await db.execute(
        select(IdempotencyKey).where(IdempotencyKey.expires_at < now)
    )
    
    # Check for existing key
    query = select(IdempotencyKey).where(IdempotencyKey.key == key)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        # Check if request matches
        request_hash = compute_request_hash(request_data)
        
        if existing.request_hash == request_hash:
            # Same request, return stored response
            return existing.response_json
        else:
            # Different request with same key
            raise ValueError("Idempotency key already used with different request")
    
    return None


async def store_idempotency_key(
    db: AsyncSession,
    key: str,
    user_id: Optional[str],
    request_data: Dict[str, Any],
    response_data: Dict[str, Any],
    ttl_hours: int = 24
) -> None:
    """
    Store idempotency key with response
    
    Args:
        db: Database session
        key: Idempotency key
        user_id: User ID (optional)
        request_data: Request payload
        response_data: Response to store
        ttl_hours: Time to live in hours
    """
    request_hash = compute_request_hash(request_data)
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    
    idempotency_record = IdempotencyKey(
        key=key,
        user_id=user_id,
        request_hash=request_hash,
        response_json=response_data,
        created_at=datetime.utcnow(),
        expires_at=expires_at
    )
    
    db.add(idempotency_record)
    await db.commit()
