# All-Day Build Contract: agentkit-cli v1.29.0 flagship self-advance

Status: In Progress
Date: 2026-04-21
Owner: OpenClaw sub-agent execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Teach the flagship `agentkit spec` flow to recognize when `flagship-post-closeout-advance` is already shipped or truthfully local release-ready, stop re-emitting that lane, and promote the next honest flagship recommendation from current repo truth.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Re-run the required validation from the current tree before any completion claim.
4. Verify the stale planner output from current repo truth before changing behavior.
5. Keep the work inside flagship planner progression logic, nearest tests, and truthful local planning surfaces.
6. Never reopen the already shipped `flagship-concrete-next-step` or `flagship-post-closeout-advance` behavior lanes.
7. No remote push, tag, publish, or external mutation from this repo state.
8. Commit after each completed deliverable cluster, not only at the end.
9. If stuck on the same issue for 3 attempts, stop and write a blocker report.
10. Read existing planning/report surfaces before mutating them.

## 3. Feature Deliverables

### D1. Reproduce and ground the stale planner state

Required:
- `.agentkit/source.md`
- `BUILD-TASKS.md`
- `progress-log.md`

- [ ] Prove the current repo is already shipped for `v1.28.0`.
- [ ] Prove `agentkit spec` still recommends `flagship-post-closeout-advance`.
- [ ] Record the exact evidence pattern that should suppress replay.

### D2. Advance the flagship recommendation logic

Required:
- `agentkit_cli/spec_engine.py`
- nearest spec command/workflow surfaces
- focused tests

- [ ] Implement deterministic suppression for already-closed `flagship-post-closeout-advance`.
- [ ] Promote one fresh adjacent flagship recommendation and contract seed.
- [ ] Keep the recommendation aligned with the flagship repo-understanding workflow.

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

- [ ] Reproduce current stale planner output before fixing it
- [ ] Focused spec-engine / spec command / spec workflow / main validation
- [ ] Full `uv run python -m pytest -q`
- [ ] All existing tests must still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable.
- If blocked, write `blocker-report-v1.29.0-flagship-self-advance.md` with the exact failure, attempts, and recommended next move.

## 6. Stop Conditions

- All deliverables checked and validation gates satisfied -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write blocker report
- Scope creep beyond flagship planner self-advance -> STOP and report the new requirement
