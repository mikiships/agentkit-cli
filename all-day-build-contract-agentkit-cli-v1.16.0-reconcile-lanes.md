# All-Day Build Contract: agentkit-cli v1.16.0 reconcile lane state

Status: Blocked at closeout
Date: 2026-04-20
Owner: OpenClaw sub-agent execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build a deterministic `agentkit reconcile` workflow that closes the current gap after `observe` and `supervise`. Today the lane can tell you what happened and what is locally ready, but the human still has to manually restitch that back into an updated execution plan. This pass should consume saved launch, observe, and supervise artifacts plus local lane state, then emit one stable reconciliation packet that says what is complete, what must relaunch, what is newly unblocked, and what the next safe execution order is.

This contract can be marked complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside `/Users/mordecai/repos/agentkit-cli-v1.16.0-reconcile-lanes`.
7. Commit after each completed deliverable, not just at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not refactor unrelated commands or rename existing packet formats unless the contract requires it.
10. Read the current `launch`, `observe`, and `supervise` docs/tests before writing code.
11. Do not push, tag, publish, or claim shipped state. End at truthful local release-ready or a documented blocker.

## 3. Feature Deliverables

### D1. Reconcile engine and schema

Build the deterministic reconcile engine that reads saved launch/observe/supervise artifacts plus local lane evidence and produces a stable reconciliation model.

Required:
- `agentkit_cli/reconcile.py`
- any supporting schema/types modules the command needs

- [x] Load the latest saved launch packet and lane metadata without guessing missing paths
- [x] Load observe and supervise artifacts when present, and degrade cleanly when one side is missing
- [x] Classify each lane into reconciliation buckets such as complete, relaunch-ready, still-running, blocked, drifted, or needs-human-review
- [x] Compute the next safe execution ordering, preserving serialization groups and dependency gates
- [x] Tests for D1

### D2. CLI command and rendered outputs

Add a first-class `agentkit reconcile` command with deterministic markdown and JSON output plus packet-directory writing.

Required:
- `agentkit_cli/commands/reconcile_cmd.py`
- `agentkit_cli/main.py`

- [x] Add `agentkit reconcile` CLI wiring with parity to the recent workflow commands
- [x] Support human-readable output, `--json`, and `--output-dir`
- [x] Write stable `reconcile.md`, `reconcile.json`, and per-lane reconciliation packets under `lanes/`
- [x] Surface explicit next actions and relaunch ordering instead of vague summaries
- [x] Tests for D2

### D3. Workflow semantics and edge cases

Make the command trustworthy on the failure modes the current orchestration layer actually hits.

Required:
- `tests/test_reconcile_workflow.py`
- fixture updates under `tests/fixtures/` as needed

- [x] Cover newly unblocked serialized lanes after a prior lane completes
- [x] Cover dirty or drifted worktrees that should not auto-advance
- [x] Cover missing observe or missing supervise artifacts without crashing
- [x] Cover lanes whose launch packet exists but no completion evidence was saved
- [x] Cover relaunch-ready vs human-review-required distinctions

### D4. Docs and release-ready surfaces

Document the new lane in the repo’s shipped workflow story and update the local release-ready surfaces truthfully for `1.16.0`.

Required:
- `README.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `FINAL-SUMMARY.md`
- `progress-log.md`
- version metadata surfaces already used in this repo

- [x] Document where `reconcile` fits after `observe` and `supervise`
- [x] Add concrete examples for markdown/JSON or output-dir usage
- [x] Update versioned local release-ready surfaces for `1.16.0`
- [x] Record deliverable completion and validation honestly in `progress-log.md`

### D5. Validation and closeout

Finish with a truthful clean local release-ready repo or a blocker report.

Required:
- repo-local validation/report files

- [x] Run focused reconcile slices
- [x] Run adjacent workflow slices that exercise `launch -> observe -> supervise -> reconcile`
- [x] Run the full suite and fix truthful regressions instead of weakening tests
- [x] Run `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.16.0-reconcile-lanes`
- [x] Run `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.16.0-reconcile-lanes`
- [x] Run `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.16.0-reconcile-lanes`
- [x] Leave the repo clean except intentional contract/report artifacts
- [x] Final summary when all deliverables are done or stopped

## 4. Test Requirements

- [x] Unit tests for the reconcile engine and command rendering
- [x] Integration coverage for the full `launch -> observe -> supervise -> reconcile` workflow
- [x] Edge cases: missing observe packet, missing supervise packet, dirty worktree, detached head, serialized lane unblocked by prior completion, relaunch-needed lane with stale packet
- [x] All existing tests must still pass

## 5. Reports

- [x] Write progress to `progress-log.md` after each deliverable
- [x] Include what was built, what tests pass, what is next, and any blockers
- [x] Before trusting any release/status narrative, run `scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.16.0-reconcile-lanes`, then run `scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.16.0-reconcile-lanes`
- [x] Before final summary, run `scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.16.0-reconcile-lanes`
- [x] If the branch cannot reach truthful local release-ready state, write `blocker-report-v1.16.0-reconcile-lanes.md`

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on the same issue -> STOP, write blocker report
- Scope creep detected, new requirements discovered, or the command needs a different product shape -> STOP, report what changed
- All tests passing but deliverables remain -> continue to the next deliverable

## 7. Closeout resolution

- The child sandbox blocker turned out to be environmental, not product-level.
- Parent-session rerun of the previously blocked subset: `./.venv/bin/python -m pytest -q tests/test_doctor.py tests/test_serve_sse.py tests/test_webhook_d1.py` -> `101 passed in 27.39s`
- Parent-session full suite rerun: `./.venv/bin/python -m pytest -q tests/` -> `4949 passed, 1 warning in 163.63s (0:02:43)`
- Current truth: this branch is now truthfully local `RELEASE-READY`, and final closeout should proceed from the parent session environment rather than the restricted child sandbox.
