# agentkit-cli

## Objective
Teach the self-spec flow to replace the generic `subsystem-next-step` fallback for `agentkit_cli` with one bounded next recommendation grounded in current flagship repo truth.

## Commands
- `python3 -m agentkit_cli.main source-audit . --json`
- `python3 -m agentkit_cli.main spec . --json`
- `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`
- `uv run python -m pytest -q`

## Scope
Work only inside this repository. Keep changes narrowly focused on planner progression inside `agentkit_cli`, truthful local planning surfaces, and the regressions that prove the flagship planner now emits one bounded `agentkit_cli` next step after adjacent closeout.

## Constraints
- Keep outputs deterministic and file-backed.
- Preserve the supported flagship workflow instead of adding unrelated command sprawl.
- Do not reopen already-shipped flagship lanes except to read the evidence pattern they leave behind.
- No remote push, tag, or publish from this repo state.
- Keep report surfaces truthful: this branch remains local-only.

## Validation
- Confirm `agentkit spec . --json` now emits `kind=agentkit-cli-bounded-next-step`, title `Emit one bounded \`agentkit_cli\` next step after adjacent closeout`.
- Keep focused regressions in `tests/test_spec_engine.py`, `tests/test_spec_cmd.py`, `tests/test_spec_workflow.py`, and `tests/test_main.py` green.
- Run `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`.
- Run `uv run python -m pytest -q`.

## Deliverables
- Canonical `.agentkit/source.md` aligned with the bounded post-fallback objective.
- Successful self-spec output that emits one bounded `agentkit_cli` next recommendation instead of the generic `subsystem-next-step` fallback.
- Truthful local planning surfaces in `BUILD-TASKS.md` and `progress-log.md` that reflect the new local-only lane state.
- One local completion commit after validation passes.
