# All-Day Build Contract: agentkit-cli v1.14.0 observe lane outcomes

Status: In Progress
Date: 2026-04-20
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build a deterministic `agentkit observe` workflow that closes the gap after `agentkit launch`. Right now the handoff lane can map, contract, bundle, taskpack, clarify, resolve, dispatch, stage, materialize, and launch, but once builders start there is no first-class way to collect lane status back into one stable artifact. This build should consume saved `launch` artifacts and local lane metadata, classify each lane as observed success, observed failure, still running, waiting, blocked, or unknown, and emit a reusable markdown/JSON observe packet that lets an orchestrator decide what to do next without re-reading scattered worktrees.

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
10. Read existing tests and docs before writing new code.
11. Scope is observe-only. Do not add retry, resume, spawn, publish, or remote-mutation behavior in this pass.

## 3. Feature Deliverables

### D1. Observe engine and schema-backed lane status model

Create the core `agentkit observe` engine that loads a saved `launch.json` artifact, inspects the referenced lane worktrees and launch packet files, and produces one deterministic observe plan. The plan must classify each lane using explicit status values that distinguish completed success, completed failure, in-progress execution, waiting-on-dependency, blocked-from-launch, and unknown/no-result states. Preserve upstream handoff context so an orchestrator can see the lane title, owned paths, dependencies, launch command metadata, and the exact evidence used for the observed status.

Required:
- `agentkit_cli/observe.py`
- any shared schema/model surface needed for observe JSON stability

- [ ] Load saved `launch` artifacts from either the project root or a supplied observe/launch packet path
- [ ] Define deterministic observe status values and evidence fields per lane
- [ ] Inspect local lane evidence without guessing, using only files and process/result artifacts available from the saved launch/worktree state
- [ ] Preserve upstream waiting and blocked lanes as waiting/blocked instead of collapsing them into unknown
- [ ] Tests for D1

### D2. CLI wiring and stable markdown/JSON rendering

Add a first-class `agentkit observe` command with stable markdown and JSON output. The command should support human-readable review plus machine-readable orchestration. It must fail clearly when the saved launch artifact is missing, malformed, or target-incompatible.

Required:
- `agentkit_cli/commands/observe_cmd.py`
- `agentkit_cli/main.py`
- help/CLI registration surfaces already used by adjacent commands

- [ ] Add CLI command wiring with target-aware loading from saved launch artifacts
- [ ] Render stable markdown summary plus schema-stable JSON
- [ ] Surface lane-by-lane evidence, overall summary counts, and recommended next actions
- [ ] Clear failures for missing launch packets, mismatched targets, or unusable local evidence
- [ ] Tests for D2

### D3. Portable observe packet directory output

Match the adjacent workflow pattern by letting users write `observe.md`, `observe.json`, and per-lane packet files under `lanes/<lane-id>/`. The output should be reusable by an orchestrator or follow-on tooling and must preserve deterministic filenames and shapes.

Required:
- observe packet writer surface in the new engine/command
- packet directory tests

- [ ] Support top-level `--output` and `--output-dir` behavior consistent with adjacent handoff commands
- [ ] Write top-level `observe.md` and `observe.json`
- [ ] Write per-lane `observe.md` and `observe.json` packets
- [ ] Include explicit evidence and recommended next step in each lane packet
- [ ] Tests for D3

### D4. End-to-end workflow coverage and edge cases

Prove the full `resolve -> dispatch -> stage -> materialize -> launch -> observe` lane works and that observe does not hallucinate results when artifacts are partial or stale.

Required:
- focused regression tests under `tests/`

- [ ] End-to-end workflow test covering a successful observed lane from saved launch artifacts
- [ ] Coverage for waiting lanes, blocked lanes, and missing-result lanes
- [ ] Coverage for a failed or incomplete local execution result path
- [ ] Coverage for manual/generic launch targets where process execution is not local-subprocess based
- [ ] Tests for D4

### D5. Docs, reports, and release-ready surfaces for v1.14.0

Document the new command, update the supported handoff story so it no longer ends at launch, and leave the repo in truthful local release-ready state for a later release-completion pass.

Required:
- `README.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `FINAL-SUMMARY.md`
- `progress-log.md`
- version surfaces for `1.14.0`

- [ ] README usage docs for `agentkit observe`
- [ ] CHANGELOG entry and version bump to `1.14.0`
- [ ] BUILD-REPORT, FINAL-SUMMARY, and progress surfaces reconciled to local release-ready truth
- [ ] Run contradiction scan and hygiene check before final summary
- [ ] Commit D5 and leave repo clean except intentional contract/report artifacts

## 4. Test Requirements

- [ ] Unit tests for each deliverable
- [ ] Integration test covering the full `resolve -> dispatch -> stage -> materialize -> launch -> observe` workflow
- [ ] Edge cases: missing launch artifact, target mismatch, waiting lanes, blocked lanes, generic/manual launch targets, incomplete result evidence, failed local execution evidence, and stale or partial per-lane metadata
- [ ] All existing tests must still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what is next, and any blockers
- Before trusting any release or status narrative, run `scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.14.0-observe-lanes` first so current handoff state, temporal drift, learned rules, and recent router anomalies are in view, then run `scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.14.0-observe-lanes` or equivalent contradiction scan
- Before final summary or release claims, run `scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.14.0-observe-lanes`
- Final summary when all deliverables are done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP, write blocker report
- Scope creep detected, including retry/resume/spawn behavior -> STOP, report what is new
- All tests passing but deliverables remain -> continue to next deliverable
