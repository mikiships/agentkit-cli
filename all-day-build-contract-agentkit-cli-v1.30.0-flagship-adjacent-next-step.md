# All-Day Build Contract: agentkit-cli v1.30.0 flagship adjacent next step

Status: In Progress
Date: 2026-04-21
Owner: OpenClaw sub-agent execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Advance the flagship planner from the freshly emitted `flagship-adjacent-next-step` recommendation into its next truthful bounded increment, using current shipped repo truth.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Re-run the required validation from the current tree before any completion claim.
4. Ground the starting recommendation directly from current repo truth before changing behavior.
5. Keep the work inside flagship planner progression logic, nearest tests, and truthful local planning surfaces.
6. Do not reopen already-shipped `flagship-post-closeout-advance` or `flagship-adjacent-next-step` behavior as if unfinished once the current tree proves otherwise.
7. No remote push, tag, publish, or external mutation from this repo state.
8. Commit after each completed deliverable cluster, not only at the end.
9. If stuck on the same issue for 3 attempts, stop and write a blocker report.
10. Read existing planning/report surfaces before mutating them.

## 3. Feature Deliverables

### D1. Ground the adjacent-lane planner state

Required:
- `.agentkit/source.md`
- `BUILD-TASKS.md`
- `progress-log.md`

- [ ] Prove the current repo is already shipped for `v1.29.0`.
- [ ] Prove `agentkit spec` now recommends `flagship-adjacent-next-step`.
- [ ] Record the evidence pattern that should keep the flagship planner on the truthful adjacent lane.

### D2. Advance the next bounded flagship increment

Required:
- `agentkit_cli/spec_engine.py`
- nearest planner/command/workflow surfaces
- focused tests

- [ ] Implement the next deterministic bounded flagship increment implied by `flagship-adjacent-next-step`.
- [ ] Keep the recommendation aligned with the flagship repo-understanding workflow.
- [ ] Update contract-seed output if needed.

### D3. Truthful local planning-surface refresh

Required:
- `.agentkit/source.md`
- `BUILD-TASKS.md`
- `progress-log.md`
- any nearest local planning surfaces touched by the planner output

- [ ] Update local planning surfaces so they describe the new lane truthfully.
- [ ] Keep version and workflow wording consistent with local-only build state.

### D4. Validation and local closeout

Required:
- focused spec regressions
- full suite proof
- `progress-log.md`

- [ ] Run focused spec validation.
- [ ] Run `uv run python -m pytest -q`.
- [ ] Leave the repo clean at the end.
- [ ] Record final local-only closeout truth in `progress-log.md`.

## 4. Test Requirements

- [ ] Reproduce current adjacent planner output before fixing it
- [ ] Focused spec-engine / spec command / spec workflow / main validation
- [ ] Full `uv run python -m pytest -q`
- [ ] All existing tests must still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable.
- If blocked, write `blocker-report-v1.30.0-flagship-adjacent-next-step.md` with the exact failure, attempts, and recommended next move.

## 6. Stop Conditions

- All deliverables checked and validation gates satisfied -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write blocker report
- Scope creep beyond the bounded flagship adjacent lane -> STOP and report the new requirement
