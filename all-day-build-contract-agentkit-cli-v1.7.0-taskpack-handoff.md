# All-Day Build Contract: agentkit-cli v1.7.0 taskpack handoff

Status: In Progress
Date: 2026-04-20
Owner: OpenClaw subagent execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build a deterministic `agentkit taskpack` workflow that turns the shipped `source -> source-audit -> map -> contract -> bundle` lane into an execution-ready handoff packet for coding agents. Today `agentkit bundle` produces the right source artifact, but users still have to manually wrap it into the actual prompt packet they paste into Codex, Claude Code, or a generic coding agent. This pass should remove that manual stitching step by generating a portable packet directory with stable markdown/JSON surfaces, explicit target modes, and crisp gap reporting.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside `/Users/mordecai/repos/agentkit-cli-v1.7.0-taskpack-handoff`.
7. Commit after each completed deliverable, not only at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not refactor or restyle unrelated code.
10. Read existing bundle, contract, map, source-audit, and CLI tests/docs before writing new code.

## 3. Feature Deliverables

### D1. Deterministic taskpack engine + schema

Add a first-class taskpack engine that consumes bundle-ready inputs and emits a stable packet model for execution handoffs. The packet should explicitly separate durable context, execution instructions, and missing-surface warnings so downstream agents do not have to infer structure.

Required:
- `agentkit_cli/taskpack.py`
- any supporting schema/helpers needed for stable packet rendering
- tests covering packet structure and deterministic ordering

- [ ] Implement deterministic taskpack assembly from existing bundle/contract surfaces
- [ ] Include explicit sections for context, task brief, execution checklist, and gap reporting
- [ ] Support stable JSON output with schema-backed keys and ordering
- [ ] Tests for D1

### D2. CLI workflow + target modes

Expose the new workflow through the CLI so a user can generate execution-ready packets for common coding-agent contexts without hand-editing the artifact. Keep target support narrow and concrete: `generic`, `codex`, and `claude-code`.

Required:
- `agentkit_cli/commands/taskpack_cmd.py`
- CLI wiring in main/help surfaces
- tests for CLI text/JSON/output-dir flows

- [ ] Add `agentkit taskpack <path>` CLI entrypoint
- [ ] Support `--target generic|codex|claude-code`
- [ ] Support writing a packet directory with at least markdown + JSON artifacts
- [ ] Tests for D2

### D3. End-to-end handoff workflow validation

Prove the full `source -> source-audit -> map -> contract -> bundle -> taskpack` lane works and fails clearly when prereqs are missing.

Required:
- focused end-to-end workflow tests
- explicit missing-artifact / missing-source coverage
- docs/report updates for the new lane

- [ ] Add focused end-to-end tests for the full workflow
- [ ] Add gap-path tests for missing upstream artifacts or unsupported target inputs
- [ ] Update README, changelog, and build-report/progress surfaces for `1.7.0`
- [ ] Tests for D3

### D4. Release-readiness pass

Leave the worktree in a truthful local release-ready state, not partially updated. Version metadata, changelog, docs, build report, and progress log must all agree.

Required:
- `pyproject.toml`
- `agentkit_cli/__init__.py`
- `uv.lock`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.7.0.md`
- `progress-log.md`

- [ ] Bump release metadata to `1.7.0`
- [ ] Reconcile docs and report surfaces to one local release-ready story
- [ ] Run contradiction + hygiene checks on the final repo state
- [ ] Tests/checks for D4

## 4. Test Requirements

- [ ] Unit tests for taskpack engine and renderers
- [ ] CLI tests for human-readable and JSON/output-dir flows
- [ ] Integration test covering `source -> source-audit -> map -> contract -> bundle -> taskpack`
- [ ] Edge cases: missing source, missing map/contract inputs, target-specific instruction shaping, deterministic output ordering
- [ ] All existing tests must still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include what was built, exact tests that passed, what remains, and any blockers
- Before trusting any release/status narrative, run:
  - `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.7.0-taskpack-handoff`
  - `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.7.0-taskpack-handoff`
- Before final summary, run:
  - `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.7.0-taskpack-handoff`
- Final summary when all deliverables are done or the pass stops

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write blocker report
- Scope creep detected beyond taskpack generation -> STOP and report the newly discovered requirement
- Any contradiction remains unresolved between tests and report surfaces -> STOP until source-of-truth state is reconciled
