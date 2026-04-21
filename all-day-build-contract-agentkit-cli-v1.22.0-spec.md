# All-Day Build Contract: agentkit-cli v1.22.0 spec

Status: In Progress
Date: 2026-04-21
Owner: OpenClaw build-loop builder
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Ship `agentkit-cli v1.22.0` with a deterministic `agentkit spec` workflow that turns the current repo-understanding surfaces into the next-increment planning step that still exists only as a human prompt. The concrete outcome is: local or saved-repo inputs can produce a stable markdown/JSON spec artifact naming the single best adjacent build, bounded alternates, why-now reasoning, scope boundaries, validation hints, and seeded contract-ready material that can flow directly into `agentkit contract`.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. No product-scope drift beyond deterministic next-increment spec generation.
4. Keep the feature local-only and artifact-driven. No agent execution, no remote mutation, no publishing steps in this pass.
5. Do not modify files outside `/Users/mordecai/repos/agentkit-cli-v1.22.0-spec`.
6. Commit only truthful feature, test, or release-surface work. No cosmetic drive-bys.
7. If stuck on the same blocker for 3 attempts, stop and write a blocker report.
8. Before claiming release-ready, verify tests and repo surfaces directly.
9. Preserve the repo-understanding/storyline: this step should strengthen the `source -> audit -> map -> spec -> contract` lane, not add random command sprawl.
10. Leave intentional contract artifacts alone or note them explicitly.

## 3. Deliverables

### D1. Deterministic spec engine

Required:
- schema-backed spec models
- deterministic recommendation logic grounded in current repo artifacts
- markdown + JSON rendering inputs

- [ ] Add a first-class `agentkit spec` engine that consumes current repo context, preferably canonical source, `source-audit`, `map`, and recent shipped workflow artifacts when present.
- [ ] Emit one primary recommended next build plus bounded alternates, all grounded in repo state rather than generic ideation.
- [ ] Include explicit why-now reasoning, scope boundaries, validation hints, and contract-seeding fields in the spec data model.
- [ ] Fail truthfully when required upstream context is missing or contradictory.

### D2. CLI and artifact flow

Required:
- CLI wiring
- stable stdout rendering
- JSON and file output
- contract-seeding path

- [ ] Add first-class `agentkit spec` CLI wiring with stable markdown/stdout output.
- [ ] Support machine-readable output (`--json`) and artifact writing (`--output`, `--output-dir`) consistent with adjacent commands.
- [ ] Provide deterministic contract-seeding material that can feed directly into `agentkit contract` without manual restitching.
- [ ] Keep behavior local-only, with no hidden execution side effects.

### D3. Workflow coverage and adjacency proof

Required:
- focused tests
- workflow integration
- explicit lane documentation

- [ ] Add focused tests for the spec engine, CLI, and artifact rendering.
- [ ] Add workflow coverage proving the repo-understanding story is now `source -> audit -> map -> spec -> contract` when those artifacts exist.
- [ ] Cover missing-upstream, contradictory-upstream, and fallback cases truthfully.
- [ ] Ensure the recommendation remains reproducible from the same input artifacts.

### D4. Docs and truthful local release readiness

Required:
- `README.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `FINAL-SUMMARY.md`
- `progress-log.md`

- [ ] Update docs and release surfaces to describe `agentkit spec` accurately.
- [ ] Bump version surfaces to `1.22.0`.
- [ ] Re-run validation and leave the repo truthfully `RELEASE-READY (LOCAL-ONLY)` or write an exact blocker report.
- [ ] Record the final supported lane and the exact validation outcomes in the repo surfaces.

## 4. Test Requirements

- [ ] Focused spec/contract/map workflow slice passes.
- [ ] Release-confidence validation pass succeeds.
- [ ] If repo prose changes materially, final suite truth is represented accurately and not contradicted.
- [ ] All status claims in report surfaces are backed by direct verification.

## 5. Reports

- Append progress to `progress-log.md` after each deliverable.
- Before trusting status prose, use `/Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.22.0-spec` if present.
- Run `/Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.22.0-spec` if present.
- Run `/Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.22.0-spec` before final summary if present.
- If a workspace script is missing or fails for environmental reasons, note that explicitly and keep going with equivalent direct verification.

## 6. Stop Conditions

- All deliverables checked and repo left truthfully local release-ready -> DONE.
- 3 consecutive failed attempts on the same blocker -> STOP and write blocker report.
- Any mismatch between tests and repo status surfaces that cannot be reconciled safely -> STOP and report exact mismatch.
- If the feature proves structurally redundant with existing commands, STOP and write the exact redundancy proof instead of forcing a fake increment.
