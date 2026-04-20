# BUILD-REPORT-v1.12.0.md — agentkit-cli v1.12.0 materialize worktrees

Status: SHIPPED
Date: 2026-04-20
Contract: all-day-build-contract-agentkit-cli-v1.12.0-release.md

## Summary

Shipped `agentkit materialize` as the deterministic post-stage step for local worktree creation. The command reads a saved `stage.json`, preserves serialized waiting lanes, refuses unsafe collisions, creates eligible local git worktrees, and seeds `.agentkit/materialize/` handoff directories per lane.

## Deliverables

- D1: schema-backed materialize planning engine in `agentkit_cli/materialize.py`
- D2: `agentkit materialize` CLI wiring, markdown/JSON rendering, `--dry-run`, and real local `git worktree add` execution
- D3: seeded `.agentkit/materialize/` handoff packets with copied stage artifacts, machine-readable metadata, and target-aware notes
- D4: regression and edge-case coverage for the `resolve -> dispatch -> stage -> materialize` handoff lane
- D5: pushed branch and tag, published `agentkit-cli==1.12.0`, and reconciled shipped release surfaces

## Validation

- `python3 -m pytest -q tests/test_materialize_engine.py tests/test_materialize_cmd.py tests/test_materialize_workflow.py` -> `9 passed in 2.31s`
- `python3 -m pytest -q tests/test_materialize_engine.py tests/test_materialize_cmd.py tests/test_materialize_workflow.py tests/test_stage.py tests/test_stage_workflow.py tests/test_dispatch.py tests/test_dispatch_workflow.py tests/test_resolve.py tests/test_resolve_workflow.py tests/test_resolve_cmd.py tests/test_taskpack.py` -> `46 passed in 4.04s`
- `python3 -m pytest -q tests/test_main.py tests/test_materialize_engine.py tests/test_materialize_cmd.py tests/test_materialize_workflow.py` -> `16 passed in 2.64s`
- `.venv/bin/python -m pytest tests/ -x` -> `4903 passed, 1 warning in 417.24s (0:06:57)` for tested release commit `9e1e1440f01e557857c84b4ac00a405f3e51f505`
- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.12.0-materialize-worktrees` -> completed
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.12.0-materialize-worktrees` -> no contradictory success/blocker narratives found
- `git ls-remote --heads origin feat/v1.12.0-materialize-worktrees` -> branch pushed and later allowed to advance only through docs-only chronology cleanup after the shipped tag
- `git ls-remote --tags origin refs/tags/v1.12.0^{}` -> `9e1e1440f01e557857c84b4ac00a405f3e51f505`
- `https://pypi.org/pypi/agentkit-cli/1.12.0/json` -> `1.12.0` live with wheel and sdist present

## Current Truth

- `agentkit-cli v1.12.0` is shipped.
- The supported handoff lane is `source -> source-audit -> map -> contract -> bundle -> taskpack -> clarify -> resolve -> dispatch -> stage -> materialize`.
- The shipped artifact is pinned by annotated tag `v1.12.0` at `9e1e1440f01e557857c84b4ac00a405f3e51f505`.
- Any later branch movement after that tag is docs-only chronology cleanup, not a new shipped artifact.
