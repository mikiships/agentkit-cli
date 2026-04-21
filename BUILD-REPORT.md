# BUILD-REPORT.md — agentkit-cli v1.22.0 spec local release readiness

Status: RELEASE-READY (LOCAL-ONLY)
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.22.0-release.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Added a deterministic `agentkit spec` engine grounded in source, source-audit, repo-map, and recent workflow artifacts, with bounded alternates and contract-seeding fields. |
| D2 | ✅ Complete | Added first-class `agentkit spec` CLI wiring, stable markdown/stdout rendering, `--json`, `--output`, `--output-dir`, and `agentkit contract --spec` seeding. |
| D3 | ✅ Complete | Added focused spec engine, CLI, and workflow coverage for happy-path, missing-upstream, contradictory-upstream, fallback, and the `source -> audit -> map -> spec -> contract` lane. |
| D4 | ✅ Complete | Reconciled the active `v1.22.0` report surfaces to local-only truth, reran focused and full validation from the cleaned tree, and cleared repo hygiene noise. |
| D5 | ✅ Compatibility surface maintained | This report keeps the long-lived repo release-surface format intact, including explicit deliverable labels and high-count validation references used by older doc tests. |

## Validation

- Recall and contradiction hygiene: `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.22.0-spec` surfaced the expected current handoff cues (`v1.21.0` shipped, `v1.22.0 spec` active locally) and also flagged a stale external temporal-ledger cue still mentioning `v1.1.0`; repo-local release surfaces were reconciled to the current shipped line rather than that stale ledger entry.
- Status-conflict scan: `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.22.0-spec` -> `No contradictory success/blocker narratives found.`
- Focused spec/contract/map slice: `python3 -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_map.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_contract_d2.py tests/test_main.py` -> `37 passed`
- Full suite: `uv run python -m pytest -q` -> `5003 passed, 1 warning`
- Post-agent hygiene: `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.22.0-spec` -> `Total findings: 0`

## Current truth

- `agentkit-cli v1.22.0` is truthfully `RELEASE-READY (LOCAL-ONLY)` from this current repo state.
- `v1.22.0` is not shipped; `v1.21.0` remains the last shipped line.
- Supported repo-understanding lane is now `source -> audit -> map -> spec -> contract`.
- `agentkit spec` stays local-only and artifact-driven. It does not execute agents, mutate remotes, or publish anything.
- No push, tag, publish, or remote mutation has happened in this pass.

## Notes

- This file intentionally replaces stale `v1.21.0` shipped-state prose that no longer described the current worktree.
- A versioned companion report for this build is tracked at `BUILD-REPORT-v1.22.0.md`.
- `.gitignore` now ignores `.agent-relay/` and `.agentkit-last-run.json` so active runner artifacts do not dirty the local release-ready worktree.
