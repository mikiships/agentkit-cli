# All-Day Build Contract: agentkit-cli v1.15.0 supervise restack

Status: Active
Date: 2026-04-20
Owner: OpenClaw build-loop restack pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build the next honest unreleased line for `agentkit supervise` on top of the already shipped `v1.14.0` observe chronology.

`v1.14.0` is already shipped from `feat/v1.14.0-observe-lanes`, so the older `feat/v1.14.0-supervise-lanes` branch is blocked by chronology and cannot truthfully publish as `v1.14.0`. This pass must inspect the shipped base plus the blocked supervise branch, restack the supervise feature onto `/Users/mordecai/repos/agentkit-cli-v1.15.0-supervise-restack`, update all version and release surfaces to truthful unreleased `v1.15.0`, and leave the repo in local `RELEASE-READY` or precise blocker state only.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end unless a real blocker is documented precisely.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must remain deterministic and schema-backed where specified.
6. Never modify files outside this project directory.
7. Commit after each completed deliverable, not only at the end.
8. If the previous supervise commits cannot be restacked cleanly, stop and write a blocker report instead of forcing the branch.
9. Do not push, tag, publish, or mutate remotes.
10. Read existing docs and adjacent tests for `dispatch`, `stage`, `materialize`, `launch`, and `observe` before editing release surfaces.
11. Keep the safety boundary explicit: supervision remains local-only and observational by default.
12. Release/report language must stay truthful: this branch is an unreleased `v1.15.0` restack, not shipped.

## 3. Feature Deliverables

### D0. Restack contract and chronology audit

- [ ] Inspect shipped base `55c6467` and blocked supervise branch deltas before mutation
- [ ] Record the truthful restack objective and guardrails in this contract
- [ ] Commit the contract as the first deliverable

### D1. Restack supervision engine and packet surfaces

Required:
- `agentkit_cli/supervise.py`
- any supporting tests or helpers needed for deterministic output

- [ ] Bring the supervision engine onto the shipped base cleanly
- [ ] Preserve stable states: `ready`, `running`, `waiting`, `blocked`, `completed`, `drifted`
- [ ] Preserve deterministic markdown/JSON packet rendering and newly-unblocked dependency handling
- [ ] Keep observe surfaces intact on the shipped base
- [ ] Commit the completed engine restack

### D2. Restack `agentkit supervise` CLI wiring

Required:
- `agentkit_cli/commands/supervise_cmd.py`
- `agentkit_cli/main.py`

- [ ] Add `agentkit supervise` with `--json`, `--output`, `--output-dir`, `--launch-path`, and stable format handling
- [ ] Keep command registration truthful on top of the shipped observe line
- [ ] Commit the completed CLI restack

### D3. Workflow and regression coverage

Required:
- supervise workflow and command/engine regression tests

- [ ] Bring over focused engine/command/workflow coverage for supervise
- [ ] Verify the `resolve -> dispatch -> stage -> materialize -> launch -> supervise` lane on this restacked base
- [ ] Commit the completed regression restack

### D4. Truthful v1.15.0 release-readiness surfaces

Required:
- `README.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.15.0.md`
- `FINAL-SUMMARY.md`
- `progress-log.md`
- version surfaces such as `pyproject.toml`, `agentkit_cli/__init__.py`, `tests/test_main.py`, `uv.lock`

- [ ] Update docs so the supported handoff lane ends with `supervise` after `observe`
- [ ] Bump local version surfaces from shipped `1.14.0` to unreleased `1.15.0`
- [ ] Mark reports as local `RELEASE-READY` only, with no shipped claims
- [ ] Commit the completed docs/version restack

### D5. Validation, recall, contradiction, and hygiene closeout

- [ ] Run targeted supervise slices
- [ ] Run broader adjacent workflow coverage
- [ ] Run the full test suite
- [ ] Run recall, contradiction, and hygiene checks before final status
- [ ] Leave the repo in clean local `RELEASE-READY` or precise blocker state

## 4. Test Requirements

- [ ] Unit tests for supervise engine and command
- [ ] Integration coverage for `resolve -> dispatch -> stage -> materialize -> launch -> supervise`
- [ ] Adjacent observe/launch/materialize/stage/dispatch/resolve surfaces stay green
- [ ] Full suite passes before final `RELEASE-READY`

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what changed, what passed, what remains next, and any blocker truth
- Before trusting the final release/status narrative, run repo-local recall / contradiction / hygiene checks and record results honestly
- Final summary only when all deliverables are done or a real blocker remains

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- Previous supervise restack cannot be applied cleanly without breaking shipped observe surfaces -> STOP and write blocker report
- 3 consecutive failed attempts on the same issue -> STOP and write blocker report
- Scope creep detected beyond local supervise restack and release-readiness prep -> STOP and report the new requirement
