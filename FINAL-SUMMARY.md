# Final Summary — agentkit-cli v1.12.0 materialize worktrees

Status: SHIPPED
Date: 2026-04-20
Contract: all-day-build-contract-agentkit-cli-v1.12.0-release.md

## What shipped in this pass

- Added `agentkit materialize` as the deterministic post-stage step for local worktree creation.
- Added schema-backed materialize planning with dry-run support, collision refusal, serialized waiting lanes, and real local `git worktree add` execution for eligible lanes.
- Added seeded `.agentkit/materialize/` handoff directories inside created worktrees, including copied stage artifacts, machine-readable metadata, and target-aware `handoff.md` notes.
- Shipped `agentkit-cli==1.12.0` to origin and PyPI, then reconciled release surfaces so shipped truth is explicit.

## Shipped truth

- Tested release commit: `9e1e1440f01e557857c84b4ac00a405f3e51f505`
- Branch: `feat/v1.12.0-materialize-worktrees`
- Annotated tag: `v1.12.0` -> `9e1e1440f01e557857c84b4ac00a405f3e51f505`
- PyPI: `https://pypi.org/project/agentkit-cli/1.12.0/`
- Supported handoff lane: `source -> source-audit -> map -> contract -> bundle -> taskpack -> clarify -> resolve -> dispatch -> stage -> materialize`

## Validation surfaces used for shipped truth

- Focused materialize slice: `python3 -m pytest -q tests/test_materialize_engine.py tests/test_materialize_cmd.py tests/test_materialize_workflow.py` -> `9 passed in 2.31s`
- Cross-lane workflow slice: `python3 -m pytest -q tests/test_materialize_engine.py tests/test_materialize_cmd.py tests/test_materialize_workflow.py tests/test_stage.py tests/test_stage_workflow.py tests/test_dispatch.py tests/test_dispatch_workflow.py tests/test_resolve.py tests/test_resolve_workflow.py tests/test_resolve_cmd.py tests/test_taskpack.py` -> `46 passed in 4.04s`
- CLI integration slice: `python3 -m pytest -q tests/test_main.py tests/test_materialize_engine.py tests/test_materialize_cmd.py tests/test_materialize_workflow.py` -> `16 passed in 2.64s`
- Full suite: `.venv/bin/python -m pytest tests/ -x` -> `4903 passed, 1 warning in 417.24s (0:06:57)`
- Remote branch verification: `git ls-remote --heads origin feat/v1.12.0-materialize-worktrees`
- Remote tag verification: `git ls-remote --tags origin refs/tags/v1.12.0^{}`
- Registry verification: `https://pypi.org/pypi/agentkit-cli/1.12.0/json` -> `1.12.0` live with wheel and sdist present

## Chronology note

- The shipped artifact is pinned by tag `v1.12.0` at `9e1e1440f01e557857c84b4ac00a405f3e51f505`.
- Any later branch movement after that tag is docs-only chronology cleanup, not a new shipped artifact.
