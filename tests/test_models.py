import pytest
from pydantic import ValidationError

from cas_reference_product.models import PromptEnvelope


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
