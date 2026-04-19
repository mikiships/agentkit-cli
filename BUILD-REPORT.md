# BUILD-REPORT.md — agentkit-cli v0.99.0 release candidate

Date: 2026-04-19
Builder: subagent mainline RC convergence pass
Contract: all-day-build-contract-agentkit-cli-v0.99.0-mainline-rc.md
Prior feature contract: all-day-build-contract-agentkit-cli-v0.99.0-context-projections.md

## Summary

Completed the canonical-source context projection release. agentkit can now detect one source context file, project it into the major tool-specific filenames teams are converging on, report deterministic drift, and optionally wire projection fan-out into init.

## RC Objective

This canonical build report now tracks the local v0.99.0 release-candidate convergence branch. The RC preserves the feature set from `feat/v0.99.0-context-projections`, uses `f2bc687` as the documented pre-feature sync point, and treats this repo state as locally release-ready only after the RC validation and narrative reconciliation gates are complete.

## Deliverables

| # | Deliverable | Status | Notes |
|---|-------------|--------|-------|
| D1 | Projection engine + target schema | ✅ Complete | Shared target metadata, detection priority, deterministic projections, and drift hashing landed |
| D2 | `agentkit project` CLI surface | ✅ Complete | Dry-run by default, `--write`, `--check`, `--output-dir`, and JSON reporting landed |
| D3 | Drift and sync verification | ✅ Complete | Sync now understands the broader target set and repairs stale or missing projections |
| D4 | Workflow integration | ✅ Complete | `agentkit init` can optionally fan out projections immediately |
| D5 | Docs, changelog, build report, versioning | ✅ Complete | README, changelog, build report, progress log, and version metadata updated to `0.99.0` |

## Test Results

- focused projection coverage on `rc/v0.99.0-mainline`: `uv run pytest -q tests/test_context_projections.py tests/test_project_cmd.py tests/test_sync_projections.py tests/test_init_projections.py tests/test_migrate_cmd.py tests/test_migrate_engine.py tests/test_init.py` -> `84 passed in 1.41s`
- final full suite on `rc/v0.99.0-mainline`: `uv run pytest -q` -> `4775 passed, 1 warning in 123.64s (0:02:03)`

## Release Notes

- current branch state: local RC convergence, not shipped or published

- version metadata bumped to `0.99.0` in `pyproject.toml` and `agentkit_cli/__init__.py`
- compatibility preserved for the legacy migrate engine tests while enabling the broader projection workflow in the new command surfaces
- versioned build report copy added as `BUILD-REPORT-v0.99.0.md`
- status: RC IN PROGRESS, target state is release-ready locally and not published
