"""
Request ID middleware for request tracing and correlation
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from contextvars import ContextVar

# Context variable to store request ID across async calls
request_id_var: ContextVar[str] = ContextVar('request_id', default='')


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to ensure every request has a unique request ID.
    
    - Accepts incoming X-Request-Id header
    - Generates new UUID if not present
    - Adds X-Request-Id to response headers
    - Stores in context variable for logging/tracing
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get request ID from header or generate new one
        request_id = request.headers.get('X-Request-Id', str(uuid.uuid4()))
        
        # Store in context variable for access throughout request lifecycle
        request_id_var.set(request_id)
        
        # Add to request state for easy access
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers['X-Request-Id'] = request_id
        
        return response


def get_request_id() -> str:
    """Get current request ID from context"""
    return request_id_var.get('')
