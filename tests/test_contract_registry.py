import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from cas_reference_product.workflow import LocalWorkflowAgentService, WorkflowOrchestrator

CONTRACT_ROOT = Path(__file__).parent / "contracts" / "cas-contracts" / "v0.1.0"


def load_json(path: Path) -> dict[str, Any]:
    from typing import cast
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def contract_registry() -> Registry[Any]:
    resources = []
    for path in CONTRACT_ROOT.glob("*.schema.json"):
        schema = load_json(path)
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def assert_valid(schema_name: str, instance: dict[str, Any]) -> None:
    schema = load_json(CONTRACT_ROOT / schema_name)
    Draft202012Validator(schema, registry=contract_registry()).validate(instance)


def test_vendored_contract_release_matches_manifest_hashes() -> None:
    manifest = load_json(CONTRACT_ROOT / "manifest.json")

    assert manifest["version"] == "0.1.0"
    for entry in manifest["schemas"]:
        content = (CONTRACT_ROOT / entry["path"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == entry["sha256"]


def test_prompt_envelope_serialization_conforms_to_v010_registry(envelope: "Any") -> None:
    assert_valid("prompt-envelope.schema.json", envelope.model_dump(mode="json"))


def test_run_event_serialization_conforms_to_v010_registry(envelope: "Any") -> None:
    result = WorkflowOrchestrator(LocalWorkflowAgentService(), envelope.repo).execute(envelope)

    for event in result.events:
        assert_valid("run-event.schema.json", event.model_dump(mode="json"))
