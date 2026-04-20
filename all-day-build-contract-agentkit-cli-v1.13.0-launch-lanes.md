# All-Day Build Contract: agentkit-cli v1.13.0 launch lanes

Status: In Progress
Date: 2026-04-20
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit launch` as the next adjacent execution layer after `materialize`. Today `materialize` creates real local worktrees and seeded handoff packets, but users still have to manually figure out the exact Codex or Claude Code commands to start each lane, and serialized waiting lanes have no first-class launch surface. This pass should add a deterministic post-materialize launch workflow that reads saved materialize artifacts, derives target-aware launch commands and per-lane launch packets, supports dry-run and machine-readable output, and can optionally kick off eligible local builder commands without touching remotes.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable, not only at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or improve unrelated commands.
10. Read existing tests and docs for `taskpack`, `dispatch`, `stage`, and `materialize` before writing new code.
11. Keep the safety boundary explicit: no git push, tag, publish, or remote mutation in this feature pass.
12. Any optional local execution path must remain opt-in and refuse unsafe missing-artifact states cleanly.

## 3. Feature Deliverables

### D1. Schema-backed launch planning engine

Build a deterministic launch planner that consumes saved `materialize.json` output and per-lane packet directories, identifies launchable versus waiting lanes, and emits stable launch plans for supported targets.

Required:
- `agentkit_cli/launch.py`
- any schema/types helpers needed for stable JSON output

- [ ] Read saved materialize artifacts and derive eligible launch lanes
- [ ] Preserve serialized waiting behavior instead of pretending blocked lanes can launch early
- [ ] Emit target-aware launch command plans for `generic`, `codex`, and `claude-code`
- [ ] Include explicit reasons when a lane is waiting, blocked, or missing required artifacts
- [ ] Tests for D1

### D2. `agentkit launch` CLI surface

Add a first-class CLI command that renders markdown and JSON launch plans and can optionally execute eligible local builder commands when explicitly requested.

Required:
- `agentkit_cli/commands/launch_cmd.py`
- `agentkit_cli/main.py`

- [ ] Add `agentkit launch` with `--target`, `--json`, `--output`, and `--output-dir`
- [ ] Support a dry-run/default planning path with no subprocess launch side effects
- [ ] Support an explicit opt-in local execution flag for eligible lanes only
- [ ] Fail clearly on missing materialize artifacts, missing worktrees, or target/tool mismatches
- [ ] Tests for D2

### D3. Launch packet and script artifacts

Write portable launch artifacts so users and orchestrators can inspect or reuse the exact launch commands without reconstructing them from prose.

Required:
- launch markdown and JSON outputs
- per-lane launch packet files under the output directory

- [ ] Emit top-level `launch.md` and `launch.json`
- [ ] Emit per-lane launch packets with worktree path, handoff path, command, status, and waiting notes
- [ ] Write target-aware helper scripts or command files when useful for local execution reuse
- [ ] Keep single-lane plans clean while preserving multi-lane serialization metadata
- [ ] Tests for D3

### D4. Regression and edge-case coverage

Cover the real handoff lane from `resolve -> dispatch -> stage -> materialize -> launch`, plus failure states around collisions, missing tools, and waiting lanes.

Required:
- regression tests across launch workflow surfaces

- [ ] End-to-end workflow coverage for the full post-materialize launch lane
- [ ] Edge cases: waiting lane preserved, missing worktree, missing materialize packet, unsupported target, execution flag without required tool
- [ ] Verify deterministic JSON fields and stable command rendering
- [ ] All existing related tests continue to pass

### D5. Docs and release-readiness surfaces

Update docs and local report surfaces so the supported handoff lane now ends with `launch` after `materialize`, while keeping this pass strictly local release-ready only.

Required:
- `README.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `FINAL-SUMMARY.md`
- `progress-log.md`

- [ ] Document `agentkit launch` usage, dry-run path, and optional execution behavior
- [ ] Update supported full handoff lane examples through `launch`
- [ ] Record validation, contradiction-check, and hygiene-check results
- [ ] Leave the repo in truthful local `RELEASE-READY` or blocker state

## 4. Test Requirements

- [ ] Unit tests for each deliverable
- [ ] Integration test covering `resolve -> dispatch -> stage -> materialize -> launch`
- [ ] Edge cases: waiting lanes, missing worktree, missing materialize packet, unsupported target, missing tool on execute path
- [ ] All existing tests must still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what is next, and any blockers
- Before trusting any release/status narrative, run `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.13.0-launch-lanes`
- Then run `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.13.0-launch-lanes`
- Before final summary, run `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.13.0-launch-lanes`
- Final summary only when all deliverables are done or a real blocker remains

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP, write blocker report
- Scope creep detected, for example full supervision/monitoring beyond launch planning and optional execution -> STOP, report the new requirement
- All tests passing but deliverables remain -> continue to next deliverable
