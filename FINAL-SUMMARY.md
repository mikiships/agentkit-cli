# Final Summary — agentkit-cli v1.26.0 spec shipped truth sync

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.26.0-release.md

## Outcome

SHIPPED

- Fixed the flagship follow-up bug where `agentkit spec` kept recommending the already-shipped v1.25.0 `adjacent-grounding` increment.
- Added shipped-adjacent regression coverage across command and workflow paths.
- Refreshed `.agentkit/source.md` so the local source objective matches current shipped repo truth.
- Shipped release commit: `ba813b0836d8baa0cd6d1e5c27d42872c5fff555` via annotated tag `v1.26.0`.
- Branch chronology continues separately after the tag so repo reporting can reflect shipped truth without changing the released artifact.
- PyPI `agentkit-cli==1.26.0` is live with both wheel and sdist artifacts.

## Validation anchor

- Full validation and exact command outcomes are recorded in `progress-log.md`.
- Final local verification from the release tree: `uv run python -m pytest -q` -> `5008 passed, 1 warning in 1401.37s (0:23:21)`.
- Versioned companion report: `BUILD-REPORT-v1.26.0.md`.
