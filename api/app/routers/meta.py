from datetime import datetime
from fastapi import APIRouter
from app.schemas import HealthResponse, MetaResponse

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "time": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/_meta", response_model=MetaResponse)
async def get_meta():
    """Return API metadata and available endpoints"""
    return {
        "name": "ResumeRAG",
        "version": "1.0.0",
        "api_root": "/api",
        "endpoints": [
            "/api/health",
            "/api/_meta",
            "/api/auth/register",
            "/api/auth/login",
            "/api/resumes",
            "/api/resumes/{id}",
            "/api/ask",
            "/api/jobs",
            "/api/jobs/{id}",
            "/api/jobs/{id}/match"
        ],
        "features": {
            "idempotency": True,
            "rate_limit": True,
            "pagination": True,
            "pii_redaction": True,
            "deterministic_ranking": True
        }
    }
