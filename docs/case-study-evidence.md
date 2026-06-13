# Immutable Golden-Path Evidence

The committed bundle under
`evidence/verified-local-golden-path-v0.1/` is the case-study evidence for one
verified local golden-path execution. It connects four independently versioned
CAS repositories without claiming an Azure deployment.

## What The Bundle Proves

- `cas-reference-product` served the deterministic local workflow over HTTP.
- `cas-evals` evaluated the actual returned output and preserved lifecycle and
  trace identifiers.
- The published `cas-contracts` v0.1.0 registry manifest is pinned by SHA-256.
- Every schema digest referenced by that registry manifest is verified before
  the canonical records are validated against the exact published schemas.
- The evaluation fixture, normalized evidence, fixture digest, and returned
  output digest are verified together.
- The `cas-platform` what-if script is pinned as a non-deploying interface
  reference. No what-if output or Azure deployment is claimed.
- Every included artifact digest and immutable source SHA is checked offline in
  tests and CI.

The canonical `artifact-manifest.json` and `verification-result.json` conform to
the vendored `cas-contracts` `ArtifactManifest` and `VerificationResult`
schemas. `bundle.json` maps their URN evidence identifiers to committed files
and records the claim boundaries.

## Container Digest Boundary

The bundle does not claim a container image digest. The repository builds a
local image in CI, but it does not publish a reproducible registry artifact
whose digest can be independently resolved. The canonical verification result
therefore marks this check as `skipped` rather than substituting a mutable tag
or local image ID.

## Verify

```powershell
./scripts/validate.ps1
./scripts/verify-evidence.ps1
```

The verifier is network-free. It fails when an artifact changes, a digest is
malformed, a source URI is not pinned to its full commit SHA, the golden result
does not pass exactly one case, or the platform evidence claims deployment.
