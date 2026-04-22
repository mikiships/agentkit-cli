# Progress Log — agentkit-cli v1.28.0 flagship post-closeout advance

Status: IN PROGRESS
Date: 2026-04-21

## Why this lane exists

After the v1.27.0 concrete-next-step closeout, the flagship repo still let `agentkit spec . --json` replay `flagship-concrete-next-step` from its own local truth. That made the self-spec flow concrete, but not yet self-advancing.

## What changed

- Added replay detection in `agentkit_cli/spec_engine.py` for flagship repos whose shipped or local-release-ready artifacts already close out `flagship-concrete-next-step`.
- Promoted a new `flagship-post-closeout-advance` recommendation, title, objective, and contract seed once replay suppression fires.
- Updated focused engine, command, and workflow regressions for the post-closeout replay case.
- Advanced `.agentkit/source.md`, `BUILD-TASKS.md`, `CHANGELOG.md`, `BUILD-REPORT.md`, and `FINAL-SUMMARY.md` to truthful `v1.28.0` local-only wording.
- Bumped repo version surfaces to `1.28.0` in `pyproject.toml`, `agentkit_cli/__init__.py`, and the main-version test.

## Validation

- Pending focused spec/source validation from this worktree.
- Pending full-suite `uv run python -m pytest -q` closeout pass.

## Current blocker

Validation has not been run yet from this worktree, so the tree is not ready to call `RELEASE-READY (LOCAL-ONLY)`.


## D1 update

- Grounded the replay path in real repo truth: current local artifacts already mark `flagship-concrete-next-step` as shipped or `RELEASE-READY (LOCAL-ONLY)`.
- Added deterministic replay suppression in `agentkit_cli/spec_engine.py` so the old flagship lane is no longer eligible once those artifacts exist.
- Added focused engine coverage for the closed-lane detection path.
- Validation for D1: `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `26 passed`.
- Next: keep the fresh adjacent recommendation and local closeout surfaces aligned through the remaining deliverables.
