# All-Day Build Contract: agentkit-cli v1.12.0 materialize worktrees

Status: DONE
Date: 2026-04-20
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build a deterministic `agentkit materialize` workflow that consumes a saved `stage` plan and turns it into real local git worktrees plus lane-specific handoff directories. The concrete outcome is: after `source -> audit -> map -> contract -> bundle -> taskpack -> clarify -> resolve -> dispatch -> stage`, a user can run one more command and have the planned worktrees created locally with deterministic branch names, deterministic output paths, copied lane packets, and clear safety behavior around collisions or serialized lanes.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory except through the intentional local test fixtures needed to validate worktree creation.
7. Commit after each completed deliverable, not at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not refactor, restyle, or improve code outside the deliverables.
10. Read existing stage, dispatch, resolve, and taskpack tests/docs before changing anything.
11. `agentkit materialize` must only create local git worktrees and local handoff files. It must not spawn agents, publish anything, or mutate remote repositories.
12. Default safety matters: support `--dry-run`, refuse unsafe collisions by default, and preserve serialized lanes instead of creating fake parallel worktrees for overlapping ownership in the same phase.

## 3. Feature Deliverables

### D1. Materialization engine

Add a deterministic engine that consumes `stage.json` plus lane packets and plans actual local worktree creation.

Required:
- `agentkit_cli/materialize.py`
- any shared schema/helpers needed under `agentkit_cli/`

- [x] Build a materialization data model for worktree creation actions, branch targets, output paths, and lane packet copies
- [x] Derive deterministic worktree roots from the stage manifest plus CLI options
- [x] Preserve serialized lane ordering and explicitly mark lanes that must wait instead of materializing everything at once
- [x] Support dry-run planning without touching git state
- [x] Tests for D1

### D2. CLI command + execution wiring

Expose the engine through a first-class CLI that can print markdown, emit stable JSON, dry-run safely, and perform real local materialization.

Required:
- `agentkit_cli/commands/materialize_cmd.py`
- `agentkit_cli/main.py`

- [x] Add `agentkit materialize` CLI wiring
- [x] Support `--target`, `--json`, `--output`, `--output-dir`, `--worktree-root`, and `--dry-run`
- [x] Execute actual `git worktree add` flows for eligible lanes when not in dry-run
- [x] Refuse collisions or pre-existing path/branch conflicts with explicit errors unless the contract defines a safe behavior
- [x] Tests for D2

### D3. Lane packet seeding and safety behavior

Each created worktree should receive the lane packet and enough metadata to hand to a builder cleanly.

Required:
- materialization helpers under `agentkit_cli/`
- docs/examples updated in repo surfaces

- [x] Copy or write lane-specific handoff artifacts into deterministic per-worktree locations
- [x] Include target-aware notes for `generic`, `codex`, and `claude-code`
- [x] Preserve serialization-group metadata so later orchestration can see what must wait
- [x] Ensure single-lane plans work cleanly without extra scaffolding
- [x] Tests for D3

### D4. Regression + edge-case coverage

Prove the feature works on the real handoff path and fails safely around git/worktree edge cases.

Required:
- `tests/test_materialize*.py` and any touched workflow tests

- [x] Integration test covering `stage -> materialize`
- [x] Edge case: dry-run produces stable action plan without mutating git state
- [x] Edge case: serialized lanes do not materialize early
- [x] Edge case: existing branch or path collision fails cleanly
- [x] Edge case: deterministic naming remains stable across runs
- [x] Full-suite validation remains green

### D5. Docs, reports, and release-readiness surfaces

Ship the feature as a release-ready `v1.12.0` branch with coherent docs and build-report surfaces.

Required:
- `README.md`
- `CHANGELOG.md`
- `progress-log.md`
- `BUILD-REPORT.md`
- version surface(s) for `1.12.0`

- [x] Document where materialize sits in the full handoff lane
- [x] Add examples for dry-run and real local materialization
- [x] Update changelog/build report/progress log/version metadata to `1.12.0`
- [x] Leave the repo release-ready locally with clean status except the intentional contract file
- [x] Tests for D5 noted in reports

## 4. Test Requirements

- [x] Unit tests for each deliverable
- [x] Integration test covering the `stage -> materialize` workflow
- [x] Edge cases: dry-run stability, serialized lanes, collisions, stable naming, target-specific packet seeding
- [x] All existing tests must still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what is next, and any blockers
- Before trusting any release/status narrative, run `scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.12.0-materialize-worktrees` first so current handoff state, temporal drift, learned rules, and recent router anomalies are in view, then run `scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.12.0-materialize-worktrees`
- Before final summary, run `scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.12.0-materialize-worktrees`
- Final summary when all deliverables are done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on the same issue -> STOP, write blocker report
- Scope creep detected, for example actual agent spawning or remote repo mutation -> STOP, report what is new
- All tests passing but deliverables remain -> continue to next deliverable
