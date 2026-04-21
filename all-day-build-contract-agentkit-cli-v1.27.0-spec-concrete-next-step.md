# All-Day Build Contract — agentkit-cli v1.27.0 spec concrete next step

## Objective
Teach the flagship self-spec flow to emit a concrete adjacent build recommendation and contract seed after shipped-truth sync, instead of falling back to the generic `subsystem-next-step` recommendation for `agentkit_cli`.

## Why this is the next honest increment
- `v1.26.0` is shipped and the stale shipped-adjacent loop is closed.
- From current shipped truth, `agentkit spec . --json` no longer repeats old work, but it still lands on a broad generic fallback: `subsystem-next-step` with `Use agentkit_cli as the next scoped build surface`.
- That means the flagship repo is truthful again, but not yet specifically self-directing.
- The adjacent increment is to make the planner produce a bounded, evidence-backed next lane for the flagship repo itself.

## Deliverables
- Add planner logic that detects when the flagship repo has already completed shipped-truth sync and should advance to a concrete next build recommendation instead of the generic subsystem fallback.
- Emit a concrete recommendation title, objective, why-now reasoning, scope boundaries, and contract seed that are specific enough to open the next lane without human reinterpretation.
- Add or update focused regression coverage for the post-shipped-truth flagship case across engine, command, and workflow paths.
- Refresh `.agentkit/source.md` and nearby local closeout surfaces only if needed so they truthfully describe the new active objective and recommended lane.

## Validation
- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`
- `uv run python -m agentkit_cli.main spec . --json`
- `uv run python -m pytest -q`

## Constraints
- Local lane setup and implementation only, no push, tag, publish, or external posting.
- Keep the work bounded to `agentkit_cli`, the nearest spec tests, and truthful local status surfaces.
- Do not reopen already-shipped canonical-source, adjacent-grounding, or shipped-truth-sync work except where new planner logic must recognize those completed states.
- Prefer deterministic file-backed evidence over heuristics that depend on network or mutable external state.
