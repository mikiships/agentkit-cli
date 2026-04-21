# BUILD-REPORT-v1.23.0.md — agentkit-cli release completion

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.23.0-release.md

## Objective

Take the tested `v1.23.0` self-spec source tree from truthful local `RELEASE-READY` to fully shipped truth.

## Current truth

- Release validation reran cleanly from `d6aceff`.
- The tested release candidate was pushed successfully to origin at `d6aceff`, and annotated tag `v1.23.0` peels to `d6aceff`.
- The registry surface closed via the local `.pypirc` auth path: a tagged temp worktree built `1.23.0`, then `uvx twine upload --skip-existing` completed the live upload after `uv publish --keyring-provider subprocess` had falsely suggested there was no usable credential path.
- PyPI now shows `agentkit-cli==1.23.0` live, and the version JSON serves both `agentkit_cli-1.23.0-py3-none-any.whl` and `agentkit_cli-1.23.0.tar.gz`.
- Therefore `v1.23.0` is shipped, and it is now the last shipped release.
