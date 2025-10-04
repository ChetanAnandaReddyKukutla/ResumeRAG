"""
Structured JSON logging middleware with PII masking
"""
import json
import logging
import time
import re
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.request_id import get_request_id
from app.observability.metrics import track_http_request


# Configure JSON logging
class StructuredLogger(logging.Handler):
    """Custom logging handler that outputs structured JSON logs"""

    def emit(self, record: logging.LogRecord):  # type: ignore[override]
        # Avoid duplicate emission when log record propagates through hierarchy
        if getattr(record, '_structured_emitted', False):
            return
        log_entry = {
            'timestamp': self.format_time(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
        }

        # Add extra fields if present (using getattr with default to satisfy type checkers)
        for attr in ('request_id', 'user_id', 'route', 'status_code', 'duration_ms'):
            value = getattr(record, attr, None)
            if value is not None:
                log_entry[attr] = value

        # Mark BEFORE printing so downstream/root handlers suppress duplicates
        setattr(record, '_structured_emitted', True)
        print(json.dumps(log_entry))
    
    def format_time(self, record):
        """Format timestamp in ISO 8601"""
        from datetime import datetime
        dt = datetime.fromtimestamp(record.created)
        return dt.isoformat() + 'Z'


# PII patterns to mask in logs
PII_PATTERNS = [
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL]'),  # Email
    (re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'), '[PHONE]'),  # Phone
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[SSN]'),  # SSN
    (re.compile(r'"password"\s*:\s*"[^"]*"'), '"password":"[REDACTED]"'),  # Password in JSON
    (re.compile(r'Bearer\s+[A-Za-z0-9\-._~+/]+=*'), 'Bearer [TOKEN]'),  # JWT tokens
]


def mask_pii(text: str) -> str:
    """
    Mask PII in log messages
    
    Args:
        text: Original text that may contain PII
        
    Returns:
        Text with PII replaced with placeholders
    """
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured JSON logging of HTTP requests
    
    Logs include:
    - request_id: Unique request identifier
    - user_id: Authenticated user ID (if present)
    - route: Request path
    - method: HTTP method
    - status_code: Response status
    - duration_ms: Request processing time
    - user_agent: Client user agent (masked)
    
    PII is automatically masked in log output.
    """
    
    def __init__(self, app, logger: logging.Logger | None = None):
        super().__init__(app)
        self.logger = logger or logging.getLogger('resumerag.http')
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()
        
        # Get request context
        request_id = get_request_id()
        route = request.url.path
        method = request.method
        
        # Get user ID if authenticated (from request.state set by auth middleware)
        user_id = ""
        if hasattr(request.state, 'user_id') and request.state.user_id is not None:
            user_id = str(request.state.user_id)
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            error = None
        except Exception as e:
            # Log error and re-raise
            status_code = 500
            error = str(e)
            self.log_request(
                request_id=request_id,
                user_id=user_id,
                route=route,
                method=method,
                status_code=status_code,
                duration_ms=int((time.time() - start_time) * 1000),
                error=error
            )
            raise
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        duration_seconds = duration_ms / 1000.0
        
        # Track metrics
        track_http_request(method, route, status_code, duration_seconds)
        
        # Log request
        self.log_request(
            request_id=request_id,
            user_id=user_id,
            route=route,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            error=error
        )
        
        return response
    
    def log_request(
        self,
        request_id: str,
        user_id: str,
        route: str,
        method: str,
        status_code: int,
        duration_ms: int,
    error: str | None = None
    ):
        """Log request with structured data"""
        
        # Mask PII in route (query params may contain sensitive data)
        safe_route = mask_pii(route)
        
        # Determine log level based on status
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING
        else:
            level = logging.INFO
        
        # Create log message
        message = f"{method} {safe_route} {status_code} {duration_ms}ms"
        if error:
            message += f" - {mask_pii(error)}"
        
        # Log with extra fields
        self.logger.log(
            level,
            message,
            extra={
                'request_id': request_id,
                'user_id': user_id,
                'route': safe_route,
                'method': method,
                'status_code': status_code,
                'duration_ms': duration_ms,
            }
        )


def setup_structured_logging():
    """
    Configure application-wide structured logging
    
    Call this during app startup to initialize JSON logging.
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add structured JSON handler
    json_handler = StructuredLogger()
    json_handler.setLevel(logging.INFO)
    root_logger.addHandler(json_handler)
    
    # Set format for console during development (fallback)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    # Uncomment for development console output:
    # root_logger.addHandler(console_handler)
