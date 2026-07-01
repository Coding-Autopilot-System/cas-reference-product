"""Tests for Phase 2 — Telemetry Hardening (TEL-01 through TEL-04)."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from cas_reference_product import telemetry
from cas_reference_product.app import create_app
from cas_reference_product.config import Settings
from cas_reference_product.telemetry import (
    LoopStage,
    configure_telemetry,
    current_traceparent,
    install_propagator,
)


# ---------------------------------------------------------------------------
# TEL-04: Application Insights exporter — no-op when connection string absent
# ---------------------------------------------------------------------------


def test_telemetry_is_noop_without_application_insights() -> None:
    with patch("cas_reference_product.telemetry.build_credential") as credential:
        configure_telemetry(Settings())
    credential.assert_not_called()


# ---------------------------------------------------------------------------
# TEL-04: Application Insights exporter — active when connection string present
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# current_traceparent helper
# ---------------------------------------------------------------------------


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


def test_all_loop_stages_share_one_trace_without_prompt_or_output_attributes() -> None:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    with patch.object(telemetry, "tracer", provider.get_tracer("test")):
        with telemetry.start_loop_span(LoopStage.CONTROL_PLANE, "corr-1", goal_id="goal-1"):
            for stage in (
                LoopStage.WORKER,
                LoopStage.TOOL,
                LoopStage.VERIFIER,
                LoopStage.FOUNDRY,
            ):
                with telemetry.start_loop_span(stage, "corr-1", work_item_id="work-1"):
                    pass

    spans = exporter.get_finished_spans()
    assert {span.attributes["cas.stage"] for span in spans} == {stage.value for stage in LoopStage}
    assert len({span.context.trace_id for span in spans}) == 1
    assert all(
        "prompt" not in key and "output" not in key
        for span in spans
        for key in span.attributes
    )


# ---------------------------------------------------------------------------
# TEL-03: W3C propagator installed
# ---------------------------------------------------------------------------


def test_install_propagator_sets_w3c_propagator() -> None:
    install_propagator()
    from opentelemetry import propagate

    carrier: dict[str, str] = {}
    propagate.inject(carrier)
    global_propagator = propagate.get_global_textmap()
    propagator_repr = repr(global_propagator)
    assert "TraceContext" in propagator_repr or "Composite" in propagator_repr


# ---------------------------------------------------------------------------
# TEL-01: span created for every /api/v1/workflows request
# ---------------------------------------------------------------------------


def test_workflow_endpoint_creates_span(in_memory_exporter: InMemorySpanExporter, envelope) -> None:
    client = TestClient(create_app(Settings()))
    response = client.post("/api/v1/workflows", json=envelope.model_dump(mode="json"))

    assert response.status_code == 200
    spans = in_memory_exporter.get_finished_spans()
    span_names = [s.name for s in spans]
    assert "cas.api.workflows.execute" in span_names, (
        f"Expected 'cas.api.workflows.execute' in spans, got: {span_names}"
    )


# ---------------------------------------------------------------------------
# TEL-01 + TEL-02: workflow span carries correlation/run attributes
# ---------------------------------------------------------------------------


def test_workflow_span_attributes(in_memory_exporter: InMemorySpanExporter, envelope) -> None:
    client = TestClient(create_app(Settings()))
    client.post("/api/v1/workflows", json=envelope.model_dump(mode="json"))

    spans = in_memory_exporter.get_finished_spans()
    api_span = next(s for s in spans if s.name == "cas.api.workflows.execute")
    assert api_span.attributes.get("cas.correlation_id") == envelope.correlationId
    assert api_span.attributes.get("cas.run_id") == envelope.runId
    assert api_span.attributes.get("cas.intent") == envelope.intent


# ---------------------------------------------------------------------------
# TEL-02: canonical lifecycle events emitted as span events
# ---------------------------------------------------------------------------


def test_workflow_span_events_started_and_completed(
    in_memory_exporter: InMemorySpanExporter, envelope
) -> None:
    client = TestClient(create_app(Settings()))
    client.post("/api/v1/workflows", json=envelope.model_dump(mode="json"))

    spans = in_memory_exporter.get_finished_spans()
    api_span = next(s for s in spans if s.name == "cas.api.workflows.execute")
    event_names = [e.name for e in api_span.events]
    assert "workflow.started" in event_names
    assert "workflow.completed" in event_names
    assert "workflow.failed" not in event_names


def test_workflow_span_events_started_and_failed(
    in_memory_exporter: InMemorySpanExporter, envelope
) -> None:
    from cas_reference_product.workflow import WorkflowAgentServiceError

    class FailingService:
        def run(self, _env) -> str:
            raise WorkflowAgentServiceError("backend down")

    with patch(
        "cas_reference_product.app.build_workflow_agent_service",
        return_value=FailingService(),
    ):
        client = TestClient(create_app(Settings()))
        response = client.post("/api/v1/workflows", json=envelope.model_dump(mode="json"))

    assert response.status_code == 502
    spans = in_memory_exporter.get_finished_spans()
    api_span = next(s for s in spans if s.name == "cas.api.workflows.execute")
    event_names = [e.name for e in api_span.events]
    assert "workflow.started" in event_names
    assert "workflow.failed" in event_names
    assert "workflow.completed" not in event_names


def test_span_event_carries_correlation_id(
    in_memory_exporter: InMemorySpanExporter, envelope
) -> None:
    client = TestClient(create_app(Settings()))
    client.post("/api/v1/workflows", json=envelope.model_dump(mode="json"))

    spans = in_memory_exporter.get_finished_spans()
    api_span = next(s for s in spans if s.name == "cas.api.workflows.execute")
    started_event = next(e for e in api_span.events if e.name == "workflow.started")
    assert started_event.attributes.get("cas.correlation_id") == envelope.correlationId
    assert started_event.attributes.get("cas.run_id") == envelope.runId


# ---------------------------------------------------------------------------
# TEL-03: W3C traceparent propagated inbound — downstream span is child
# ---------------------------------------------------------------------------


def test_w3c_traceparent_propagated_inbound(
    in_memory_exporter: InMemorySpanExporter, envelope
) -> None:
    """Request with a W3C traceparent header links the API span as a child."""
    incoming_traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    install_propagator()

    client = TestClient(create_app(Settings()))
    response = client.post(
        "/api/v1/workflows",
        json=envelope.model_dump(mode="json"),
        headers={"traceparent": incoming_traceparent},
    )

    assert response.status_code == 200
    spans = in_memory_exporter.get_finished_spans()
    api_span = next((s for s in spans if s.name == "cas.api.workflows.execute"), None)
    assert api_span is not None

    expected_trace_id = int("4bf92f3577b34da6a3ce929d0e0e4736", 16)
    assert api_span.context.trace_id == expected_trace_id, (
        f"Expected trace_id {expected_trace_id:#x}, "
        f"got {api_span.context.trace_id:#x}"
    )
