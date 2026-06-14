from collections.abc import Awaitable, Callable

from opentelemetry import context, propagate, trace
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .config import Settings
from .identity import build_credential

tracer = trace.get_tracer(__name__)


# ---------------------------------------------------------------------------
# W3C trace-context propagation middleware
# ---------------------------------------------------------------------------


class W3CTraceContextMiddleware(BaseHTTPMiddleware):
    """Extract W3C traceparent/tracestate headers from every inbound request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        ctx = propagate.extract(dict(request.headers))
        token = context.attach(ctx)
        try:
            return await call_next(request)
        finally:
            context.detach(token)


def install_propagator() -> None:
    """Set the global propagator to W3C TraceContext (traceparent / tracestate)."""
    propagate.set_global_textmap(
        CompositePropagator([TraceContextTextMapPropagator()])
    )


# ---------------------------------------------------------------------------
# Application Insights exporter
# ---------------------------------------------------------------------------


def configure_telemetry(settings: Settings) -> None:
    install_propagator()

    if settings.applicationinsights_connection_string:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            connection_string=settings.applicationinsights_connection_string,
            credential=build_credential(settings.environment),
            disable_offline_storage=True,
            instrumentation_options={
                "azure_sdk": {"enabled": False},
                "requests": {"enabled": False},
                "urllib": {"enabled": False},
                "urllib3": {"enabled": False},
            },
            service_name=settings.app_name,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def current_traceparent(fallback: str) -> str:
    context = trace.get_current_span().get_span_context()
    if context.is_valid:
        return f"00-{context.trace_id:032x}-{context.span_id:016x}-01"
    return fallback
