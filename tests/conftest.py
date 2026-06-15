from datetime import UTC, datetime

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from cas_reference_product.models import Actor, PromptEnvelope, TraceContext


@pytest.fixture(scope="session")
def session_otel_exporter() -> InMemorySpanExporter:
    """Set the global OTel provider once for the entire test session."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return exporter


@pytest.fixture()
def in_memory_exporter(session_otel_exporter: InMemorySpanExporter) -> InMemorySpanExporter:
    """Return the shared exporter, cleared for this test."""
    session_otel_exporter.clear()
    return session_otel_exporter


@pytest.fixture
def envelope() -> PromptEnvelope:
    return PromptEnvelope(
        correlationId="corr-001",
        promptId="prompt-001",
        runId="run-001",
        repo="Coding-Autopilot-System/cas-reference-product",
        actor=Actor(id="developer", type="human"),
        timestamp=datetime(2026, 6, 11, tzinfo=UTC),
        traceContext=TraceContext(
            traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        ),
        intent="Explain the reference workflow",
        prompt="Explain how this reference product works.",
        constraints=["No secrets"],
    )

