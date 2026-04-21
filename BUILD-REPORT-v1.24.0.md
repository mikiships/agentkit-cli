# BUILD-REPORT-v1.24.0.md — agentkit-cli release completion

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.24.0-release.md

## Objective

Take the tested `v1.24.0` clean-JSON-stdout tree from truthful local `RELEASE-READY` to fully shipped truth.

## Current truth

- Release validation reran cleanly from `6790e96`.
- The tested release candidate was pushed successfully to origin at `6790e96`, and annotated tag `v1.24.0` object `1f86c659` peels to `6790e96`.
- The registry surface closed via the known-good local `.pypirc` path: exact `1.24.0` wheel and sdist artifacts were built from the tested release tree, then uploaded with `uvx twine upload --skip-existing`.
- PyPI now shows `agentkit-cli==1.24.0` live. Both `https://pypi.org/pypi/agentkit-cli/json` and `https://pypi.org/pypi/agentkit-cli/1.24.0/json` report `info.version = 1.24.0` and serve the wheel plus sdist for `1.24.0`.
- The exact project page URL `https://pypi.org/project/agentkit-cli/1.24.0/` now responds `200`, even though simple non-browser fetches still hit PyPI's client-challenge HTML.
- Therefore `v1.24.0` is shipped, and it is now the last shipped release.
