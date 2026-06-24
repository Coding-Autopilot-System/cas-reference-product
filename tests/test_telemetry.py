from unittest.mock import MagicMock, patch

from cas_reference_product.config import Settings
from cas_reference_product.telemetry import configure_telemetry, current_traceparent


def test_telemetry_is_noop_without_application_insights() -> None:
    with patch("cas_reference_product.telemetry.build_credential") as credential:
        configure_telemetry(Settings())
    credential.assert_not_called()


def test_telemetry_uses_identity_and_privacy_hardening() -> None:
    settings = Settings(
        environment="prod",
        applicationinsights_connection_string=(
            "InstrumentationKey=00000000-0000-0000-0000-000000000000"
        ),
    )
    with (
        patch("cas_reference_product.telemetry.build_credential") as credential,
        patch("azure.monitor.opentelemetry.configure_azure_monitor") as configure,
    ):
        configure_telemetry(settings)

    credential.assert_called_once_with("prod")
    configure.assert_called_once_with(
        connection_string=settings.applicationinsights_connection_string,
        credential=credential.return_value,
        disable_offline_storage=True,
        instrumentation_options={
            "azure_sdk": {"enabled": False},
            "requests": {"enabled": False},
            "urllib": {"enabled": False},
            "urllib3": {"enabled": False},
        },
        service_name=settings.app_name,
    )


def test_invalid_span_preserves_incoming_traceparent() -> None:
    incoming = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    with patch("cas_reference_product.telemetry.trace.get_current_span") as current:
        span = MagicMock()
        span.get_span_context.return_value.is_valid = False
        current.return_value = span

        value = current_traceparent(incoming)

    assert value == incoming


def test_valid_span_returns_formatted_traceparent() -> None:
    with patch("cas_reference_product.telemetry.trace.get_current_span") as current:
        span = MagicMock()
        ctx = MagicMock()
        ctx.is_valid = True
        ctx.trace_id = 0x4BF92F3577B34DA6A3CE929D0E0E4736
        ctx.span_id = 0x00F067AA0BA902B7
        span.get_span_context.return_value = ctx
        current.return_value = span

        value = current_traceparent("fallback")

    assert value == "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
