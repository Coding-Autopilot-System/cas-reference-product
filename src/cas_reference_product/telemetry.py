from opentelemetry import trace

from .config import Settings


def configure_telemetry(settings: Settings) -> None:
    if settings.applicationinsights_connection_string:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            connection_string=settings.applicationinsights_connection_string,
            service_name=settings.app_name,
        )


def current_traceparent(fallback: str) -> str:
    context = trace.get_current_span().get_span_context()
    if context.is_valid:
        return f"00-{context.trace_id:032x}-{context.span_id:016x}-01"
    return fallback
