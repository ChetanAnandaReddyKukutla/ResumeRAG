"""
PII access logging and auditing service
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import PIIAccessLog, User
from app.utils import generate_id


async def log_pii_access(
    db: AsyncSession,
    actor_user_id: str,
    resume_id: str,
    action: str,
    reason: Optional[str] = None,
    request_id: Optional[str] = None
) -> PIIAccessLog:
    """
    Log PII access event
    
    Args:
        db: Database session
        actor_user_id: ID of the user accessing PII
        resume_id: ID of the resume being accessed
        action: Type of action (VIEW_PII, EXPORT_PII, EDIT_PII, etc.)
        reason: Optional reason for access
        request_id: Optional request ID for correlation
        
    Returns:
        Created PIIAccessLog record
    """
    log_entry = PIIAccessLog(
        id=f"pii_log_{generate_id()}",
        actor_user_id=actor_user_id,
        resume_id=resume_id,
        action=action,
        reason=reason,
        request_id=request_id,
        created_at=datetime.utcnow()
    )
    
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    
    return log_entry


async def get_pii_access_logs(
    db: AsyncSession,
    resume_id: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Query PII access logs
    
    Args:
        db: Database session
        resume_id: Filter by resume ID
        actor_user_id: Filter by actor user ID
        limit: Maximum number of results
        offset: Number of results to skip
        
    Returns:
        List of PIIAccessLog records
    """
    query = select(PIIAccessLog)
    
    if resume_id:
        query = query.where(PIIAccessLog.resume_id == resume_id)
    
    if actor_user_id:
        query = query.where(PIIAccessLog.actor_user_id == actor_user_id)
    
    query = query.order_by(PIIAccessLog.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    return result.scalars().all()


async def has_pii_access_permission(user: User, resume_owner_id: str) -> bool:
    """
    Check if user has permission to access PII
    
    Args:
        user: The user requesting access
        resume_owner_id: The ID of the resume owner
        
    Returns:
        True if user has permission, False otherwise
    """
    # User can access their own PII
    if user.id == resume_owner_id:
        return True
    
    # Recruiters and admins can access any PII
    if user.role.value in ["recruiter", "admin"]:
        return True
    
    return False
