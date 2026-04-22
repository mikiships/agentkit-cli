# agentkit-cli

## Objective
Teach the self-spec flow to advance past the generic `subsystem-next-step` fallback for `agentkit_cli`, so the flagship repo-understanding workflow emits one concrete bounded next recommendation inside the `agentkit_cli` subsystem instead of stopping at the generic scoped-surface handoff.

## Commands
- `python3 -m agentkit_cli.main source-audit . --json`
- `python3 -m agentkit_cli.main spec . --output-dir <temp-dir> --json`
- `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`
- `uv run python -m pytest -q`

## Scope
Work only inside this repository. Keep changes narrowly focused on spec/planner progression, subsystem recommendation grounding for `agentkit_cli`, truthful local planning surfaces, and the tests that prove the planner emits a concrete next step instead of the generic subsystem fallback.

## Constraints
- Keep outputs deterministic and file-backed.
- Preserve the supported flagship workflow instead of adding unrelated command sprawl.
- Do not reopen already-shipped flagship lanes except to read their evidence pattern.
- No remote push, tag, or publish from this repo state.
- Keep report surfaces truthful: this branch is local-only until an intentional release pass happens later.

## Validation
- Reproduce the current `subsystem-next-step` output from repo truth before changing behavior.
- Add regressions showing the planner can turn the generic `agentkit_cli` subsystem fallback into one concrete bounded next recommendation from current repo evidence.
- Run `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`.
- Run `uv run python -m pytest -q`.

## Deliverables
- Canonical `.agentkit/source.md` aligned with the post-fallback objective.
- Successful self-spec output that emits one concrete `agentkit_cli` next recommendation instead of the generic `subsystem-next-step` fallback.
- Truthful local planning surfaces in `BUILD-TASKS.md`, `progress-log.md`, and the new build contract.
- One local completion commit after validation passes.
