"""Shared monitoring and observability utilities."""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace import config_integration
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from prometheus_client import Counter, Histogram, Gauge

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests',
    ['method', 'endpoint']
)

ERROR_COUNT = Counter(
    'errors_total',
    'Total errors',
    ['service', 'error_type']
)


class MonitoringConfig:
    """Configuration for monitoring and observability."""

    def __init__(
        self,
        service_name: str,
        app_insights_connection_string: Optional[str] = None,
        enable_prometheus: bool = True,
        enable_app_insights: bool = True,
        log_level: str = "INFO",
    ):
        """
        Initialize monitoring configuration.

        Args:
            service_name: Name of the service
            app_insights_connection_string: Azure Application Insights connection string
            enable_prometheus: Enable Prometheus metrics
            enable_app_insights: Enable Application Insights
            log_level: Logging level
        """
        self.service_name = service_name
        self.app_insights_connection_string = app_insights_connection_string
        self.enable_prometheus = enable_prometheus
        self.enable_app_insights = enable_app_insights
        self.log_level = log_level

    def setup_logging(self) -> logging.Logger:
        """
        Set up logging with Application Insights integration.

        Returns:
            Configured logger
        """
        logger = logging.getLogger(self.service_name)
        logger.setLevel(self.log_level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Application Insights handler
        if self.enable_app_insights and self.app_insights_connection_string:
            ai_handler = AzureLogHandler(
                connection_string=self.app_insights_connection_string
            )
            ai_handler.setLevel(self.log_level)
            logger.addHandler(ai_handler)

        return logger

    def setup_tracing(self) -> Tracer:
        """
        Set up distributed tracing with Application Insights.

        Returns:
            Configured tracer
        """
        if self.enable_app_insights and self.app_insights_connection_string:
            # Configure integrations
            config_integration.trace_integrations(['requests', 'httplib'])

            # Create tracer
            tracer = Tracer(
                exporter=AzureExporter(
                    connection_string=self.app_insights_connection_string
                ),
                sampler=ProbabilitySampler(1.0),  # Sample all requests
            )
            return tracer
        return None


def track_request(
    method: str,
    endpoint: str,
) -> Callable:
    """
    Decorator to track HTTP requests with Prometheus metrics.

    Args:
        method: HTTP method
        endpoint: Endpoint path

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Increment active requests
            ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).inc()

            # Track request duration
            start_time = time.time()

            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Get status code from result
                status = getattr(result, 'status_code', 200)

                # Record metrics
                REQUEST_COUNT.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()

                return result

            except Exception as e:
                # Record error
                REQUEST_COUNT.labels(
                    method=method,
                    endpoint=endpoint,
                    status=500
                ).inc()

                ERROR_COUNT.labels(
                    service=endpoint,
                    error_type=type(e).__name__
                ).inc()

                raise

            finally:
                # Record duration
                duration = time.time() - start_time
                REQUEST_DURATION.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)

                # Decrement active requests
                ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).dec()

        return wrapper
    return decorator

