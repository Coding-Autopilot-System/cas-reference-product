import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from cas_reference_product.models import LifecycleMetadata
from cas_reference_product.workflow import LocalWorkflowAgentService, WorkflowOrchestrator

# The cas-contracts schema version this consumer pins to. Its Pydantic models
# (cas_reference_product.models.LifecycleMetadata.schemaVersion) emit this exact
# value, so the pin below and the models must stay in lockstep.
PINNED_SCHEMA_VERSION = "0.1.0"

CONTRACT_ROOT = Path(__file__).parent / "contracts" / "cas-contracts" / f"v{PINNED_SCHEMA_VERSION}"
# Sibling source-of-truth checkout (local polyrepo). Absent in isolated CI.
UPSTREAM_ROOT = (
    Path(__file__).resolve().parents[2]
    / "cas-contracts"
    / "registry"
    / "releases"
    / f"v{PINNED_SCHEMA_VERSION}"
)


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

    assert manifest["version"] == PINNED_SCHEMA_VERSION
    for entry in manifest["schemas"]:
        content = (CONTRACT_ROOT / entry["path"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == entry["sha256"]


def test_pinned_version_is_the_version_models_emit() -> None:
    """The version this consumer pins must equal both the schemaVersion const the
    vendored schema enforces and the schemaVersion the Pydantic models emit.

    Fails red if the vendored release is bumped without updating models.LifecycleMetadata.
    """
    common = load_json(CONTRACT_ROOT / "common.schema.json")
    schema_const = common["$defs"]["lifecycleMetadata"]["properties"]["schemaVersion"]["const"]
    assert schema_const == PINNED_SCHEMA_VERSION

    model_default = LifecycleMetadata.model_fields["schemaVersion"].default
    assert model_default == PINNED_SCHEMA_VERSION


@pytest.mark.skipif(
    not UPSTREAM_ROOT.exists(),
    reason="sibling cas-contracts checkout not present (expected in isolated CI)",
)
def test_vendored_release_matches_upstream_source_of_truth() -> None:
    """Local-only drift guard: vendored copy must equal the sibling cas-contracts
    release byte-for-byte. Skipped in isolated CI where the sibling is not checked out.
    """
    for path in CONTRACT_ROOT.glob("*.json"):
        upstream = UPSTREAM_ROOT / path.name
        assert upstream.exists(), f"upstream missing {path.name}"
        assert (
            hashlib.sha256(path.read_bytes()).hexdigest()
            == hashlib.sha256(upstream.read_bytes()).hexdigest()
        ), f"vendored {path.name} drifted from upstream cas-contracts {PINNED_SCHEMA_VERSION}"


def test_prompt_envelope_serialization_conforms_to_v010_registry(envelope: "Any") -> None:
    assert_valid("prompt-envelope.schema.json", envelope.model_dump(mode="json"))


def test_run_event_serialization_conforms_to_v010_registry(envelope: "Any") -> None:
    result = WorkflowOrchestrator(LocalWorkflowAgentService(), envelope.repo).execute(envelope)

    for event in result.events:
        assert_valid("run-event.schema.json", event.model_dump(mode="json"))
