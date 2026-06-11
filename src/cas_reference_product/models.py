from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Actor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=256)
    type: Literal["human", "agent", "service", "workflow"]
    displayName: str | None = Field(default=None, min_length=1, max_length=256)


class TraceContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    traceparent: str = Field(pattern=r"^[\da-f]{2}-[\da-f]{32}-[\da-f]{16}-[\da-f]{2}$")
    tracestate: str | None = Field(default=None, max_length=512)


class LifecycleMetadata(BaseModel):
    correlationId: str = Field(min_length=1, max_length=128)
    promptId: str = Field(min_length=1, max_length=128)
    runId: str = Field(min_length=1, max_length=128)
    repo: str = Field(pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
    actor: Actor
    timestamp: datetime
    schemaVersion: Literal["0.1.0"] = "0.1.0"
    traceContext: TraceContext


class PromptEnvelope(LifecycleMetadata):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["PromptEnvelope"] = "PromptEnvelope"
    intent: str = Field(min_length=1, max_length=256)
    prompt: str = Field(min_length=1, max_length=50_000)
    constraints: list[str] = Field(default_factory=list)


class RunEvent(LifecycleMetadata):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["RunEvent"] = "RunEvent"
    eventType: str = Field(min_length=1, max_length=128)
    sequence: int = Field(ge=0)
    status: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    message: str | None = Field(default=None, max_length=5_000)


class WorkflowResult(BaseModel):
    runId: str
    output: str
    events: list[RunEvent]

