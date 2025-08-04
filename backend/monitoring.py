"""
Monitoring setup for the Agentic Stack MVP
Configures OpenTelemetry and Logfire for observability
"""

import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

logger = logging.getLogger(__name__)


def setup_monitoring():
    """
    Setup comprehensive monitoring with OpenTelemetry and Logfire
    """
    try:
        # Setup OpenTelemetry tracing
        setup_opentelemetry()
        
        # Setup Logfire if token is available
        logfire_token = os.getenv("LOGFIRE_TOKEN")
        if logfire_token:
            setup_logfire(logfire_token)
        
        logger.info("Monitoring setup complete")
        
    except Exception as e:
        logger.warning(f"Could not setup monitoring: {e}")


def setup_opentelemetry():
    """
    Configure OpenTelemetry tracing
    """
    # Create tracer provider
    provider = TracerProvider()
    
    # Configure OTLP exporter (e.g., to Jaeger or another backend)
    otlp_endpoint = os.getenv("OTLP_ENDPOINT", "localhost:4317")
    
    try:
        exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=True  # Use insecure for local development
        )
        
        # Add batch processor for efficient export
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        
        # Set the tracer provider
        trace.set_tracer_provider(provider)
        
        # Auto-instrument libraries
        FastAPIInstrumentor.instrument()
        HTTPXClientInstrumentor.instrument()
        RedisInstrumentor.instrument()
        
        logger.info(f"OpenTelemetry configured with endpoint: {otlp_endpoint}")
        
    except Exception as e:
        logger.warning(f"Could not configure OpenTelemetry: {e}")


def setup_logfire(token: str):
    """
    Configure Logfire for PydanticAI observability
    """
    try:
        import logfire
        
        # Configure Logfire
        logfire.configure(
            token=token,
            service_name="agentic-stack-mvp",
            environment=os.getenv("ENV", "development")
        )
        
        # Instrument PydanticAI
        logfire.instrument_pydantic_ai()
        
        # Instrument other libraries
        logfire.instrument_fastapi()
        logfire.instrument_httpx()
        
        logger.info("Logfire configured successfully")
        
    except ImportError:
        logger.warning("Logfire not installed, skipping Logfire setup")
    except Exception as e:
        logger.warning(f"Could not configure Logfire: {e}")


def get_tracer(name: str):
    """
    Get a tracer for manual instrumentation
    
    Args:
        name: Name of the component requesting the tracer
    
    Returns:
        OpenTelemetry tracer instance
    """
    return trace.get_tracer(name)