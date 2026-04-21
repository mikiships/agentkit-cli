# BUILD-REPORT-v1.23.0.md — agentkit-cli release completion

Status: BLOCKED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.23.0-release.md

## Objective

Take the tested `v1.23.0` self-spec source tree from truthful local `RELEASE-READY` to fully shipped truth, or stop with the exact blocker.

## Current truth

- Release validation reran cleanly from `d6aceff`.
- The tested release candidate was pushed successfully to origin at `d6aceff`, and annotated tag `v1.23.0` peels to `d6aceff`.
- PyPI publish is blocked because `uv publish --keyring-provider subprocess` failed with `Missing credentials for https://upload.pypi.org/legacy/`.
- PyPI still shows `agentkit-cli==1.22.0` as the live line, with no `1.23.0` release present.
- Therefore `v1.23.0` is not shipped, and `v1.22.0` remains the last shipped release.
