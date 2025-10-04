import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv

from app.db import init_db
from app.routers import auth, resumes, ask, jobs, meta, admin
from app.services.rate_limiter import rate_limiter
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.logging import StructuredLoggingMiddleware, setup_structured_logging
from app.observability.metrics import get_metrics
from app.observability.tracing import setup_tracing

# Load environment variables
load_dotenv()

# Setup structured logging
setup_structured_logging()
logger = logging.getLogger('resumerag')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("Starting up ResumeRAG API...")
    await init_db()
    await rate_limiter.connect()
    
    logger.info("Startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ResumeRAG API...")
    await rate_limiter.close()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="ResumeRAG API",
    description="Resume RAG system with deterministic embeddings and job matching",
    version="1.0.0",
    lifespan=lifespan
)

# Setup tracing (must be before adding middleware)
setup_tracing(app, service_name="resumerag-api")

# CORS configuration
cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*")
if cors_origins == "*":
    origins = ["*"]
else:
    origins = cors_origins.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware (first to ensure all requests have IDs)
app.add_middleware(RequestIDMiddleware)

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware)


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Skip rate limiting for health check and meta endpoints
    if request.url.path in ["/api/health", "/api/_meta", "/.well-known/hackathon.json"]:
        return await call_next(request)
    
    # Determine user identifier
    user_id = "anonymous"
    
    # Try to get user from Authorization header
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        # For simplicity, use token as user_id (in production, decode JWT)
        user_id = f"token_{hash(token)}"
    else:
        # Use client IP
        client_host = request.client.host if request.client else "unknown"
        user_id = f"ip_{client_host}"
    
    # Check rate limit
    allowed = await rate_limiter.check_rate_limit(user_id)
    
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMIT",
                    "message": "Rate limit exceeded: 60 req/min"
                }
            }
        )
    
    response = await call_next(request)
    return response


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Normalize HTTPException responses to have a top-level 'error' key.

    Throughout the code we raise HTTPException with detail={"error": {...}} but FastAPI
    wraps this under {"detail": {...}} by default. Tests expect the error object at the
    top level, so we unwrap it here for consistency.
    """
    detail = exc.detail
    if isinstance(detail, dict) and 'error' in detail:
        return JSONResponse(status_code=exc.status_code, content={'error': detail['error']})
    # Fallback generic shape
    return JSONResponse(status_code=exc.status_code, content={
        'error': {
            'code': 'HTTP_ERROR',
            'message': str(detail)
        }
    })
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    errors = exc.errors()
    
    if errors:
        first_error = errors[0]
        field = ".".join(str(loc) for loc in first_error["loc"])
        message = first_error["msg"]
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "field": field,
                    "message": message
                }
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred"
            }
        }
    )


# Include routers
app.include_router(meta.router)
app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(ask.router)
app.include_router(jobs.router)
app.include_router(admin.router)


# Hackathon manifest endpoint
@app.get("/.well-known/hackathon.json")
async def hackathon_manifest():
    """Return hackathon manifest"""
    return {
        "name": "ResumeRAG",
        "version": "1.0.0",
        "api_root": "/api",
        "endpoints": [
            "/api/health",
            "/api/_meta",
            "/api/resumes",
            "/api/ask",
            "/api/jobs"
        ],
        "notes": "Idempotency-Key required for POST creates. Rate limit: 60 req/min/user."
    }


# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus text format for scraping.
    """
    metrics_data, content_type = get_metrics()
    return Response(content=metrics_data, media_type=content_type)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
