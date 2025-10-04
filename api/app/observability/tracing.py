"""
OpenTelemetry distributed tracing for ResumeRAG

Provides tracing instrumentation for key operations:
- HTTP requests (automatic)
- Resume upload and parsing
- Embedding generation
- Vector search
- Job matching
- Worker jobs

Exports traces to OTLP collector or console.
"""
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.trace import Status, StatusCode
from typing import Callable, Optional
from functools import wraps
import asyncio

from app.middleware.request_id import get_request_id


# Global tracer
tracer: Optional[trace.Tracer] = None


def setup_tracing(app, service_name: str = "resumerag-api"):
    """
    Setup OpenTelemetry tracing for the application
    
    Args:
        app: FastAPI application instance
        service_name: Name of the service for tracing
    """
    global tracer
    
    # Skip tracing in explicit test mode or when disabled
    if os.getenv("TESTING") == "1" or os.getenv("OTEL_SDK_DISABLED") == "1":
        return None

    # Create resource with service name
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Configure exporter based on environment
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    
    if otlp_endpoint:
        # Export to OTLP collector (production)
        exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() == "true"
        )
    else:
        # Export to console (development)
        exporter = ConsoleSpanExporter()
    
    # Add span processor
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    
    # Set global tracer provider
    trace.set_tracer_provider(provider)
    
    # Get tracer
    tracer = trace.get_tracer(__name__)
    
    # Instrument FastAPI automatically
    FastAPIInstrumentor.instrument_app(app)
    
    return tracer


def get_tracer() -> Optional[trace.Tracer]:
    """Get the global tracer instance"""
    return tracer


def add_request_context_to_span(span: trace.Span, user_id: Optional[str] = None):
    """
    Add request context to span attributes
    
    Args:
        span: Span to add attributes to
        user_id: User ID if authenticated
    """
    request_id = get_request_id()
    
    if request_id:
        span.set_attribute("request.id", request_id)
    
    if user_id:
        span.set_attribute("user.id", user_id)


def trace_operation(operation_name: str, **attributes):
    """
    Decorator to trace an operation with a custom span
    
    Usage:
        @trace_operation("resume.parse", file_type="pdf")
        async def parse_resume(file_path: str):
            ...
    
    Args:
        operation_name: Name of the operation for the span
        **attributes: Additional attributes to add to the span
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if tracer is None:
                # Tracing not enabled, just call function
                return await func(*args, **kwargs)
            
            with tracer.start_as_current_span(operation_name) as span:
                # Add custom attributes
                for key, value in attributes.items():
                    span.set_attribute(key, value)
                
                # Add request context
                add_request_context_to_span(span)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if tracer is None:
                # Tracing not enabled, just call function
                return func(*args, **kwargs)
            
            with tracer.start_as_current_span(operation_name) as span:
                # Add custom attributes
                for key, value in attributes.items():
                    span.set_attribute(key, value)
                
                # Add request context
                add_request_context_to_span(span)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def create_span(operation_name: str, **attributes):
    """
    Manually create a span (context manager)
    
    Usage:
        with create_span("embedding.generate", model="hash-sha256"):
            # Do work
            pass
    
    Args:
        operation_name: Name of the operation for the span
        **attributes: Additional attributes to add to the span
    """
    if tracer is None:
        # Return a no-op context manager
        class NoOpSpan:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def set_attribute(self, key, value):
                pass
            def set_status(self, status):
                pass
        
        return NoOpSpan()
    
    span = tracer.start_as_current_span(operation_name)
    
    # Add custom attributes
    for key, value in attributes.items():
        span.__enter__().set_attribute(key, value)
    
    # Add request context
    add_request_context_to_span(span.__enter__())
    
    return span


# Convenience functions for common operations

def trace_resume_upload(resume_id: str, filename: str, user_id: Optional[str] = None):
    """Start a span for resume upload operation"""
    if tracer is None:
        class NoOpSpan:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return NoOpSpan()
    
    span = tracer.start_as_current_span("resume.upload")
    span.__enter__().set_attribute("resume.id", resume_id)
    span.__enter__().set_attribute("resume.filename", filename)
    
    if user_id:
        span.__enter__().set_attribute("user.id", user_id)
    
    add_request_context_to_span(span.__enter__())
    
    return span


def trace_embedding_generation(text_length: int, model: str = "hash-sha256"):
    """Start a span for embedding generation"""
    if tracer is None:
        class NoOpSpan:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return NoOpSpan()
    
    span = tracer.start_as_current_span("embedding.generate")
    span.__enter__().set_attribute("embedding.model", model)
    span.__enter__().set_attribute("embedding.text_length", text_length)
    
    add_request_context_to_span(span.__enter__())
    
    return span


def trace_vector_search(query_length: int, limit: int = 20):
    """Start a span for vector search"""
    if tracer is None:
        class NoOpSpan:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return NoOpSpan()
    
    span = tracer.start_as_current_span("vector.search")
    span.__enter__().set_attribute("search.query_length", query_length)
    span.__enter__().set_attribute("search.limit", limit)
    
    add_request_context_to_span(span.__enter__())
    
    return span


def trace_job_match(job_id: str, top_n: int):
    """Start a span for job matching"""
    if tracer is None:
        class NoOpSpan:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return NoOpSpan()
    
    span = tracer.start_as_current_span("job.match")
    span.__enter__().set_attribute("job.id", job_id)
    span.__enter__().set_attribute("job.top_n", top_n)
    
    add_request_context_to_span(span.__enter__())
    
    return span
