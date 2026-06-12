import pytest
from pydantic import ValidationError

from cas_reference_product.models import Actor, PromptEnvelope, RunEvent, TraceContext


def test_prompt_envelope_rejects_extra_properties(envelope) -> None:
    payload = envelope.model_dump()
    payload["secret"] = "not-allowed"

    with pytest.raises(ValidationError):
        PromptEnvelope.model_validate(payload)


def test_prompt_envelope_matches_cas_contract_metadata(envelope) -> None:
    payload = envelope.model_dump(mode="json")

    assert payload["kind"] == "PromptEnvelope"
    assert payload["schemaVersion"] == "0.1.0"
    assert payload["traceContext"]["traceparent"].startswith("00-")


@pytest.mark.parametrize(
    "constraints",
    [
        [""],
        ["x" * 1_001],
        ["No secrets", "No secrets"],
    ],
)
def test_prompt_envelope_enforces_cas_contract_constraints(envelope, constraints) -> None:
    payload = envelope.model_dump()
    payload["constraints"] = constraints

    with pytest.raises(ValidationError):
        PromptEnvelope.model_validate(payload)


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (Actor, {"id": "developer", "type": "human", "displayName": None}),
        (
            TraceContext,
            {
                "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
                "tracestate": None,
            },
        ),
        (
            RunEvent,
            {
                "correlationId": "corr-001",
                "promptId": "prompt-001",
                "runId": "run-001",
                "repo": "Coding-Autopilot-System/cas-reference-product",
                "actor": {"id": "workflow", "type": "workflow"},
                "timestamp": "2026-06-11T00:00:00Z",
                "traceContext": {
                    "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
                },
                "eventType": "workflow.started",
                "sequence": 0,
                "status": "running",
                "message": None,
            },
        ),
    ],
)
def test_contract_models_reject_explicit_null_optional_fields(model, payload) -> None:
    with pytest.raises(ValidationError):
        model.model_validate(payload)
