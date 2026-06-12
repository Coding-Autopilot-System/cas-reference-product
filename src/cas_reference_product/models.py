from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def reject_explicit_null(data: Any, fields: tuple[str, ...]) -> Any:
    if isinstance(data, dict):
        null_fields = [field for field in fields if field in data and data[field] is None]
        if null_fields:
            raise ValueError(f"{', '.join(null_fields)} must be omitted instead of null")
    return data


class Actor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=256)
    type: Literal["human", "agent", "service", "workflow"]
    displayName: str | None = Field(
        default=None, min_length=1, max_length=256, exclude_if=lambda value: value is None
    )

    @model_validator(mode="before")
    @classmethod
    def reject_null_display_name(cls, data: Any) -> Any:
        return reject_explicit_null(data, ("displayName",))


class TraceContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    traceparent: str = Field(pattern=r"^[\da-f]{2}-[\da-f]{32}-[\da-f]{16}-[\da-f]{2}$")
    tracestate: str | None = Field(
        default=None, max_length=512, exclude_if=lambda value: value is None
    )

    @model_validator(mode="before")
    @classmethod
    def reject_null_tracestate(cls, data: Any) -> Any:
        return reject_explicit_null(data, ("tracestate",))


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
    constraints: list[Annotated[str, Field(min_length=1, max_length=1_000)]] = Field(
        default_factory=list
    )

    @field_validator("constraints")
    @classmethod
    def constraints_must_be_unique(cls, constraints: list[str]) -> list[str]:
        if len(constraints) != len(set(constraints)):
            raise ValueError("constraints must contain unique values")
        return constraints


class RunEvent(LifecycleMetadata):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["RunEvent"] = "RunEvent"
    eventType: str = Field(min_length=1, max_length=128)
    sequence: int = Field(ge=0)
    status: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    message: str | None = Field(
        default=None, max_length=5_000, exclude_if=lambda value: value is None
    )

    @model_validator(mode="before")
    @classmethod
    def reject_null_message(cls, data: Any) -> Any:
        return reject_explicit_null(data, ("message",))


class WorkflowResult(BaseModel):
    runId: str
    output: str
    events: list[RunEvent]
