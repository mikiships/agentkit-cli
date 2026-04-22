# Progress Log — agentkit-cli v1.31.0 subsystem next step

Status: IN PROGRESS
Date: 2026-04-22

## Why this lane exists

After `v1.30.0` shipped, the next honest self-spec output on current repo truth falls through to the generic `subsystem-next-step` recommendation for `agentkit_cli`. This lane should turn that generic subsystem fallback into one concrete bounded next recommendation instead of leaving build-loop with only a broad scoped-surface handoff.

## Grounded starting truth

- Starting HEAD is `77cf238` on `feat/v1.31.0-subsystem-next-step`
- `v1.30.0` is already shipped, with annotated tag and PyPI live in the parent line
- On the invalidated successor branch, `python3 -m agentkit_cli.main spec . --json` now falls through to `kind=subsystem-next-step`, title `Use agentkit_cli as the next scoped build surface`
- Family is clear, cron health is clean, and the earlier closeout-lane launch was invalidated, so this became the next honest heartbeat move

## Planned deliverables

- Add planner grounding for the `agentkit_cli` subsystem so the generic fallback becomes one concrete bounded next recommendation
- Promote truthful why-now, scope, and validation fields for that recommendation
- Add focused regressions in spec engine, spec command, and spec workflow coverage for the subsystem-fallback case
- Refresh `.agentkit/source.md` and `BUILD-TASKS.md` so the active local-only objective matches the new lane truthfully

## Validation plan

- `python3 -m agentkit_cli.main source-audit . --json`
- `python3 -m agentkit_cli.main spec . --json`
- `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`
- `uv run python -m pytest -q`
