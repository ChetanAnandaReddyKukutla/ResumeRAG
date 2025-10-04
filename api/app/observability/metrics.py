"""
Prometheus metrics for ResumeRAG API

Exports comprehensive metrics for monitoring:
- HTTP request metrics (rate, duration, errors)
- Business logic metrics (embeddings, searches, uploads)
- Queue metrics (pending, failed jobs)
- System metrics (active users, error rates)
"""
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from typing import Callable
import time
from functools import wraps

# Create custom registry (avoids conflicts with default)
registry = CollectorRegistry()

# ============================================================================
# HTTP Metrics
# ============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=registry
)

# ============================================================================
# Business Logic Metrics
# ============================================================================

embeddings_generation_total = Counter(
    'embeddings_generation_total',
    'Total embeddings generated',
    ['model'],
    registry=registry
)

embeddings_latency_seconds = Histogram(
    'embeddings_latency_seconds',
    'Embedding generation latency in seconds',
    ['model'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=registry
)

vector_search_total = Counter(
    'vector_search_total',
    'Total vector searches performed',
    registry=registry
)

vector_search_latency_seconds = Histogram(
    'vector_search_latency_seconds',
    'Vector search latency in seconds',
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry
)

resume_uploads_total = Counter(
    'resume_uploads_total',
    'Total resume uploads',
    ['status'],  # success, failed_validation, failed_malware, failed_processing
    registry=registry
)

resume_parse_errors_total = Counter(
    'resume_parse_errors_total',
    'Total resume parsing errors',
    registry=registry
)

job_matches_total = Counter(
    'job_matches_total',
    'Total job match operations',
    registry=registry
)

# ============================================================================
# Queue Metrics
# ============================================================================

queue_jobs_pending = Gauge(
    'queue_jobs_pending',
    'Number of pending jobs in queue',
    registry=registry
)

queue_jobs_failed = Gauge(
    'queue_jobs_failed',
    'Number of failed jobs in queue',
    registry=registry
)

queue_jobs_processing = Gauge(
    'queue_jobs_processing',
    'Number of jobs currently being processed',
    registry=registry
)

# ============================================================================
# System Metrics
# ============================================================================

active_users_total = Gauge(
    'active_users_total',
    'Number of active users (last 5 minutes)',
    registry=registry
)

errors_total = Counter(
    'errors_total',
    'Total errors by type',
    ['error_type'],  # validation, auth, rate_limit, internal
    registry=registry
)

# ============================================================================
# Metric Update Functions
# ============================================================================

def track_http_request(method: str, endpoint: str, status: int, duration: float):
    """
    Track HTTP request metrics
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Endpoint path (e.g., /api/resumes)
        status: HTTP status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def track_embedding_generation(model: str, duration: float):
    """
    Track embedding generation metrics
    
    Args:
        model: Model name (e.g., sentence-transformers/all-MiniLM-L6-v2)
        duration: Generation duration in seconds
    """
    embeddings_generation_total.labels(model=model).inc()
    embeddings_latency_seconds.labels(model=model).observe(duration)


def track_vector_search(duration: float):
    """
    Track vector search metrics
    
    Args:
        duration: Search duration in seconds
    """
    vector_search_total.inc()
    vector_search_latency_seconds.observe(duration)


def track_resume_upload(status: str):
    """
    Track resume upload metrics
    
    Args:
        status: Upload status (success, failed_validation, failed_malware, failed_processing)
    """
    resume_uploads_total.labels(status=status).inc()


def track_resume_parse_error():
    """Track resume parsing error"""
    resume_parse_errors_total.inc()


def track_job_match():
    """Track job match operation"""
    job_matches_total.inc()


def update_queue_metrics(pending: int, failed: int, processing: int):
    """
    Update queue metrics
    
    Args:
        pending: Number of pending jobs
        failed: Number of failed jobs
        processing: Number of jobs being processed
    """
    queue_jobs_pending.set(pending)
    queue_jobs_failed.set(failed)
    queue_jobs_processing.set(processing)


def update_active_users(count: int):
    """
    Update active users count
    
    Args:
        count: Number of active users
    """
    active_users_total.set(count)


def track_error(error_type: str):
    """
    Track error by type
    
    Args:
        error_type: Type of error (validation, auth, rate_limit, internal)
    """
    errors_total.labels(error_type=error_type).inc()


# ============================================================================
# Decorators for Easy Instrumentation
# ============================================================================

def track_time(metric_name: str):
    """
    Decorator to track execution time of a function
    
    Usage:
        @track_time('embeddings')
        async def generate_embeddings(text: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                
                # Route to appropriate metric
                if metric_name == 'embeddings':
                    # Extract model from kwargs if available
                    model = kwargs.get('model', 'default')
                    track_embedding_generation(model, duration)
                elif metric_name == 'vector_search':
                    track_vector_search(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                
                # Route to appropriate metric
                if metric_name == 'embeddings':
                    model = kwargs.get('model', 'default')
                    track_embedding_generation(model, duration)
                elif metric_name == 'vector_search':
                    track_vector_search(duration)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ============================================================================
# Metrics Export
# ============================================================================

def get_metrics() -> tuple[str, str]:
    """
    Get Prometheus metrics in text format
    
    Returns:
        Tuple of (metrics_data, content_type)
    """
    metrics_data = generate_latest(registry)
    return metrics_data, CONTENT_TYPE_LATEST
