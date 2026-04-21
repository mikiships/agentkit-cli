# BUILD-REPORT.md — agentkit-cli v1.26.0 spec shipped truth sync

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.26.0-release.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Reproduced the flagship repo case where `agentkit spec . --json` still recommended the already-shipped `adjacent-grounding` increment from v1.25.0. |
| D2 | ✅ Complete | Taught `agentkit_cli/spec_engine.py` to detect shipped or local-release-ready adjacent spec-grounding evidence and suppress that same recommendation on the next run. |
| D3 | ✅ Complete | Added shipped-adjacent command and workflow regressions that require a `shipped-truth-sync` follow-up instead of `adjacent-grounding`. |
| D4 | ✅ Complete | Refreshed `.agentkit/source.md`, version surfaces, changelog, and local closeout artifacts for truthful `v1.26.0` status. |

## Validation

- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `20 passed in 4.03s`
- `uv run python -m agentkit_cli.main spec . --json` now advances past the shipped v1.25.0 increment and returns primary recommendation kind `subsystem-next-step` from refreshed source truth.
- `uv run python -m pytest -q` -> `5008 passed, 1 warning in 768.47s (0:12:48)`
- Verified test-count floor recorded in this report: `5008 passed`.

## Current truth

- `agentkit-cli v1.26.0` is shipped.
- The shipped release tag is `v1.26.0`, and it peels to tested release commit `ba813b0836d8baa0cd6d1e5c27d42872c5fff555`.
- `origin/feat/v1.26.0-spec-shipped-truth` now carries this later docs-only chronology head, which preserves shipped tag truth separately from post-release reporting reconciliation.
- PyPI `agentkit-cli==1.26.0` is live with both wheel and sdist artifacts verified directly.
- The repo now self-specs past the already-shipped v1.25.0 adjacent-grounding increment.
