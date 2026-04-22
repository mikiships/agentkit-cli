# agentkit-cli

## Objective
Teach the flagship self-spec flow to detect when `flagship-post-closeout-advance` is already shipped or truthfully local release-ready, suppress replay of that closed lane, and emit one concrete adjacent flagship recommendation, `flagship-adjacent-next-step`, instead of the generic subsystem fallback.

## Commands
- `python3 -m agentkit_cli.main source-audit . --json`
- `python3 -m agentkit_cli.main spec . --output-dir <temp-dir> --json`
- `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`
- `uv run python -m pytest -q`

## Scope
Work only inside this repository. Keep changes narrowly focused on flagship planner progression, adjacent-lane recommendation text, contract seeding, the nearest truthful local planning surfaces, and the tests that prove the planner advances past already-closed lanes.

## Constraints
- Keep outputs deterministic and file-backed.
- Preserve the supported flagship workflow instead of adding unrelated command sprawl.
- Do not reopen the already-completed `flagship-post-closeout-advance` implementation lane.
- No remote push, tag, or publish from this repo state.
- Keep report surfaces truthful: this branch is local-only until an intentional release pass happens later.

## Validation
- Reproduce the current adjacent-lane planner output from shipped repo truth before changing behavior.
- Add regressions showing shipped or truthful local-release-ready evidence for `flagship-post-closeout-advance` emits the concrete adjacent flagship lane deterministically.
- Run `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`.
- Run `uv run python -m pytest -q`.

## Deliverables
- Canonical `.agentkit/source.md` aligned with the adjacent flagship objective.
- Successful self-spec output that emits `flagship-adjacent-next-step` from the shipped flagship repo truthfully.
- Truthful local planning surfaces in `BUILD-TASKS.md`, `progress-log.md`, and the new build contract.
- One local completion commit after validation passes.
