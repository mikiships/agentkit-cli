# BUILD-REPORT-v1.26.0.md — agentkit-cli spec shipped truth sync

Status: RELEASE-READY (LOCAL-ONLY)
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.26.0-spec-shipped-truth-sync.md

## Summary

- Fixed the planner bug where the flagship repo still recommended the already-shipped `adjacent-grounding` increment.
- Added regression coverage for shipped-adjacent command and workflow cases.
- Refreshed `.agentkit/source.md`, version surfaces, changelog, and local closeout artifacts for truthful `v1.26.0` status.

## Validation

- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `20 passed in 4.03s`
- `uv run python -m agentkit_cli.main spec . --json` -> primary recommendation kind `subsystem-next-step`
- `uv run python -m pytest -q` -> `5008 passed, 1 warning in 768.47s (0:12:48)`
