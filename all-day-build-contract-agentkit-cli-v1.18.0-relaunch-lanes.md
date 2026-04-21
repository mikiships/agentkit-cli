# All-Day Build Contract: agentkit-cli v1.18.0 relaunch lanes

Status: In Progress
Date: 2026-04-20
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build a deterministic `agentkit relaunch` workflow on top of the shipped `resume` lane so operators can turn a saved resume packet back into fresh launch-ready artifacts without manually reconstructing which lanes should restart, which must stay waiting, and which still require review. The concrete outcome is a local-only command that consumes saved `resume` output plus upstream lane evidence, emits stable markdown and JSON relaunch artifacts plus per-lane launch packets for eligible lanes, preserves waiting and review-only buckets explicitly, and leaves the repo truthfully local release-ready with tests and docs updated.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable, not at the end.
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or improve code outside the deliverables.
10. Read existing launch, reconcile, and resume tests/docs before writing new code.
11. Stay local-only. No git push, tag, publish, network mutation, or silent agent execution.
12. Do not silently launch builders. If any execution helper exists, it must stay explicit opt-in and clearly marked as local-only.

## 3. Feature Deliverables

### D1. Relaunch engine and schema-backed plan assembly

Build the engine that reads a saved resume artifact, validates the upstream lane state, and deterministically classifies which lanes can be relaunched now versus preserved as waiting, review-only, or completed.

Required:
- `agentkit_cli/relaunch.py`
- `agentkit_cli/resume.py`
- any shared schema/helper surface needed for stable relaunch artifacts

- [ ] Load saved `resume.json` or directory-based resume artifacts from the existing workflow surfaces.
- [ ] Emit a stable relaunch plan with explicit buckets for `relaunch-now`, `waiting`, `review-only`, and `completed`.
- [ ] Carry forward dependency and serialization safety so only lanes that are actually eligible reopen in the same pass.
- [ ] Track relaunch metadata per lane, including why it is eligible now and which upstream evidence it relied on.
- [ ] Tests for D1.

### D2. First-class CLI and artifact writing

Add `agentkit relaunch` as a first-class command that can print markdown, write markdown and JSON, and generate per-lane relaunch packets for eligible lanes without mutating git state.

Required:
- `agentkit_cli/commands/relaunch_cmd.py`
- `agentkit_cli/main.py`
- `tests/test_relaunch_cmd.py`

- [ ] Add CLI wiring with deterministic stdout behavior matching adjacent commands.
- [ ] Support `--json` and `--output-dir` flows that produce stable file layouts.
- [ ] Write per-lane relaunch packets under a deterministic directory shape for lanes in `relaunch-now`.
- [ ] Keep waiting, review-only, and completed lanes visible in summary output instead of dropping them.
- [ ] Tests for D2.

### D3. Relaunch-ready handoff packets

Turn eligible lanes into concrete relaunch-ready handoff artifacts that bridge `resume` back to `launch` semantics without requiring an operator to manually restitch commands.

Required:
- `agentkit_cli/relaunch.py`
- `tests/test_relaunch_engine.py`
- `tests/test_relaunch_workflow.py`

- [ ] Generate deterministic per-lane packet content that names the source resume decision, target lane, worktree path if known, and next runner instructions.
- [ ] Reuse or bridge the shipped launch packet conventions where appropriate instead of inventing a parallel format with avoidable drift.
- [ ] Make the relaunch output clear about what still needs human review before execution.
- [ ] Cover edge cases: missing upstream artifacts, stale lane references, serialized groups, already-completed lanes, and lanes blocked by unresolved review items.
- [ ] Tests for D3.

### D4. Docs, reports, and local release-readiness surfaces

Update docs and repo state so the new relaunch workflow is documented and the branch ends in a truthful local release-ready state for v1.18.0.

Required:
- `README.md`
- `CHANGELOG.md`
- `agentkit_cli/__init__.py`
- `pyproject.toml`
- `BUILD-REPORT.md`
- `FINAL-SUMMARY.md`
- `progress-log.md`

- [ ] Document where `relaunch` fits in the `launch -> observe -> supervise -> reconcile -> resume -> relaunch` continuation loop.
- [ ] Bump version surfaces to `1.18.0` and describe the feature accurately.
- [ ] Update progress and build report surfaces after each deliverable with truthful test status.
- [ ] Leave the repo in a coherent local `RELEASE-READY` state, not shipped.
- [ ] Tests and contradiction scan for D4.

## 4. Test Requirements

- [ ] Unit tests for each deliverable.
- [ ] Integration coverage for the full `resume -> relaunch` workflow.
- [ ] Edge cases: missing resume artifact, malformed lane state, serialized groups, blocked review-only lanes, already-completed lanes, stale worktree paths, and deterministic packet ordering.
- [ ] All existing tests must still pass.
- [ ] Final full suite passes locally.

## 5. Reports

- Write progress to `progress-log.md` after each deliverable.
- Include what was built, what tests pass, what is next, and any blockers.
- Before trusting any release or status narrative, run `scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.18.0-relaunch-lanes` first so current handoff state, temporal drift, learned rules, and recent router anomalies are in view, then run `scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.18.0-relaunch-lanes` or an equivalent contradiction scan.
- Before final summary, run `scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.18.0-relaunch-lanes` and either clean findings or note why they are intentional.
- Write a final summary when all deliverables are done or the pass stops.

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE.
- 3 consecutive failed attempts on same issue -> STOP and write a blocker report.
- Scope creep detected, especially if the feature wants to actually spawn or manage live agents -> STOP and report the new requirement instead of freelancing it.
- All tests passing but deliverables remain -> continue to next deliverable.
