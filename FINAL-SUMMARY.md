# Final Summary — agentkit-cli v1.25.0 spec grounding

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.25.0-spec-grounding.md

## Outcome

SHIPPED

- Fixed the flagship stale-recommendation bug where `agentkit spec` kept proposing already-completed self-hosting/source-readiness work.
- Added regression coverage that pins the shipped-like repo-truth case across command and workflow paths.
- Grounded planner ranking in current canonical-source readiness plus recent shipped/local-ready workflow evidence.
- Upgraded the primary recommendation and contract seed so the next build is the honest adjacent spec-grounding increment.
- Pushed `feat/v1.25.0-spec-grounding`, tagged tested release commit `ecf1f46` as annotated `v1.25.0`, and published `agentkit-cli==1.25.0`.
- Verified PyPI version JSON, package-root JSON, and the exact version page all show `1.25.0` live with wheel plus sdist.
- Kept shipped tag truth separate from later docs-only chronology head `853a648`.

## Validation anchor

- Full validation and hygiene results are recorded in `progress-log.md`.
- Versioned companion report: `BUILD-REPORT-v1.25.0.md`.
