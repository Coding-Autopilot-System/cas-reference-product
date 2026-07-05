from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from opentelemetry import trace

from .config import Settings, get_settings
from .models import PromptEnvelope, WorkflowResult
from .telemetry import W3CTraceContextMiddleware, configure_telemetry
from .workflow import WorkflowAgentServiceError, WorkflowOrchestrator, build_workflow_agent_service

_tracer = trace.get_tracer(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        configure_telemetry(app_settings)
        yield

    app = FastAPI(title="CAS Reference Product", version="0.1.0", lifespan=lifespan)
    app.add_middleware(W3CTraceContextMiddleware)

    service = build_workflow_agent_service(app_settings) if app_settings.ready else None

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready")
    def ready() -> dict[str, str]:
        if not app_settings.ready:
            raise HTTPException(status_code=503, detail="Foundry configuration is incomplete")
        return {"status": "ready", "backend": app_settings.workflow_backend}

    @app.post("/api/v1/workflows", response_model=WorkflowResult)
    def execute(envelope: PromptEnvelope, request: Request) -> WorkflowResult:
        if service is None:
            raise HTTPException(status_code=503, detail="Workflow backend is not ready")
        request.state.correlation_id = envelope.correlationId
        with _tracer.start_as_current_span("cas.api.workflows.execute") as span:
            span.set_attribute("cas.correlation_id", envelope.correlationId)
            span.set_attribute("cas.run_id", envelope.runId)
            span.set_attribute("cas.intent", envelope.intent)
            span.add_event(
                "workflow.started",
                attributes={
                    "cas.correlation_id": envelope.correlationId,
                    "cas.run_id": envelope.runId,
                },
            )
            orchestrator = WorkflowOrchestrator(service, app_settings.repository)
            try:
                result = orchestrator.execute(envelope)
            except WorkflowAgentServiceError:
                span.add_event(
                    "workflow.failed",
                    attributes={
                        "cas.correlation_id": envelope.correlationId,
                        "cas.run_id": envelope.runId,
                        "error": True,
                    },
                )
                raise HTTPException(
                    status_code=502, detail="Workflow backend request failed"
                ) from None
            span.add_event(
                "workflow.completed",
                attributes={
                    "cas.correlation_id": envelope.correlationId,
                    "cas.run_id": envelope.runId,
                },
            )
            return result

    @app.get("/")
    def root() -> dict[str, Any]:
        return {
            "name": app_settings.app_name,
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health/ready",
        }

    return app


app = create_app()
