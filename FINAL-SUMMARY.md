# Final Summary — agentkit-cli v1.25.0 spec grounding

Status: RELEASE-READY (LOCAL-ONLY)
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.25.0-spec-grounding.md

## Outcome

RELEASE-READY (LOCAL-ONLY)

- Fixed the flagship stale-recommendation bug where `agentkit spec` kept proposing already-completed self-hosting/source-readiness work.
- Added regression coverage that pins the shipped-like repo-truth case across command and workflow paths.
- Grounded planner ranking in current canonical-source readiness plus recent shipped/local-ready workflow evidence.
- Upgraded the primary recommendation and contract seed so the next build is the honest adjacent spec-grounding increment.
- Updated local version, changelog, and report surfaces for `v1.25.0` without claiming any external release actions.

## Validation anchor

- Full validation and hygiene results are recorded in `progress-log.md`.
- Versioned companion report: `BUILD-REPORT-v1.25.0.md`.
