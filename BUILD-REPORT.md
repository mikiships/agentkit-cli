# BUILD-REPORT.md — agentkit-cli v0.99.0 release candidate

Date: 2026-04-19
Builder: subagent mainline RC convergence pass
Contract: all-day-build-contract-agentkit-cli-v0.99.0-release.md
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

- focused projection coverage on `rc/v0.99.0-mainline`: `uv run pytest -q tests/test_context_projections.py tests/test_project_cmd.py tests/test_sync_projections.py tests/test_init_projections.py tests/test_migrate_cmd.py tests/test_migrate_engine.py tests/test_init.py` -> `84 passed in 1.36s`
- final full suite on `rc/v0.99.0-mainline`: `uv run pytest -q` -> `4775 passed, 1 warning in 127.61s (0:02:07)`

## Release Notes

- current branch state: release branch is on origin at docs-only cleanup commit `d9cb8cf`, release tag `v0.99.0` remains on shipped commit `3b2f21d`, and PyPI now shows `agentkit-cli==0.99.0` live
- current artifact verification: `uv build` succeeded from this checkout and rebuilt `dist/agentkit_cli-0.99.0.tar.gz` plus `dist/agentkit_cli-0.99.0-py3-none-any.whl`
- PyPI registry proof:
  - `agentkit_cli-0.99.0-py3-none-any.whl` uploaded `2026-04-19T02:24:46.882825Z`, sha256 `47e8f716f3f588c85eeb2f1b3e6a3fe718413955d74be7c2f5ca5e0c72b04766`
  - `agentkit_cli-0.99.0.tar.gz` uploaded `2026-04-19T02:24:48.497683Z`, sha256 `e0518e4ef25b083bedd6fcc5bc9b206cbed270b3f92ec5d6a5d3624519a2c508`
- version metadata bumped to `0.99.0` in `pyproject.toml` and `agentkit_cli/__init__.py`
- compatibility preserved for the legacy migrate engine tests while enabling the broader projection workflow in the new command surfaces
- versioned build report copy added as `BUILD-REPORT-v0.99.0.md`
- status: SHIPPED, with tests green, remote branch verified, release tag verified, and PyPI live

## Final RC Summary

- branch: `rc/v0.99.0-mainline`
- branch head at shipped-state reconciliation: `d9cb8cf763c97b7ecc8794f827853cc3d57738f0`
- shipped release tag: `v0.99.0` -> `3b2f21df8defa08cbdcfe5b69c140d02292ecdf6`
- targeted validation: `84 passed in 1.36s`
- full suite: `4775 passed, 1 warning in 127.61s (0:02:07)`
- working tree: clean after report reconciliation
- RC verdict: v0.99.0 is shipped, with docs-only chronology cleanup living after the tagged release commit on the release branch
