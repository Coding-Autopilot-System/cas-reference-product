import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from cas_reference_product.evidence import (
    DEFAULT_BUNDLE,
    EvidenceVerificationError,
    _load_json,
    main,
    verify_bundle,
)


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


def rebuild_evidence_digests(bundle: Path) -> None:
    descriptor_path = bundle / "bundle.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))

    for section_name in ("sourceProvenance", "contractRegistry", "evaluation", "platformWhatIf"):
        section = descriptor[section_name]
        section["sha256"] = hashlib.sha256((bundle / section["path"]).read_bytes()).hexdigest()

    artifact_manifest_path = bundle / "artifact-manifest.json"
    artifact_manifest = json.loads(artifact_manifest_path.read_text(encoding="utf-8"))
    manifest_entries = {item["uri"]: item for item in artifact_manifest["artifacts"]}
    for artifact in descriptor["artifacts"]:
        digest = hashlib.sha256((bundle / artifact["path"]).read_bytes()).hexdigest()
        artifact["sha256"] = digest
        manifest_entries[artifact["uri"]]["sha256"] = digest

    write_json(artifact_manifest_path, artifact_manifest)
    write_json(descriptor_path, descriptor)


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


def test_load_json_rejects_non_object_json(tmp_path: Path) -> None:
    path = tmp_path / "array.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(EvidenceVerificationError, match="must contain a JSON object"):
        _load_json(path)


def test_bundle_artifacts_must_be_a_non_empty_list(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    descriptor_path = bundle / "bundle.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["artifacts"] = []
    write_json(descriptor_path, descriptor)

    with pytest.raises(
        EvidenceVerificationError,
        match="bundle artifacts must be a non-empty list",
    ):
        verify_bundle(bundle)


def test_bundle_artifact_entry_must_be_an_object(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    descriptor_path = bundle / "bundle.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["artifacts"] = ["not-an-object"]
    write_json(descriptor_path, descriptor)

    with pytest.raises(EvidenceVerificationError, match="bundle artifact entries must be objects"):
        verify_bundle(bundle)


def test_artifact_missing_path_or_sha256_raises(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    descriptor_path = bundle / "bundle.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["artifacts"] = [{"uri": "urn:test", "path": None, "sha256": None}]
    write_json(descriptor_path, descriptor)

    with pytest.raises(EvidenceVerificationError, match="artifact path and sha256 must be strings"):
        verify_bundle(bundle)


def test_artifact_sha256_with_invalid_pattern_raises(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    descriptor_path = bundle / "bundle.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["artifacts"] = [
        {"uri": "urn:test", "path": "artifact-manifest.json", "sha256": "invalid"}
    ]
    write_json(descriptor_path, descriptor)

    with pytest.raises(EvidenceVerificationError, match="has an invalid SHA-256 digest"):
        verify_bundle(bundle)


def test_artifact_path_traversal_outside_bundle_root_raises(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    descriptor_path = bundle / "bundle.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["artifacts"] = [
        {"uri": "urn:test", "path": "../../outside.json", "sha256": "a" * 64}
    ]
    write_json(descriptor_path, descriptor)

    with pytest.raises(EvidenceVerificationError, match="escapes the bundle root"):
        verify_bundle(bundle)


def test_invalid_git_sha_in_source_provenance_raises(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    provenance_path = bundle / "artifacts" / "source-provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["repositories"][0]["sha"] = "not-a-git-sha"
    write_json(provenance_path, provenance)
    rebuild_evidence_digests(bundle)

    with pytest.raises(EvidenceVerificationError, match="invalid immutable source reference"):
        verify_bundle(bundle)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("summary", {"failed": 1, "passed": 0, "total": 1}, "did not pass exactly one case"),
        ("suiteId", "wrong-suite", "unexpected golden path evaluation suite"),
    ],
)
def test_evaluation_metadata_mismatch_raises(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    bundle = copy_bundle(tmp_path)
    evaluation_path = bundle / "artifacts" / "eval-evidence.json"
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    evaluation[field] = value
    write_json(evaluation_path, evaluation)
    rebuild_evidence_digests(bundle)

    with pytest.raises(EvidenceVerificationError, match=message):
        verify_bundle(bundle)


def test_evaluation_response_digest_mismatch_raises(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    evaluation_path = bundle / "artifacts" / "eval-evidence.json"
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    evaluation["evidence"][0]["execution"]["responseDigest"] = f"sha256:{'0' * 64}"
    write_json(evaluation_path, evaluation)
    rebuild_evidence_digests(bundle)

    with pytest.raises(EvidenceVerificationError, match="evaluation response digest mismatch"):
        verify_bundle(bundle)


def test_available_container_with_invalid_digest_raises(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    descriptor_path = bundle / "bundle.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["containerImage"] = {"status": "available", "digest": "invalid"}
    write_json(descriptor_path, descriptor)

    with pytest.raises(EvidenceVerificationError, match="requires a valid digest"):
        verify_bundle(bundle)


def test_verification_result_outcome_not_passed_raises(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    result_path = bundle / "verification-result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["outcome"] = "failed"
    write_json(result_path, result)

    with pytest.raises(EvidenceVerificationError, match="canonical VerificationResult must pass"):
        verify_bundle(bundle)


def test_main_returns_zero_on_valid_bundle() -> None:
    with patch.object(sys, "argv", ["evidence"]):
        assert main() == 0


def test_main_returns_one_on_invalid_bundle_path() -> None:
    with patch.object(sys, "argv", ["evidence", "/nonexistent/path/bundle"]):
        assert main() == 1


def test_main_returns_one_on_verification_failure(tmp_path: Path) -> None:
    bundle = copy_bundle(tmp_path)
    descriptor_path = bundle / "bundle.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["platformWhatIf"]["deploymentClaim"] = "deployed"
    write_json(descriptor_path, descriptor)

    with patch.object(sys, "argv", ["evidence", str(bundle)]):
        assert main() == 1
