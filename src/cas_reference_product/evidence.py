"""Offline verification for committed immutable evidence bundles."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).parents[2]
DEFAULT_BUNDLE = ROOT / "evidence" / "verified-local-golden-path-v0.1"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class EvidenceVerificationError(ValueError):
    """Raised when committed evidence does not match its immutable claims."""


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise EvidenceVerificationError(f"{path} must contain a JSON object")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contract_registry(contract_root: Path) -> Registry[Any]:
    resources = []
    for path in contract_root.glob("*.schema.json"):
        schema = _load_json(path)
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def _validate_contract(contract_root: Path, schema_name: str, instance: dict[str, Any]) -> None:
    schema = _load_json(contract_root / schema_name)
    validator = Draft202012Validator(
        schema,
        registry=_contract_registry(contract_root),
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        raise EvidenceVerificationError(f"{schema_name}: {errors[0].message}")


def verify_bundle(bundle_root: Path = DEFAULT_BUNDLE) -> None:
    """Verify every committed digest, source pin, canonical record, and claim boundary."""
    descriptor = _load_json(bundle_root / "bundle.json")
    artifact_manifest = _load_json(bundle_root / "artifact-manifest.json")
    verification_result = _load_json(bundle_root / "verification-result.json")
    contract_root = bundle_root / "artifacts" / "contracts"

    registry_manifest = _load_json(bundle_root / descriptor["contractRegistry"]["path"])
    for schema_entry in registry_manifest["schemas"]:
        schema_path = contract_root / schema_entry["path"]
        if _sha256(schema_path) != schema_entry["sha256"]:
            raise EvidenceVerificationError(f"{schema_entry['path']} registry digest mismatch")

    _validate_contract(contract_root, "artifact-manifest.schema.json", artifact_manifest)
    _validate_contract(contract_root, "verification-result.schema.json", verification_result)

    artifacts = descriptor.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise EvidenceVerificationError("bundle artifacts must be a non-empty list")

    descriptor_digests: dict[str, str] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise EvidenceVerificationError("bundle artifact entries must be objects")
        relative_path = artifact.get("path")
        expected = artifact.get("sha256")
        if not isinstance(relative_path, str) or not isinstance(expected, str):
            raise EvidenceVerificationError("artifact path and sha256 must be strings")
        if not SHA256_PATTERN.fullmatch(expected):
            raise EvidenceVerificationError(f"{relative_path} has an invalid SHA-256 digest")
        path = (bundle_root / relative_path).resolve()
        if not path.is_relative_to(bundle_root.resolve()):
            raise EvidenceVerificationError(f"{relative_path} escapes the bundle root")
        if _sha256(path) != expected:
            raise EvidenceVerificationError(f"{relative_path} digest mismatch")
        descriptor_digests[artifact["uri"]] = expected

    manifest_digests = {
        artifact["uri"]: artifact.get("sha256") for artifact in artifact_manifest["artifacts"]
    }
    if descriptor_digests != manifest_digests:
        raise EvidenceVerificationError("ArtifactManifest does not match bundle artifacts")

    for section_name in ("sourceProvenance", "contractRegistry", "evaluation", "platformWhatIf"):
        section = descriptor[section_name]
        path = bundle_root / section["path"]
        if section["sha256"] != _sha256(path):
            raise EvidenceVerificationError(f"{section_name} descriptor digest mismatch")

    provenance = _load_json(bundle_root / descriptor["sourceProvenance"]["path"])
    for source in provenance["repositories"]:
        sha = source["sha"]
        if not GIT_SHA_PATTERN.fullmatch(sha) or sha not in source["uri"]:
            raise EvidenceVerificationError(f"invalid immutable source reference: {source}")

    evaluation = _load_json(bundle_root / descriptor["evaluation"]["path"])
    if evaluation.get("summary") != {"failed": 0, "passed": 1, "total": 1}:
        raise EvidenceVerificationError("golden path evaluation did not pass exactly one case")
    if evaluation.get("suiteId") != "cas-reference-product-golden-v0.1":
        raise EvidenceVerificationError("unexpected golden path evaluation suite")
    for result in evaluation["results"]:
        _validate_contract(contract_root, "evaluation-result.schema.json", result)

    fixture = _load_json(bundle_root / descriptor["evaluation"]["fixturePath"])
    case = fixture["cases"][0]
    canonical_case = json.dumps(case, sort_keys=True, separators=(",", ":")).encode("utf-8")
    eval_evidence = evaluation["evidence"][0]
    if eval_evidence["fixtureDigest"] != f"sha256:{hashlib.sha256(canonical_case).hexdigest()}":
        raise EvidenceVerificationError("evaluation fixture digest mismatch")
    response = case["response"].encode("utf-8")
    response_digest = f"sha256:{hashlib.sha256(response).hexdigest()}"
    if eval_evidence["execution"]["responseDigest"] != response_digest:
        raise EvidenceVerificationError("evaluation response digest mismatch")

    platform = descriptor["platformWhatIf"]
    if platform.get("deploymentClaim") != "not-deployed":
        raise EvidenceVerificationError("platform what-if evidence must not claim deployment")

    container = descriptor["containerImage"]
    if container.get("status") == "available":
        digest = container.get("digest", "")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            raise EvidenceVerificationError("available container image requires a valid digest")
    elif "digest" in container:
        raise EvidenceVerificationError("unavailable container image must not claim a digest")

    if verification_result["outcome"] != "passed":
        raise EvidenceVerificationError("canonical VerificationResult must pass")


def main() -> int:
    bundle_root = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BUNDLE
    try:
        verify_bundle(bundle_root)
    except (EvidenceVerificationError, FileNotFoundError, KeyError, json.JSONDecodeError) as error:
        print(f"evidence verification failed: {error}", file=sys.stderr)
        return 1
    print(f"verified immutable evidence bundle: {bundle_root}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
