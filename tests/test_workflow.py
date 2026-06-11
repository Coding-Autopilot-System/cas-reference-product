from datetime import UTC, datetime

import pytest

from cas_reference_product.workflow import WorkflowOrchestrator


class SuccessfulService:
    def run(self, envelope) -> str:
        return f"processed:{envelope.promptId}"


class FailingService:
    def run(self, envelope) -> str:
        raise RuntimeError("expected")


def test_orchestrator_returns_traceable_events(envelope) -> None:
    fixed = datetime(2026, 6, 11, 10, 0, tzinfo=UTC)
    result = WorkflowOrchestrator(
        SuccessfulService(), envelope.repo, clock=lambda: fixed
    ).execute(envelope)

    assert result.output == "processed:prompt-001"
    assert [event.eventType for event in result.events] == [
        "workflow.started",
        "workflow.completed",
    ]
    assert all(event.timestamp == fixed for event in result.events)


def test_orchestrator_propagates_failure(envelope) -> None:
    with pytest.raises(RuntimeError, match="expected"):
        WorkflowOrchestrator(FailingService(), envelope.repo).execute(envelope)

