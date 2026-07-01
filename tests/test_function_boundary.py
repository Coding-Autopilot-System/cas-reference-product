import json

import pytest

from cas_reference_product.ingress import InvalidIngressRequest, create_worker_message


def test_ingress_validates_and_serializes_canonical_envelope(envelope) -> None:
    message = create_worker_message(envelope.model_dump_json().encode())

    assert json.loads(message)["runId"] == envelope.runId


def test_ingress_rejects_malformed_work_without_reasoning() -> None:
    with pytest.raises(InvalidIngressRequest, match="invalid CAS prompt envelope"):
        create_worker_message(b'{"prompt":"missing canonical fields"}')
