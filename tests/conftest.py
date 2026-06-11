from datetime import UTC, datetime

import pytest

from cas_reference_product.models import Actor, PromptEnvelope, TraceContext


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

