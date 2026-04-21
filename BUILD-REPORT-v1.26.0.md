# BUILD-REPORT-v1.26.0.md — agentkit-cli spec shipped truth sync

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.26.0-release.md

## Summary

- Fixed the planner bug where the flagship repo still recommended the already-shipped `adjacent-grounding` increment.
- Added regression coverage for shipped-adjacent command and workflow cases.
- Refreshed `.agentkit/source.md`, version surfaces, changelog, and local closeout artifacts for truthful `v1.26.0` status.

## Validation

- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `20 passed in 13.05s`
- `uv run python -m agentkit_cli.main spec . --json` -> primary recommendation kind `subsystem-next-step`
- `uv run python -m pytest -q` -> `5008 passed, 1 warning in 1401.37s (0:23:21)`

## Release proof

- Branch pushed: `origin/feat/v1.26.0-spec-shipped-truth` now exists.
- Annotated tag pushed: `v1.26.0` object on origin peels to tested release commit `ba813b0836d8baa0cd6d1e5c27d42872c5fff555`.
- PyPI live: `agentkit-cli==1.26.0` verified via version JSON with wheel `agentkit_cli-1.26.0-py3-none-any.whl` (706174 bytes) and sdist `agentkit_cli-1.26.0.tar.gz` (1239070 bytes).
