# agentkit-cli

## Objective
Teach the flagship self-spec flow to recognize when `flagship-post-closeout-advance` is already closed out in current repo truth, stop replaying that lane, and promote the next honest flagship recommendation from current shipped or local-release-ready evidence.

## Commands
- `python3 -m agentkit_cli.main source-audit . --json`
- `python3 -m agentkit_cli.main spec . --output-dir <temp-dir> --json`
- `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`
- `uv run python -m pytest -q`

## Scope
Work only inside this repository. Keep changes narrowly focused on deterministic flagship planner progression, adjacent-lane recommendation selection, the nearest truthful planning surfaces, and the tests that prove the planner advances past already-closed lanes.

## Constraints
- Keep outputs deterministic and file-backed.
- Preserve the supported flagship workflow instead of adding unrelated command sprawl.
- Do not reopen the already shipped `flagship-concrete-next-step` or `flagship-post-closeout-advance` lanes.
- No remote push, tag, or publish from this repo state.
- Keep report surfaces truthful: this branch is local-only until an intentional release pass happens later.

## Validation
- Reproduce the stale planner output from current repo truth before changing behavior.
- Add regressions showing shipped or local-release-ready evidence for `flagship-post-closeout-advance` suppresses replay.
- Run `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`.
- Run `uv run python -m pytest -q`.

## Deliverables
- Canonical `.agentkit/source.md` aligned with the new flagship objective.
- Successful self-spec output that advances past the closed `flagship-post-closeout-advance` lane.
- Truthful local planning surfaces in `BUILD-TASKS.md`, `progress-log.md`, and the new build contract.
- One local completion commit after validation passes.
