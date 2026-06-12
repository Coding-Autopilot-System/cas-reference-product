from unittest.mock import MagicMock, patch

from cas_reference_product.config import Settings
from cas_reference_product.telemetry import configure_telemetry, current_traceparent


def test_telemetry_is_noop_without_application_insights() -> None:
    configure_telemetry(Settings())


def test_invalid_span_preserves_incoming_traceparent() -> None:
    incoming = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    with patch("cas_reference_product.telemetry.trace.get_current_span") as current:
        span = MagicMock()
        span.get_span_context.return_value.is_valid = False
        current.return_value = span

        value = current_traceparent(incoming)

    assert value == incoming
