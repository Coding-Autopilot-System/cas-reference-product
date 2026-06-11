from fastapi.testclient import TestClient

from cas_reference_product.app import create_app
from cas_reference_product.config import Settings


def test_workflow_api_emits_canonical_events(envelope) -> None:
    client = TestClient(create_app(Settings()))

    response = client.post("/api/v1/workflows", json=envelope.model_dump(mode="json"))

    assert response.status_code == 200
    body = response.json()
    assert body["runId"] == "run-001"
    assert [event["status"] for event in body["events"]] == ["running", "succeeded"]
    assert all(event["schemaVersion"] == "0.1.0" for event in body["events"])
    assert all(event["correlationId"] == "corr-001" for event in body["events"])


def test_health_and_readiness() -> None:
    client = TestClient(create_app(Settings()))

    assert client.get("/").json()["version"] == "0.1.0"
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").json() == {"status": "ready", "backend": "local"}


def test_incomplete_foundry_configuration_is_not_ready() -> None:
    client = TestClient(create_app(Settings(workflow_backend="foundry")))

    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 503
    assert client.post("/api/v1/workflows", json={}).status_code == 422
