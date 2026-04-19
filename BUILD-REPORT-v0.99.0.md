# BUILD-REPORT-v0.99.0.md — agentkit-cli v0.99.0 context projections

Date: 2026-04-19
Builder: subagent mainline RC convergence pass
Contract: all-day-build-contract-agentkit-cli-v0.99.0-release.md
Prior feature contract: all-day-build-contract-agentkit-cli-v0.99.0-context-projections.md

## Summary

Completed the canonical-source context projection release. agentkit can now detect one source context file, project it into the major tool-specific filenames teams are converging on, report deterministic drift, and optionally wire projection fan-out into init.

## RC Objective

This branch is the local v0.99.0 release-candidate convergence pass. It preserves the completed context-projections feature set from `feat/v0.99.0-context-projections`, anchors chronology at sync point `f2bc687`, and reconciles repo-local report surfaces so the handoff story is explicit: release-ready locally, not yet published.

## Deliverables

| # | Deliverable | Status | Notes |
|---|-------------|--------|-------|
| D1 | Projection engine + target schema | ✅ Complete | Shared target metadata, detection priority, deterministic projections, and drift hashing landed |
| D2 | `agentkit project` CLI surface | ✅ Complete | Dry-run by default, `--write`, `--check`, `--output-dir`, and JSON reporting landed |
| D3 | Drift and sync verification | ✅ Complete | Sync now understands the broader target set and repairs stale or missing projections |
| D4 | Workflow integration | ✅ Complete | `agentkit init` can optionally fan out projections immediately |
| D5 | Docs, changelog, build report, versioning | ✅ Complete | README, changelog, build report, progress log, and version metadata updated to `0.99.0` |

## Test Results

- focused projection coverage on `rc/v0.99.0-mainline`: `uv run pytest -q tests/test_context_projections.py tests/test_project_cmd.py tests/test_sync_projections.py tests/test_init_projections.py tests/test_migrate_cmd.py tests/test_migrate_engine.py tests/test_init.py` -> `84 passed in 1.37s`
- final full suite on `rc/v0.99.0-mainline`: `uv run pytest -q` -> `4775 passed, 1 warning in 126.39s (0:02:06)`

## Release Notes

- current branch state: release branch and tag pushed, local artifacts built, PyPI publish blocked by missing credentials

- version metadata bumped to `0.99.0` in `pyproject.toml` and `agentkit_cli/__init__.py`
- compatibility preserved for the legacy migrate engine tests while enabling the broader projection workflow in the new command surfaces
- versioned build report copy added as `BUILD-REPORT-v0.99.0.md`
- status: PUSHED AND TAGGED, NOT SHIPPED, PyPI publish blocked by missing credentials

## Final RC Summary

- branch: `rc/v0.99.0-mainline`
- HEAD at D4 completion: final D4 commit on `rc/v0.99.0-mainline` (report this commit hash from `git rev-parse --short HEAD` at handoff)
- targeted validation: `84 passed in 1.37s`
- full suite: `4775 passed, 1 warning in 126.39s (0:02:06)`
- working tree: clean
- RC verdict: v0.99.0 remains unshipped because PyPI publish is blocked by missing credentials
