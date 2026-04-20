# All-Day Build Contract: agentkit-cli v1.9.0 resolve loop

Status: In Progress
Date: 2026-04-20
Owner: OpenClaw subagent execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build a deterministic `agentkit resolve` workflow that closes the loop after `agentkit clarify`. The current lane now reaches `source -> audit -> map -> contract -> bundle -> taskpack -> clarify`, but users still have to manually merge answers and decisions back into an execution-ready handoff. This pass should remove that manual reconciliation step by consuming a clarification artifact plus an answers file and emitting a stable resolved packet with answered questions folded in, remaining blockers surfaced explicitly, and updated execution guidance.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside `/Users/mordecai/repos/agentkit-cli-v1.9.0-resolve-loop`.
7. Commit after each completed deliverable, not only at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not refactor or restyle unrelated code.
10. Read existing clarify, taskpack, bundle, contract, and source-audit code/tests before writing new code.

## 3. Feature Deliverables

### D1. Deterministic resolve engine + schema

Add a first-class resolve engine that consumes clarify/taskpack-ready surfaces plus explicit answers and emits a stable resolved model. The model should record which questions were resolved, which remain open, which assumptions were confirmed or superseded, and whether execution can now proceed.

Required:
- `agentkit_cli/resolve.py`
- any supporting schema/helpers needed for stable resolve rendering
- tests covering deterministic structure and ordering

- [ ] Implement deterministic resolve assembly from clarify output plus an answers file
- [ ] Include explicit sections for resolved questions, remaining blockers, confirmed assumptions, superseded assumptions, and updated execution recommendation
- [ ] Support stable JSON output with schema-backed keys and deterministic ordering
- [ ] Tests for D1

### D2. CLI workflow + actionable rendering

Expose the new workflow through the CLI so a user can turn answers into a resolved execution packet without glue code.

Required:
- `agentkit_cli/commands/resolve_cmd.py`
- CLI wiring in main/help surfaces
- tests for text/JSON/output-file flows

- [ ] Add `agentkit resolve <path> --answers <file>` CLI entrypoint
- [ ] Support markdown and JSON rendering plus output-file/output-dir flows
- [ ] Make the output useful to both humans and upstream orchestrators
- [ ] Tests for D2

### D3. End-to-end resolution loop validation

Prove the full `source -> audit -> map -> contract -> bundle -> taskpack -> clarify -> resolve` lane works and fails clearly when answers are incomplete or contradictory.

Required:
- focused end-to-end workflow tests
- incomplete-answer / contradiction coverage
- docs/report updates for the new lane

- [ ] Add focused end-to-end tests for the full workflow including resolve
- [ ] Add failure-path tests for incomplete or contradictory answers
- [ ] Update README, changelog, and build-report/progress surfaces for `1.9.0`
- [ ] Tests for D3

### D4. Release-readiness pass

Leave the worktree in a truthful local release-ready state, not partially updated. Version metadata, changelog, docs, build report, and progress log must all agree.

Required:
- `pyproject.toml`
- `agentkit_cli/__init__.py`
- `uv.lock`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.9.0.md`
- `progress-log.md`

- [ ] Bump release metadata to `1.9.0`
- [ ] Reconcile docs and report surfaces to one local release-ready story
- [ ] Run contradiction + hygiene checks on the final repo state
- [ ] Tests/checks for D4

## 4. Test Requirements

- [ ] Unit tests for resolve engine and renderers
- [ ] CLI tests for human-readable and JSON/output flows
- [ ] Integration test covering `source -> source-audit -> map -> contract -> bundle -> taskpack -> clarify -> resolve`
- [ ] Edge cases: missing answers file, partial answers, contradictory answers, deterministic output ordering, correct post-resolution execution recommendation
- [ ] All existing tests must still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include what was built, exact tests that passed, what remains, and any blockers
- Before trusting any release/status narrative, run:
  - `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.9.0-resolve-loop`
  - `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.9.0-resolve-loop`
- Before final summary, run:
  - `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.9.0-resolve-loop`
- Final summary when all deliverables are done or the pass stops

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write a blocker report
- Scope creep detected beyond clarification-resolution generation -> STOP and report the newly discovered requirement
- Any contradiction remains unresolved between tests and report surfaces -> STOP until source-of-truth state is reconciled
