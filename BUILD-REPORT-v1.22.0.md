# BUILD-REPORT-v1.22.0.md — agentkit-cli v1.22.0 spec local release readiness

Status: RELEASE-READY (LOCAL-ONLY)
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.22.0-spec-finisher.md

## Scope

- `agentkit spec` is now the deterministic next-build planning step between `map` and `contract`.
- Direct contract seeding now flows through saved `spec.json` artifacts via `agentkit contract --spec`.
- Supported repo-understanding lane is `source -> audit -> map -> spec -> contract`.
- `v1.22.0` remains local-only; no push, tag, publish, or remote mutation happened in this pass.

## Validation

- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.22.0-spec` surfaced the expected current handoff cues (`v1.21.0` shipped, `v1.22.0 spec` active locally) plus a stale external temporal-ledger cue still mentioning `v1.1.0`.
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.22.0-spec` -> `No contradictory success/blocker narratives found.`
- `python3 -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_map.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_contract_d2.py tests/test_main.py` -> `37 passed in 2.09s`
- `uv run python -m pytest -q` could not complete in this sandbox because `uv` first hit a cache-permission error and then panicked when redirected to `/tmp`.
- `.venv/bin/python -m pytest -q` -> `4995 passed, 8 skipped, 1 warning in 159.76s (0:02:39)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.22.0-spec` -> `Total findings: 0`

## Repo truth

- The `agentkit spec` work is truthfully `RELEASE-READY (LOCAL-ONLY)` from this repo state.
- The child finisher hit a sandbox-only git metadata blocker, but the parent session completed the required local commit step outside that sandbox.
- `v1.21.0` remains the last shipped release.
