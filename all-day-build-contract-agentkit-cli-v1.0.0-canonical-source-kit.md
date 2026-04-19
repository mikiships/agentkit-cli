# All-Day Build Contract: agentkit-cli v1.0.0 canonical source kit

Status: In Progress
Date: 2026-04-19
Owner: OpenClaw build-loop execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build the missing authoring half of the v0.99.0 projection story. Right now `agentkit project` can fan one canonical context source out into `AGENTS.md`, `CLAUDE.md`, `AGENT.md`, `GEMINI.md`, `COPILOT.md`, and `llms.txt`, but it still assumes the user already knows what the canonical source file should be and where it should live. The next step is a first-class dedicated source workflow: create or promote one canonical source file into a stable agentkit-managed location, then project and drift-check everything else from that source deterministically.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside `/Users/mordecai/repos/agentkit-cli-v1.0.0-canonical-source-kit`.
7. Commit after each completed deliverable, not only at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not refactor, restyle, or improve unrelated code.
10. Read the existing projection tests/docs before writing code.
11. Do not push, tag, publish, or touch PyPI/GitHub release surfaces.
12. Keep this scoped to source-authoring and projection workflow, not a new generalized docs system.

## 3. Feature Deliverables

### D1. Dedicated canonical source path + engine support

Define one explicit agentkit-managed canonical source location and teach the projection engine to recognize and prefer it. The feature should let users stop authoring their working source in a tool-specific filename when they want a clean single source of truth.

Required:
- `agentkit_cli/context_projections.py`
- relevant shared constants/helpers for source detection and target metadata
- tests covering detection priority and dedicated-source behavior

- [ ] Add one dedicated canonical source location and expose it clearly in code/docs
- [ ] Update source detection priority so the dedicated source wins when present
- [ ] Preserve backwards compatibility for existing AGENTS/CLAUDE-based source detection
- [ ] Tests for D1

### D2. Bootstrap/promote command for canonical source authoring

Add a first-class CLI flow that can create the dedicated canonical source file or promote the best existing context file into that location without guesswork. This is the main user-facing unlock for the feature.

Required:
- one new or expanded CLI command under `agentkit_cli/commands/`
- CLI wiring in the main app
- JSON/reporting output where appropriate
- focused command tests

- [ ] User can initialize a fresh dedicated source file
- [ ] User can promote/copy from an existing detected source into the dedicated location
- [ ] Safe behavior when destination exists, with clear deterministic messaging
- [ ] Tests for D2

### D3. Projection/init/sync integration

Wire the new source workflow into the existing projection path so it feels native instead of bolted on. The dedicated source should work end-to-end with `project`, `sync`, and `init` where appropriate.

Required:
- `agentkit_cli/commands/project_cmd.py`
- `agentkit_cli/commands/init_cmd.py`
- any sync integration touched by the new source behavior
- integration tests

- [ ] `agentkit project` correctly uses the dedicated source when present
- [ ] `agentkit init` offers or supports the dedicated-source workflow in a sensible way
- [ ] Drift checks stay deterministic with the dedicated source in play
- [ ] Tests for D3

### D4. Docs, reports, versioning, and final validation

Update the repo so the new workflow is actually legible to users and to the next release pass.

Required:
- `README.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `progress-log.md`
- version metadata if the feature is complete

- [ ] README documents the dedicated-source workflow with examples
- [ ] Changelog and build report reflect the feature truthfully
- [ ] progress-log.md updated after each deliverable with tests + next step
- [ ] Full test suite green

## 4. Test Requirements

- [ ] Unit tests for each deliverable
- [ ] Integration tests covering bootstrap/promote -> project/check workflow
- [ ] Edge cases: existing destination file, no source files present, dedicated source plus legacy files both present, dedicated source drift check, init flow with projections
- [ ] All existing tests still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include what was built, what tests pass, what is next, and any blockers
- Before trusting any release/status narrative, run contradiction checks against repo-local report surfaces and reconcile them before summarizing
- Before final summary, run a hygiene pass for merge markers, unresolved comment slop, and obvious artifact noise
- Final summary only when all deliverables are done or a real stop condition triggers

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write blocker report
- Scope creep detected, for example inventing a broader docs/config system -> STOP and report the new requirement
- All tests passing but deliverables remain -> continue to the next deliverable
