"""
Admin endpoints for system management and auditing
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db import get_db
from app.models import User, UserRole
from app.routers.auth import get_current_user_required
from app.services.auditing import get_pii_access_logs


router = APIRouter(prefix="/api/admin", tags=["admin"])


class PIIAccessLogItem(BaseModel):
    id: str
    actor_user_id: str
    actor_email: Optional[str] = None
    resume_id: str
    action: str
    reason: Optional[str] = None
    request_id: Optional[str] = None
    created_at: str


class PIIAccessLogsResponse(BaseModel):
    items: List[PIIAccessLogItem]
    total: int
    limit: int
    offset: int


async def require_admin(current_user: User = Depends(get_current_user_required)):
    """Dependency to require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "FORBIDDEN", "message": "Admin access required"}}
        )
    return current_user


@router.get("/pii-logs", response_model=PIIAccessLogsResponse)
async def get_pii_logs(
    resume_id: Optional[str] = Query(None),
    actor_user_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get PII access audit logs (admin only)
    
    Returns audit trail of all PII access events including:
    - Who accessed PII
    - Which resume was accessed
    - What action was performed
    - When it occurred
    - Request correlation ID
    """
    # Get logs
    logs = await get_pii_access_logs(
        db=db,
        resume_id=resume_id,
        actor_user_id=actor_user_id,
        limit=limit,
        offset=offset
    )
    
    # Build response
    items = []
    for log in logs:
        # Get actor email (optional enhancement)
        from app.models import User
        from sqlalchemy import select
        
        actor_query = select(User).where(User.id == log.actor_user_id)
        actor_result = await db.execute(actor_query)
        actor = actor_result.scalar_one_or_none()
        
        item = PIIAccessLogItem(
            id=log.id,
            actor_user_id=log.actor_user_id,
            actor_email=actor.email if actor else None,
            resume_id=log.resume_id,
            action=log.action,
            reason=log.reason,
            request_id=log.request_id,
            created_at=log.created_at.isoformat() + "Z"
        )
        items.append(item)
    
    return {
        "items": items,
        "total": len(items),  # TODO: Add total count query
        "limit": limit,
        "offset": offset
    }


@router.post("/pii-logs/export")
async def export_pii_logs(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Export all PII access logs as CSV (admin only)"""
    # TODO: Implement CSV export
    raise HTTPException(
        status_code=501,
        detail={"error": {"code": "NOT_IMPLEMENTED", "message": "CSV export not yet implemented"}}
    )
