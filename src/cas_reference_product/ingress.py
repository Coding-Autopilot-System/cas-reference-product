import json

from pydantic import ValidationError

from .models import PromptEnvelope


class InvalidIngressRequest(ValueError):
    """The ingress payload does not satisfy the canonical prompt envelope."""


def create_worker_message(payload: bytes) -> str:
    try:
        envelope = PromptEnvelope.model_validate_json(payload)
    except (ValidationError, ValueError) as error:
        raise InvalidIngressRequest("invalid CAS prompt envelope") from error

    return json.dumps(envelope.model_dump(mode="json"), separators=(",", ":"))
