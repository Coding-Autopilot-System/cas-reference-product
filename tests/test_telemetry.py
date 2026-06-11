from unittest.mock import MagicMock, patch

from cas_reference_product.config import Settings
from cas_reference_product.telemetry import configure_telemetry, current_traceparent


def test_telemetry_is_noop_without_application_insights() -> None:
    configure_telemetry(Settings())


def test_invalid_span_produces_valid_unsampled_traceparent() -> None:
    with patch("cas_reference_product.telemetry.trace.get_current_span") as current:
        span = MagicMock()
        span.get_span_context.return_value.is_valid = False
        current.return_value = span

        value = current_traceparent()

    assert value == "00-00000000000000000000000000000001-0000000000000001-00"
