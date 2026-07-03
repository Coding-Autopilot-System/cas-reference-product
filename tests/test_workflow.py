from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

import pytest

from cas_reference_product.workflow import WorkflowOrchestrator


class SuccessfulService:
    def run(self: "Any", envelope: "Any") -> str:
        return f"processed:{envelope.promptId}"


class FailingService:
    def run(self: "Any", envelope: "Any") -> str:
        raise RuntimeError("expected")


def test_orchestrator_returns_traceable_events(envelope: "Any") -> None:
    fixed = datetime(2026, 6, 11, 10, 0, tzinfo=UTC)
    # Patch current_traceparent so this unit test is provider-independent.
    with patch(
        "cas_reference_product.workflow.current_traceparent",
        side_effect=lambda fallback: fallback,
    ):
        result = WorkflowOrchestrator(
            SuccessfulService(), envelope.repo, clock=lambda: fixed
        ).execute(envelope)

    assert result.output == "processed:prompt-001"
    assert [event.eventType for event in result.events] == [
        "workflow.started",
        "workflow.completed",
    ]
    assert all(event.timestamp == fixed for event in result.events)
    assert all(event.traceContext == envelope.traceContext for event in result.events)


def test_orchestrator_propagates_failure(envelope: "Any") -> None:
    with pytest.raises(RuntimeError, match="expected"):
        WorkflowOrchestrator(FailingService(), envelope.repo).execute(envelope)
