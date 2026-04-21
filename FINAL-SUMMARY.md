# Final Summary — agentkit-cli v1.23.0 release completion

Status: BLOCKED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.23.0-release.md

## Outcome

BLOCKED

- The tested release candidate was pushed successfully to origin at `d6aceff`.
- The annotated release tag exists on origin: `v1.23.0` object `b592b7d` peels to `d6aceff`.
- The publish step failed: `uv publish --keyring-provider subprocess <built artifacts>` -> `Missing credentials for https://upload.pypi.org/legacy/`.
- PyPI proof after the failure still shows `agentkit-cli==1.22.0` live and no `1.23.0` release.
- Shipped truth therefore stays on `v1.22.0`, even though the `v1.23.0` branch and tag now exist remotely.

## Validation anchor

- Exact rerun validation plus the push, tag, publish, and PyPI verification trail are recorded in `progress-log.md`.
- Versioned companion report: `BUILD-REPORT-v1.23.0.md`.
