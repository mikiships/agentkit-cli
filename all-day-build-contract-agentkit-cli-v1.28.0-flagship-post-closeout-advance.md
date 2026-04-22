# All-Day Build Contract: agentkit-cli v1.28.0 flagship post-closeout advance

Status: In Progress
Date: 2026-04-21
Owner: OpenClaw sub-agent execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Teach the flagship self-spec flow to detect that the shipped `flagship-concrete-next-step` lane is already complete in the current repo, stop recommending the just-shipped v1.27.0 work, and advance to one fresh adjacent recommendation with updated flagship source truth. This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New behavior must land with docs and truthful local report updates in the same pass.
5. CLI outputs must remain deterministic and schema-backed.
6. Never modify files outside `/Users/mordecai/repos/agentkit-cli-v1.28.0-flagship-post-closeout-advance`.
7. Commit after each completed deliverable, not only at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not refactor unrelated surfaces or reopen already-shipped prerequisite work.
10. Read existing spec tests, source surfaces, and release-truth docs before editing.
11. No push, tag, publish, or remote mutation.

## 3. Feature Deliverables

### D1. Replay detection for closed flagship-next-step lanes

Add planner logic that detects when the flagship repo has already completed the active `flagship-concrete-next-step` objective through shipped or truthful local-release-ready evidence, then suppresses replay of that same lane.

Required:
- `agentkit_cli/spec.py`
- `agentkit_cli/commands/spec_cmd.py`
- nearest supporting helpers already used for shipped/local-ready truth

- [ ] Identify the current replay path and ground it in repo truth instead of generic fallback heuristics.
- [ ] Add deterministic detection for the already-finished v1.27.0 flagship lane.
- [ ] Keep recommendation ranking deterministic when replay suppression activates.
- [ ] Tests for D1.

### D2. Fresh adjacent recommendation and contract seed advancement

Once replay is detected, promote one new bounded adjacent recommendation and contract seed instead of recycling the just-shipped lane. The new recommendation must be concrete enough to open the next build without human reinterpretation.

Required:
- `agentkit_cli/spec.py`
- `tests/test_spec_cmd.py`
- `tests/test_spec_workflow.py`

- [ ] Emit a new primary recommendation kind, title, slug, objective, why-now, and scope boundaries that reflect post-v1.27.0 truth.
- [ ] Update contract-seed output so it points at the fresh next lane rather than the already-shipped one.
- [ ] Preserve truthful alternates without letting them outrank the new flagship lane.
- [ ] Tests for D2.

### D3. Flagship source and local closeout truth updates

Update the flagship source or nearest truthful local surfaces so the repo no longer names the already-finished v1.27.0 objective as the active flagship objective.

Required:
- `.agentkit/source.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `FINAL-SUMMARY.md`
- `progress-log.md`
- version surfaces for local release-ready truth

- [ ] Advance the flagship source objective to match the new adjacent lane.
- [ ] Reconcile local build/report surfaces so they describe v1.28.0 local build truth, not shipped v1.27.0 truth.
- [ ] Keep release state explicitly local-only.
- [ ] Tests or verification notes for D3 captured in progress log.

### D4. Focused regression coverage and end-to-end validation

Prove the replay case and the new adjacent recommendation through focused tests plus a full-suite closeout pass.

Required:
- `tests/test_spec_cmd.py`
- `tests/test_spec_workflow.py`
- `tests/test_main.py`
- any nearest regression files touched by the engine changes

- [ ] Add regression coverage for the post-v1.27.0 replay case.
- [ ] Verify `agentkit spec . --json` from this worktree now emits the new adjacent lane instead of `flagship-concrete-next-step`.
- [ ] Run focused spec-command/workflow validation.
- [ ] Run full suite and leave the repo clean and local release-ready.

## 4. Test Requirements

- [ ] Unit tests for each deliverable
- [ ] Integration coverage for the flagship `spec` workflow from current repo truth
- [ ] Edge cases: shipped-vs-local-ready detection, truthful alternates, deterministic contract seed output, no replay of the just-shipped lane
- [ ] All existing tests must still pass
- [ ] Final command-path proof recorded in `progress-log.md`

## 5. Reports

- Write progress to `progress-log.md` after each deliverable.
- Include what was built, what tests passed, what is next, and any blockers.
- Before trusting release/status narrative, run `scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.28.0-flagship-post-closeout-advance`.
- Run `scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.28.0-flagship-post-closeout-advance` before final summary.
- Run `scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.28.0-flagship-post-closeout-advance` before final summary.
- If blocked, write `blocker-report-v1.28.0-flagship-post-closeout-advance.md` with exact failure, attempts, and recommended next move.

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP and write blocker report
- Scope creep discovered beyond replay suppression plus adjacent advancement -> STOP and report the new requirement
- All tests passing but any deliverable unchecked -> continue until the deliverable is complete
- Any push, tag, publish, or remote mutation would be required -> STOP and leave the repo in truthful local release-ready state
