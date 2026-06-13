import hashlib
import json
from pathlib import Path

import pytest

from cas_reference_product.evidence import DEFAULT_BUNDLE, EvidenceVerificationError, verify_bundle


def copy_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    for source in DEFAULT_BUNDLE.rglob("*"):
        if source.is_file():
            destination = bundle / source.relative_to(DEFAULT_BUNDLE)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
    return bundle


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_committed_immutable_evidence_bundle_verifies() -> None:
    verify_bundle()


def test_changed_artifact_fails_digest_verification(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)

    descriptor = json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))
    changed = bundle / descriptor["evaluation"]["path"]
    changed.write_text("{}\n", encoding="utf-8")

    with pytest.raises(EvidenceVerificationError, match="digest mismatch"):
        verify_bundle(bundle)


def test_descriptor_digest_drift_fails_verification(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    descriptor_path = bundle / "bundle.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["sourceProvenance"]["sha256"] = "0" * 64
    write_json(descriptor_path, descriptor)

    with pytest.raises(
        EvidenceVerificationError,
        match="sourceProvenance descriptor digest mismatch",
    ):
        verify_bundle(bundle)


def test_platform_evidence_cannot_claim_deployment(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    descriptor_path = bundle / "bundle.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["platformWhatIf"]["deploymentClaim"] = "deployed"
    write_json(descriptor_path, descriptor)

    with pytest.raises(EvidenceVerificationError, match="must not claim deployment"):
        verify_bundle(bundle)


def test_unavailable_container_cannot_claim_digest(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    descriptor_path = bundle / "bundle.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["containerImage"]["digest"] = f"sha256:{'0' * 64}"
    write_json(descriptor_path, descriptor)

    with pytest.raises(EvidenceVerificationError, match="must not claim a digest"):
        verify_bundle(bundle)


def test_canonical_manifest_must_match_descriptor(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    manifest_path = bundle / "artifact-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"].pop()
    write_json(manifest_path, manifest)

    with pytest.raises(EvidenceVerificationError, match="ArtifactManifest does not match"):
        verify_bundle(bundle)


def test_published_contract_registry_digest_is_mandatory(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    contract = bundle / "artifacts" / "contracts" / "artifact-manifest.schema.json"
    contract.write_text("{}\n", encoding="utf-8")

    with pytest.raises(EvidenceVerificationError, match="registry digest mismatch"):
        verify_bundle(bundle)


def test_canonical_verification_result_schema_is_mandatory(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    result_path = bundle / "verification-result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["outcome"] = "unverified"
    write_json(result_path, result)

    with pytest.raises(EvidenceVerificationError, match="verification-result.schema.json"):
        verify_bundle(bundle)


def test_evaluation_response_digest_is_mandatory(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    fixture_path = bundle / "artifacts" / "golden-fixture.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    fixture["cases"][0]["response"] = "changed"
    write_json(fixture_path, fixture)

    descriptor_path = bundle / "bundle.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    changed_digest = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    descriptor["artifacts"][3]["sha256"] = changed_digest
    write_json(descriptor_path, descriptor)

    manifest_path = bundle / "artifact-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"][3]["sha256"] = changed_digest
    write_json(manifest_path, manifest)

    with pytest.raises(EvidenceVerificationError, match="evaluation fixture digest mismatch"):
        verify_bundle(bundle)
