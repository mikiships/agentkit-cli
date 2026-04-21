# BUILD-REPORT-v1.22.0.md — agentkit-cli v1.22.0 shipped release report

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.22.0-release.md

## Scope

- `agentkit spec` is now the shipped deterministic next-build planning step between `map` and `contract`.
- Direct contract seeding flows through saved `spec.json` artifacts via `agentkit contract --spec`.
- Supported repo-understanding lane is `source -> audit -> map -> spec -> contract`.
- Tag truth and later chronology are intentionally separated in this report.

## Validation

- `pre-action-recall.sh` surfaced the expected handoff cues (`v1.21.0` shipped, `v1.22.0` active locally) plus a stale external temporal cue still mentioning `v1.1.0`; release surfaces were reconciled against direct git and PyPI truth instead.
- `check-status-conflicts.sh` found no contradictory success or blocker narrative before release.
- `python3 -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_map.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_contract_d2.py tests/test_main.py` -> `37 passed in 2.31s`
- `uv run python -m pytest -q` -> `5003 passed, 1 warning in 187.11s (0:03:07)`
- `post-agent-hygiene-check.sh` -> `Total findings: 0`
- Branch and tag proof: `origin/feat/v1.22.0-spec` is at a later docs-only chronology head, while annotated tag `v1.22.0` peels to shipped release commit `2c2b89f`
- Registry proof: PyPI JSON for `agentkit-cli/1.22.0` lists both the wheel (`704554` bytes) and sdist (`1231351` bytes)

## Repo truth

- The `agentkit spec` work is truthfully SHIPPED as `agentkit-cli v1.22.0`.
- The shipped release is pinned to `v1.22.0` -> `2c2b89f`.
- The branch later advanced to a later docs-only chronology head after the release tag and publish were already complete.
