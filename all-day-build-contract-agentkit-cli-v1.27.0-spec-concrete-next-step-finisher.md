# All-Day Build Contract — agentkit-cli v1.27.0 spec concrete next step finisher

Status: In Progress
Date: 2026-04-21
Owner: OpenClaw sub-agent finisher
Scope type: Deliverable-gated closeout

## 1. Objective

Finish the in-progress `v1.27.0 spec concrete next step` lane from the current worktree state, prove the flagship repo now emits a concrete adjacent recommendation instead of the generic `subsystem-next-step` fallback, and leave the repo in truthful local-only state with clean validation or a precise blocker.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when every checklist item below is checked.
3. Work only inside `/Users/mordecai/repos/agentkit-cli-v1.27.0-spec-concrete-next-step`.
4. Do not push, tag, publish, or mutate any remote surface.
5. Do not broaden scope beyond the current `spec concrete next step` lane.
6. Read the existing changed files and tests before editing.
7. Commit after each completed deliverable, not just at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not reopen already-shipped canonical-source, adjacent-grounding, or shipped-truth-sync work except where needed for this planner closeout.
10. Before trusting any status prose, reconcile it against repo truth.

## 3. Deliverables

### D1. Ground current implementation state

Review the current dirty tree, understand what the earlier builder already changed, and either keep or correct those edits so the planner logic is coherent and bounded.

Required files:
- `agentkit_cli/spec_engine.py`
- `tests/test_spec_cmd.py`
- `tests/test_spec_workflow.py`
- `tests/test_spec_engine.py`
- `BUILD-TASKS.md`

- [ ] Confirm what concrete recommendation the current edits are aiming to produce
- [ ] Tighten or fix the implementation if the recommendation is still vague, stale, or mis-grounded
- [ ] Ensure test coverage matches the intended flagship post-v1.26.0 case

### D2. Prove the concrete next-step behavior

Run focused validation and direct command-path proof from this repo, then verify the primary recommendation and contract seed are specific enough to open the next lane without human reinterpretation.

- [ ] Run `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`
- [ ] Run `uv run python -m agentkit_cli.main spec . --json`
- [ ] Confirm the primary recommendation is concrete, bounded, and evidence-backed

### D3. Truthful local closeout

Update the local lane surfaces so they match the repo truth, then leave the worktree clean except for intentional contract artifacts.

Required files:
- `progress-log.md`
- `BUILD-TASKS.md`
- `BUILD-REPORT.md`
- `FINAL-SUMMARY.md`
- version/changelog surfaces only if actually needed for truthful local-only state

- [ ] Update progress/report surfaces to describe `v1.27.0 spec concrete next step` truthfully
- [ ] Run `uv run python -m pytest -q`
- [ ] Run `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.27.0-spec-concrete-next-step`
- [ ] Run `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.27.0-spec-concrete-next-step`
- [ ] Leave the tree in truthful `RELEASE-READY (LOCAL-ONLY)` or write an explicit blocker report

## 4. Validation Requirements

- Focused tests: `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`
- Direct behavior proof: `uv run python -m agentkit_cli.main spec . --json`
- Full suite: `uv run python -m pytest -q`
- Contradiction scan: `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.27.0-spec-concrete-next-step`
- Hygiene scan: `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.27.0-spec-concrete-next-step`

## 5. Reports

- Write progress to `progress-log.md` after each deliverable or blocker
- Summarize what changed, what tests passed, and what remains
- Final summary must state one of: `RELEASE-READY (LOCAL-ONLY)` or `BLOCKED`, with evidence

## 6. Stop Conditions

- All deliverables checked and all validation gates pass -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write blocker report
- Scope creep discovered -> STOP and document the new requirement
- Full suite passes but local truth/report surfaces still disagree -> continue until reconciled
