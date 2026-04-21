# BUILD-REPORT.md — agentkit-cli v1.25.0 spec grounding

Status: RELEASE-READY (LOCAL-ONLY)
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.25.0-spec-grounding.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Added deterministic stale-self-hosting regressions that pin the flagship failure where `agentkit spec` re-proposes already-satisfied self-hosting work. |
| D2 | ✅ Complete | Grounded recommendation ranking in canonical-source readiness plus recent shipped/local-ready workflow evidence so stale prerequisites no longer outrank the next adjacent build. |
| D3 | ✅ Complete | Tightened the primary recommendation and contract seed so markdown and JSON output explain the concrete adjacent spec-grounding increment. |
| D4 | ✅ Complete | Updated changelog, version, and report surfaces for truthful `v1.25.0` local closeout without claiming push, tag, or publish. |

## Validation

- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `18 passed in 1.10s`
- `uv run python -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `24 passed in 4.85s`
- `uv run python -m agentkit_cli.main spec . --json` now returns primary recommendation kind `adjacent-grounding` with a contract seed focused on grounding `agentkit spec` in current repo truth.
- `uv run python -m pytest -q` -> `5006 passed, 1 warning in 762.73s (0:12:42)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.25.0-spec-grounding` -> `No contradictory success/blocker narratives found.`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.25.0-spec-grounding` -> `Total findings: 0`

## Current truth

- `agentkit-cli v1.25.0` is release-ready from this local tree only.
- No push, tag, or publish was attempted in this pass.
- The flagship repo now self-specs the honest next adjacent build instead of recycling the already-satisfied self-hosting/source-readiness objective.
