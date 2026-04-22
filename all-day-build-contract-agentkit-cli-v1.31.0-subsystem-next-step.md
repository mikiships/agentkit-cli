# All-Day Build Contract: agentkit-cli v1.31.0 subsystem next step

Status: In Progress
Date: 2026-04-22
Owner: OpenClaw build-loop pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Advance the self-spec flow past the generic `subsystem-next-step` fallback for `agentkit_cli`. Use current repo evidence to turn that broad subsystem handoff into one concrete bounded next recommendation with truthful why-now, scope, and validation fields.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when every deliverable and validation item is checked off.
3. Reproduce the current planner output from this branch before changing behavior.
4. Work only inside `/Users/mordecai/repos/agentkit-cli-v1.31.0-subsystem-next-step`.
5. Keep the repo local-only. No push, tag, publish, or remote mutation from this lane.
6. Keep changes narrowly focused on planner progression, `agentkit_cli` subsystem grounding, truthful local surfaces, and test coverage.
7. Commit after each completed deliverable cluster, not only at the end.
8. If you hit the same blocker three times, stop and write a blocker report instead of thrashing.
9. Do not reopen already-shipped flagship lanes except to read the evidence pattern they leave behind.
10. Before claiming completion, run the required validation commands from the final tree and leave the worktree clean.

## 3. Feature Deliverables

### D1. Reproduce and explain the subsystem fallback
- [ ] Confirm the current `agentkit spec . --json` recommendation from repo truth.
- [ ] Identify the exact repo evidence that should narrow `agentkit_cli` into one concrete next recommendation.
- [ ] Record the starting fallback gap in `progress-log.md`.

### D2. Implement deterministic subsystem grounding
- [ ] Update the planner logic and nearest helpers so the generic `subsystem-next-step` fallback advances to one concrete `agentkit_cli` next step.
- [ ] Keep the advancement deterministic and grounded in local file-backed evidence.
- [ ] Emit one fresh bounded recommendation instead of the generic subsystem fallback.

### D3. Refresh truthful local planning surfaces
- [ ] Update `.agentkit/source.md` to the post-fallback objective.
- [ ] Update `BUILD-TASKS.md` and `progress-log.md` so they describe the new lane truthfully.
- [ ] Keep all reporting explicit that this branch remains local-only.

### D4. Prove the new lane and close locally
- [ ] Add or update focused regressions in `tests/test_spec_engine.py`, `tests/test_spec_cmd.py`, `tests/test_spec_workflow.py`, and `tests/test_main.py`.
- [ ] Run the focused validation slice.
- [ ] Run the full suite.
- [ ] Leave one local completion commit and a clean tree.

## 4. Test Requirements

- [ ] `python3 -m agentkit_cli.main source-audit . --json`
- [ ] `python3 -m agentkit_cli.main spec . --json`
- [ ] `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`
- [ ] `uv run python -m pytest -q`
- [ ] Existing tests remain green.

## 5. Reports

- Update `progress-log.md` after each deliverable cluster with actual repo truth.
- If blocked, write `blocker-report-v1.31.0-subsystem-next-step.md` with the failure, attempts, and recommended next move.
- Final summary must include: HEAD, branch, new primary recommendation kind/title, focused test result, full-suite result, and clean-tree status.

## 6. Stop Conditions

- All deliverables complete, validations green, and local completion commit made -> DONE
- Same blocker hit 3 times -> STOP and write blocker report
- Scope drifts outside planner progression for `agentkit_cli` -> STOP and report
