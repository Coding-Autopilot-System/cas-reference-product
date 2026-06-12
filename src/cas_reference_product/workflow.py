from collections.abc import Callable
from datetime import UTC, datetime
from typing import Literal, Protocol

from azure.ai.projects import AIProjectClient
from opentelemetry import trace

from .config import Settings
from .identity import build_credential
from .models import Actor, PromptEnvelope, RunEvent, TraceContext, WorkflowResult
from .telemetry import current_traceparent

tracer = trace.get_tracer(__name__)
RunStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]


class WorkflowAgentService(Protocol):
    """Application boundary implemented by local and Foundry Next Gen workflows."""

    def run(self, envelope: PromptEnvelope) -> str: ...


class WorkflowAgentServiceError(RuntimeError):
    """Stable application error raised when an external workflow backend fails."""


class LocalWorkflowAgentService:
    def run(self, envelope: PromptEnvelope) -> str:
        return (
            f"Reference workflow accepted '{envelope.intent}' "
            f"with {len(envelope.constraints)} constraints."
        )


class FoundryWorkflowAgentService:
    """Invoke a Foundry Next Gen agent reference through the project Responses client."""

    def __init__(self, settings: Settings) -> None:
        endpoint = settings.foundry_project_endpoint
        agent_name = settings.foundry_agent_name
        if not settings.foundry_ready or endpoint is None or agent_name is None:
            raise ValueError("Foundry backend requires a valid project endpoint and agent name")
        self._agent_name = agent_name
        self._client = AIProjectClient(
            endpoint=endpoint,
            credential=build_credential(settings.environment),
        ).get_openai_client()

    def run(self, envelope: PromptEnvelope) -> str:
        with tracer.start_as_current_span("foundry.responses.create"):
            try:
                response = self._client.responses.create(
                    input=envelope.prompt,
                    extra_body={
                        "agent_reference": {
                            "name": self._agent_name,
                            "type": "agent_reference",
                        }
                    },
                )
            except Exception:
                raise WorkflowAgentServiceError("Foundry workflow invocation failed") from None
        return response.output_text


def build_workflow_agent_service(settings: Settings) -> WorkflowAgentService:
    if settings.workflow_backend == "foundry":
        return FoundryWorkflowAgentService(settings)
    return LocalWorkflowAgentService()


class WorkflowOrchestrator:
    def __init__(
        self,
        service: WorkflowAgentService,
        repository: str,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._service = service
        self._repository = repository
        self._clock = clock

    def execute(self, envelope: PromptEnvelope) -> WorkflowResult:
        with tracer.start_as_current_span("cas.workflow.execute") as span:
            span.set_attribute("cas.correlation_id", envelope.correlationId)
            events = [self._event(envelope, 0, "workflow.started", "running", "Workflow started.")]
            try:
                output = self._service.run(envelope)
                events.append(
                    self._event(
                        envelope, 1, "workflow.completed", "succeeded", "Workflow completed."
                    )
                )
                return WorkflowResult(runId=envelope.runId, output=output, events=events)
            except Exception:
                events.append(
                    self._event(envelope, 1, "workflow.failed", "failed", "Workflow failed.")
                )
                raise

    def _event(
        self,
        envelope: PromptEnvelope,
        sequence: int,
        event_type: str,
        status: RunStatus,
        message: str,
    ) -> RunEvent:
        trace_context = {"traceparent": current_traceparent(envelope.traceContext.traceparent)}
        if envelope.traceContext.tracestate is not None:
            trace_context["tracestate"] = envelope.traceContext.tracestate
        return RunEvent(
            correlationId=envelope.correlationId,
            promptId=envelope.promptId,
            runId=envelope.runId,
            repo=self._repository,
            actor=Actor(id="cas-reference-workflow", type="workflow"),
            timestamp=self._clock(),
            traceContext=TraceContext.model_validate(trace_context),
            eventType=event_type,
            sequence=sequence,
            status=status,
            message=message,
        )
